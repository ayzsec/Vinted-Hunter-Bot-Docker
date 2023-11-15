import asyncio
import os
import dataset
import dotenv
import hikari
import lightbulb
from loguru import logger as log
from api import search_item

from scraper import generate_embed, scrape

dotenv.load_dotenv()

bot = lightbulb.BotApp(token=os.getenv("TOKEN"))
db = dataset.connect("sqlite:///data.db")
table = db["subscriptions"]


async def run_background() -> None:
    log.info("Scraper started.")
    while True:
        log.info("Executing scraping loop")
        for sub in db["subscriptions"]:
            items = scrape(db, sub)
            if items:
                log.debug("{items} found for {id}", items=len(items), id=str(sub["id"]))
                for item in items:
                    item_res = search_item(item["id"])
                    if item_res:
                        if str(item_res["item"]["user"]["feedback_count"]) != "0":
                            embed = generate_embed(item, sub["id"], item_res)
                            await bot.rest.create_message(sub["channel_id"], embed=embed)

            if len(items) > 0:
                # Update table by using last in date item timestamp
                table.update(
                    {
                        "id": sub["id"],
                        "last_sync": int(
                            items[0]["photo"]["high_resolution"]["timestamp"]
                        ),
                    },
                    ["id"],
                )

        log.info("Sleeping for {interval} seconds", interval=os.getenv("INTERVAL", 60))
        await asyncio.sleep(int(os.getenv("INTERVAL", 60)))


@bot.listen(hikari.ShardReadyEvent)
async def ready_listener(_):
    log.info("Bot is ready")
    log.info("{count} subscriptions registered", count=table.count())
    asyncio.create_task(run_background())


@bot.command()
@lightbulb.option("url", "URL to vinted search", type=str, required=True)
@lightbulb.option("channel_name", "Name of the channel for alerts", type=str, required=True)
@lightbulb.command("subscribe", "Subscribe to a Vinted search")
@lightbulb.implements(lightbulb.SlashCommand)
async def subscribe(ctx: lightbulb.Context) -> None:
    # Obtenir l'ID du serveur (guild) depuis le contexte d'interaction
    guild_id = ctx.interaction.guild_id

    if guild_id:
        # Récupérer l'objet du serveur (guild) à partir de l'ID du serveur
        guild = bot.cache.get_guild(int(guild_id))

        if guild:
            # Récupérer l'ID de la catégorie "alertes vinted" depuis les variables d'environnement
            category_id = os.getenv("CATEGORY_ID")

            if category_id:
                # Vérifier si la catégorie existe dans le serveur (guild)
                alert_category = guild.get_channel(int(category_id))

                if alert_category and isinstance(alert_category, hikari.GuildCategory):
                    # Créer un nouveau canal avec le nom spécifié sous la catégorie "alertes vinted"
                    new_channel = await guild.create_text_channel(ctx.options.channel_name, category=alert_category)

                    # Enregistrer l'abonnement dans la base de données
                    table.insert(
                        {"url": ctx.options.url, "channel_id": new_channel.id, "last_sync": -1}
                    )
                    log.info("Subscription created for {url}", url=ctx.options.url)

                    await ctx.respond(f"✅ Created subscription in #{new_channel.name} under {alert_category.name}")
                else:
                    await ctx.respond("❌ Error: Could not find the specified category by ID.")
            else:
                await ctx.respond("❌ Error: CATEGORY_ID is not defined in the environment variables.")
        else:
            await ctx.respond("❌ Error: Could not find the server (guild). Please use this command in a server (guild).")
    else:
        await ctx.respond("❌ Error: Could not obtain the server (guild) ID.")

@bot.command()
@lightbulb.command("subscriptions", "Get a list of subscription")
@lightbulb.implements(lightbulb.SlashCommand)
async def subscriptions(ctx: lightbulb.Context) -> None:
    embed = hikari.Embed(title="Subscriptions")

    for sub in table:
        embed.add_field(name="#" + str(sub["id"]), value=sub["url"])

    await ctx.respond(embed)

@bot.command()
@lightbulb.command("reboot", "Reboot Vinted BOT")
@lightbulb.implements(lightbulb.SlashCommand)
async def reboot(ctx: lightbulb.Context) -> None:
    await ctx.respond("✅ Restarting Vinted BOT")
    os.popen("sudo -S %s"%("pkill -9 python && reboot"), 'w').write(os.getenv("PASS"))

@bot.command()
@lightbulb.command("update", "get Vinted BOT to the latest update")
@lightbulb.implements(lightbulb.SlashCommand)
async def update(ctx: lightbulb.Context) -> None:
    os.system("cd /home/vinted/vintedpy && git pull")
    await ctx.respond("✅ Successfully updated Vinted BOT")

@bot.command()
@lightbulb.option("id", "ID of the subscription", type=int, required=True)
@lightbulb.command("unsubscribe", "Stop following a subscription")
@lightbulb.implements(lightbulb.SlashCommand)
async def unsubscribe(ctx: lightbulb.Context) -> None:
    table.delete(id=ctx.options.id)
    log.info("Deleted subscription #{id}", id=str(ctx.options.id))
    await ctx.respond(f"🗑 Deleted subscription #{str(ctx.options.id)}.")


if __name__ == "__main__":
    if os.name != "nt":
        import uvloop

        uvloop.install()

    bot.run(
        activity=hikari.Activity(
            name="Vinted!", type=hikari.ActivityType.WATCHING
        )
    )
