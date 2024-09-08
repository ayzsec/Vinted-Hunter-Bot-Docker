# Vinted Discord Bot

A Discord bot designed to automate alerts for Vinted searches. This bot scrapes Vinted search results, monitors them for new items, and sends notifications to designated Discord channels. Built with `hikari`, `lightbulb`, and `loguru` for efficient event handling and logging, this bot allows users to subscribe to search results and receive real-time updates in Discord.

## Features

- **Scraping and Alerts**: Continuously scrapes Vinted for new items based on user subscriptions.
- **Automated Channel Creation**: Automatically creates new channels under a designated category for each subscription.
- **Subscriptions Management**: Add, view, or remove subscriptions with slash commands.

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/vinted-discord-bot.git
   cd vinted-discord-bot
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up your `config.json` file with your Discord bot token and other environment variables:
   ```json
   {
      "discord_token": "YOUR BOT TOKEN"
   }
   ```

4. Run the bot:
   ```bash
   python bot.py
   ```

## Commands

- `/subscribe <url> <channel_name> <category_id>`: Subscribe to a Vinted search and create a dedicated channel for alerts.
- `/subscriptions`: View a list of active subscriptions.
- `/unsubscribe <id>`: Stop following a subscription and delete its corresponding channel.
- `/reboot`: Restart the bot.
- `/update`: Update the bot to the latest version.

## Requirements

- Python 3.8+
- `hikari`
- `lightbulb`
- `loguru`
- `dataset`
- `requests`
- `uvloop` (for non-Windows users)

## License

This project is licensed under the MIT License.
