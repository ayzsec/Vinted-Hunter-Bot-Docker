import asyncio
import os
import os
import dataset
import json
import hikari
import lightbulb
from loguru import logger as log
from api import search_item

from scraper import generate_embed, scrape

def load_config():
    with open('config.json') as config_file:
        return json.load(config_file)

config = load_config()
bot = lightbulb.BotApp(token=config["discord_token"])
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

        log.info("Sleeping for {interval} seconds", interval=60)
        await asyncio.sleep(int(60))


@bot.listen(hikari.ShardReadyEvent)
async def ready_listener(_):
    log.info("Bot is ready")
    log.info("{count} subscriptions registered", count=table.count())
    asyncio.create_task(run_background())


@bot.command()
@lightbulb.option("url", "URL to vinted search", type=str, required=True)
@lightbulb.option("channel_name", "Name of the channel for alerts", type=str, required=True)
@lightbulb.option("category_id", "ID of category for alerts", type=str, required=True)
@lightbulb.command("subscribe", "Subscribe to a Vinted search")
@lightbulb.implements(lightbulb.SlashCommand)
async def subscribe(ctx: lightbulb.Context) -> None:
    # Obtenir l'ID du serveur (guild) depuis le contexte d'interaction
    guild_id = ctx.interaction.guild_id

    if guild_id:
        # RÃ©cupÃ©rer l'objet du serveur (guild) Ã  partir de l'ID du serveur
        guild = bot.cache.get_guild(int(guild_id))

        if guild:
            # RÃ©cupÃ©rer l'ID de la catÃ©gorie "alertes vinted" depuis les variables d'environnement
            category_id = ctx.options.category_id

            if category_id:
                # VÃ©rifier si la catÃ©gorie existe dans le serveur (guild)
                alert_category = guild.get_channel(int(category_id))

                if alert_category and isinstance(alert_category, hikari.GuildCategory):
                    # CrÃ©er un nouveau canal avec le nom spÃ©cifiÃ© sous la catÃ©gorie "alertes vinted"
                    new_channel = await guild.create_text_channel(ctx.options.channel_name, category=alert_category)

                    # Enregistrer l'abonnement dans la base de donnÃ©es
                    table.insert(
                        {"url": ctx.options.url, "channel_id": new_channel.id, "last_sync": -1}
                    )
                    log.info("Subscription created for {url}", url=ctx.options.url)

                    await ctx.respond(f"âœ… Created subscription in #{new_channel.name} under {alert_category.name}")
                else:
                    await ctx.respond("âŒ Error: Could not find the specified category by ID.")
            else:
                await ctx.respond("âŒ Error: CATEGORY_ID is not defined in the environment variables.")
        else:
            await ctx.respond("âŒ Error: Could not find the server (guild). Please use this command in a server (guild).")
    else:
        await ctx.respond("âŒ Error: Could not obtain the server (guild) ID.")

@bot.command()
@lightbulb.command("subscriptions", "Get a list of subscription")
@lightbulb.implements(lightbulb.SlashCommand)
async def subscriptions(ctx: lightbulb.Context) -> None:
    embed = hikari.Embed(title="Subscriptions")

    for sub in table:
        embed.add_field(name="#" + str(sub["id"]), value=sub["url"])

    await ctx.respond(embed)

@bot.command()
@lightbulb.option("id", "ID of the subscription", type=int, required=True)
@lightbulb.command("unsubscribe", "Stop following a subscription")
@lightbulb.implements(lightbulb.SlashCommand)
async def unsubscribe(ctx: lightbulb.Context) -> None:
    subscription_id = ctx.options.id
    subscription = table.find_one(id=subscription_id)

    if subscription:
        # Supprimer l'alerte de la base de donnÃ©es
        table.delete(id=subscription_id)

        # Obtenir l'objet du canal Ã  partir de l'ID du canal dans l'alerte
        channel = bot.cache.get_guild(ctx.interaction.guild_id).get_channel(subscription["channel_id"])

        if channel:
            # Supprimer le canal
            await channel.delete()
            log.info("Deleted subscription #{id}", id=str(subscription_id))
            await ctx.respond(f"ðŸ—‘ Deleted subscription #{str(subscription_id)}.")
        else:
            await ctx.respond("âŒ Error: Could not find the channel to delete.")
    else:
        await ctx.respond("âŒ Error: Subscription not found with ID {id}.")


if __name__ == "__main__":
    if os.name != "nt":
        import uvloop

        uvloop.install()

    bot.run(
        activity=hikari.Activity(
            name="Vinted!", type=hikari.ActivityType.WATCHING
        )
    )
