# Reaper
Discord Bot for temporary channels

# ----------------------#
#       README          #
# ----------------------#

# Discord Bot for Custom Channel Management

This Discord bot, built using `nextcord`, helps manage dynamic custom channels in a Discord server. It provides an interactive way for users to create and manage temporary voice channels, with a focus on ease of use and automation.

## Features
- **Add Bot Channels**: Automatically creates a category named "Custom Channel" with a "setup" text channel and an "ADD NEW" voice channel to streamline channel management.
- **Dropdown Setup**: Administrators can initiate a setup that lets admins select existing categories for creating temporary voice channels.
- **Temporary Channel Creation**: Users can join the "ADD NEW" voice channel to trigger the setup process for a new temporary channel. These channels are automatically deleted when all users leave, ensuring the server remains organized.
- **Customizable Privacy**: Users can choose whether their temporary channels are public or private during setup, allowing for flexible control over who can join.

## Commands
- **'!add_bot_channels'** - Creates the "Custom Channel" category along with the necessary channels for users to begin creating temporary channels.
- **'!dropdown_setup'** - Displays a dropdown for administrators to select categories where temporary channels can be created.
- **'!clear'** - Clears all messages from the channel the message was sent. (admin only).

## How It Works
- **Join <"ADD NEW"> Channel**: Users can join the <"ADD NEW"> voice channel, which will prompt them to create a custom temporary channel.
- **Interactive Setup**: The bot sends an interactive setup to the user, allowing them to specify the channel name, user limit, and privacy settings.
- **Automatic Cleanup**: When all users leave a temporary channel, the bot automatically deletes the channel, keeping the server tidy.

## Prerequisites
- **Python 3.8 or higher**.
- **Nextcord library**: A fork of Discord.py for building Discord bots.
- **dotenv**: Used to securely load environment variables.

## Installation
1. Clone the repository.
   ```sh
   git clone https://github.com/your-repo/discord-bot.git
   ```
2. Install dependencies.
   ```sh
   pip install -r requirements.txt
   ```
3. Create a `.env` file to store the bot token.
   ```sh
   DISCORD_TOKEN=YOUR_DISCORD_BOT_TOKEN
   ```
4. Run the bot.
   ```sh
   python app.py
   ```

## Logging
The bot uses the Python logging module for informational and error messages. You can modify the logging level in the "app.py" file.

## License
This project is licensed under the MIT License.

