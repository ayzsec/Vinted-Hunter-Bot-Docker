import asyncio
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
            try:
                items = scrape(db, sub)
                if items:
                    log.debug("{items} found for {id}", items=len(items), id=str(sub["id"]))
                    for item in items:
                        try:
                            item_res = search_item(item["id"])
                            if item_res:
                                if str(item_res["item"]["user"]["feedback_count"]) != "0":
                                    try:
                                        embed = generate_embed(item, sub["id"], item_res)
                                        log.debug("Sending message to channel {channel} for item {item}", 
                                                 channel=sub["channel_id"], item=item["id"])
                                        await bot.rest.create_message(sub["channel_id"], embed=embed)
                                        log.info("Successfully sent message for item {item}", item=item["id"])
                                    except hikari.ForbiddenError as e:
                                        log.error("Bot lacks permissions in channel {channel}: {error}", 
                                                 channel=sub["channel_id"], error=str(e))
                                    except hikari.NotFoundError as e:
                                        log.error("Channel {channel} not found: {error}", 
                                                 channel=sub["channel_id"], error=str(e))
                                    except Exception as e:
                                        log.error("Failed to send message: {error}", error=str(e))
                        except Exception as e:
                            log.error("Error processing item {item}: {error}", 
                                     item=item["id"], error=str(e))
                            continue
            except Exception as e:
                log.error("Error in scraping loop: {error}", error=str(e))
                continue

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
    # Obtain the server (guild) ID from the interaction context
    guild_id = ctx.interaction.guild_id

    if guild_id:
        # Retrieve the server (guild) object from the server (guild) ID
        guild = bot.cache.get_guild(int(guild_id))

        if guild:
            # Retrieve the "vinted alerts" category ID from the environment variables
            category_id = ctx.options.category_id

            if category_id:
                # Check if the category exists in the server (guild)
                alert_category = guild.get_channel(int(category_id))

                if alert_category and isinstance(alert_category, hikari.GuildCategory):
                    # Create a new channel with the specified name under the "vinted alerts" category
                    new_channel = await guild.create_text_channel(ctx.options.channel_name, category=alert_category)

                    # Store the subscription in the database
                    table.insert(
                        {"url": ctx.options.url, "channel_id": new_channel.id, "last_sync": -1}
                    )
                    log.info("Subscription created for {url}", url=ctx.options.url)

                    await ctx.respond(f"? Created subscription in #{new_channel.name} under {alert_category.name}")
                else:
                    await ctx.respond("? Error: Could not find the specified category by ID.")
            else:
                await ctx.respond("? Error: CATEGORY_ID is not defined in the environment variables.")
        else:
            await ctx.respond("? Error: Could not find the server (guild). Please use this command in a server (guild).")
    else:
        await ctx.respond("? Error: Could not obtain the server (guild) ID.")

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
        # Remove the alert from the database
        table.delete(id=subscription_id)

        # Retrieve the channel object from the channel ID in the alert
        channel = bot.cache.get_guild(ctx.interaction.guild_id).get_channel(subscription["channel_id"])

        if channel:
            # Delete the channel
            await channel.delete()
            log.info("Deleted subscription #{id}", id=str(subscription_id))
            await ctx.respond(f"?? Deleted subscription #{str(subscription_id)}.")
        else:
            await ctx.respond("? Error: Could not find the channel to delete.")
    else:
        await ctx.respond("? Error: Subscription not found with ID {id}.", id=subscription_id)


if __name__ == "__main__":
    if os.name != "nt":
        try:
            import uvloop
            uvloop.install()
        except ImportError:
            print("uvloop is not installed or not compatible with this system. Falling back to default asyncio event loop.")
    else:
        print("You're running on Windows, which is not compatible with uvloop. Using default asyncio event loop.")

    bot.run(
        activity=hikari.Activity(
            name="Vinted!", type=hikari.ActivityType.WATCHING
        )
    )
