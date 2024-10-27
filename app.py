import nextcord
from nextcord.ext import commands
import os
import asyncio
import logging
from dotenv import load_dotenv

# ----------------------#
#   Logging Setup       #
# ----------------------#

# Initialize logging configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# ----------------------#
#  Load Environment     #
# ----------------------#

# Load the token from the .env file
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# ----------------------#
#  Bot Initialization   #
# ----------------------#

# Initialize intents at creation to avoid read-only warnings
intents = nextcord.Intents.default()
intents.message_content = True
intents.members = True
intents.voice_states = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Dictionary to keep track of temporary channels and selected categories
temporary_channels = {}
selected_categories = {}  # Stores currently selected categories per user


# -----------------------------#
#   Add Bot Channels Command   #
# -----------------------------#

@bot.command(name="add_bot_channels", help="Create the Custom Channel category and required channels.")
@commands.has_permissions(administrator=True)
async def add_bot_channels(ctx):
    """Creates the 'Custom Channel' category with the 'setup' text channel and 'ADD NEW' voice channel."""
    guild = ctx.guild

    # Create "Custom Channel" category if it doesn't exist
    category = nextcord.utils.get(guild.categories, name="Custom Channel")
    if not category:
        category = await guild.create_category("Custom Channel")
        logging.info("Category 'Custom Channel' created.")
        await ctx.send("Category 'Custom Channel' created.")
    else:
        await ctx.send("Category 'Custom Channel' already exists.")

    # Create "setup" text channel in "Custom Channel" category if it doesn't exist
    setup_channel = nextcord.utils.get(guild.text_channels, name="setup", category=category)
    if not setup_channel:
        setup_channel = await guild.create_text_channel("setup", category=category)
        logging.info("Text channel 'setup' created.")
        await ctx.send("Text channel 'setup' created in 'Custom Channel' category.")
    else:
        await ctx.send("Text channel 'setup' already exists.")

    # Create "ADD NEW" voice channel in "Custom Channel" category if it doesn't exist
    add_new_channel = nextcord.utils.get(guild.voice_channels, name="ADD NEW", category=category)
    if not add_new_channel:
        add_new_channel = await guild.create_voice_channel("ADD NEW", category=category)
        logging.info("Voice channel 'ADD NEW' created.")
        await ctx.send("Voice channel 'ADD NEW' created in 'Custom Channel' category.")
    else:
        await ctx.send("Voice channel 'ADD NEW' already exists.")


# -----------------------------#
#     Dropdown Setup Command   #
# -----------------------------#

@bot.command(name="dropdown_setup", help="Display category selection buttons for temporary channel setup.")
@commands.has_permissions(administrator=True)
async def dropdown_setup(ctx):
    """Displays buttons for all categories in the server for multi-selection."""
    guild = ctx.guild
    categories = [cat for cat in guild.categories if cat.name != "Custom Channel"]  # Exclude "Custom Channel"

    if not categories:
        await ctx.send("No categories exist in this server.")
        return

    # Send the instruction message and the category selection buttons
    await ctx.send("⚠️**Join 'ADD NEW' voice channel to test the setup-process!⚠️**")
    view = CategorySelectionView(categories, ctx.author)
    await ctx.send(view=view)


# ------------------------------#
#       Category Selection      #
# ------------------------------#

class CategorySelectionView(nextcord.ui.View):
    """View with buttons for each category for multi-selection."""

    def __init__(self, categories, user):
        super().__init__(timeout=300)  # Timeout after 5 minutes
        self.categories = categories
        self.user = user

        # Create a grid layout for buttons in 2 rows
        row = 0
        for i, category in enumerate(categories):
            button = nextcord.ui.Button(label=category.name, style=nextcord.ButtonStyle.secondary, row=row)
            button.callback = self.create_button_callback(category, button)
            self.add_item(button)

            # Change row every two buttons to create a grid layout
            if (i + 1) % 2 == 0:
                row += 1

        # Add the finish button in a new row below all other buttons
        finish_button = nextcord.ui.Button(label="Finish Selection", style=nextcord.ButtonStyle.success, row=row + 1)
        finish_button.callback = self.finish_selection
        self.add_item(finish_button)

    def create_button_callback(self, category, button):
        """Generate a callback for each category button that toggles selection and updates button style."""

        async def button_callback(interaction: nextcord.Interaction):
            if interaction.user != self.user:
                await interaction.response.send_message("You're not authorized to select categories for this setup.",
                                                        ephemeral=True)
                return

            # Toggle category selection and update button style
            user_id = interaction.user.id
            if user_id not in selected_categories:
                selected_categories[user_id] = []

            if category in selected_categories[user_id]:
                selected_categories[user_id].remove(category)
                button.style = nextcord.ButtonStyle.secondary
            else:
                selected_categories[user_id].append(category)
                button.style = nextcord.ButtonStyle.primary
            await interaction.response.edit_message(view=self)

        return button_callback

    async def finish_selection(self, interaction: nextcord.Interaction):
        """Handle the finish selection button press."""
        if interaction.user != self.user:
            await interaction.response.send_message("You're not authorized to finish selection for this setup.",
                                                    ephemeral=True)
            return

        user_id = interaction.user.id
        if user_id not in selected_categories or not selected_categories[user_id]:
            await interaction.response.send_message("No categories selected. Please select at least one category.",
                                                    ephemeral=True)
            return

        # Update message to show that setup is complete (grayed out)
        await interaction.message.edit(
            content="**Setup complete. Waiting for user to join the 'ADD NEW' voice channel...**", view=None)
        logging.info(
            f"{interaction.user.name} selected categories: {[cat.name for cat in selected_categories[user_id]]}")


# ------------------------------#
#   on_voice_state_update Event #
# ------------------------------#

@bot.event
async def on_voice_state_update(member, before, after):
    """Event handler for voice channel state updates."""
    try:
        setup_channel = nextcord.utils.get(member.guild.text_channels, name="setup")

        # Check if the user joined the "ADD NEW" voice channel
        if after.channel and after.channel.name == "ADD NEW":
            logging.info(f"{member.name} joined the 'ADD NEW' voice channel.")

            user_id = member.id
            if user_id not in selected_categories or not selected_categories[user_id]:
                await setup_channel.send(
                    "No categories have been approved for selection. Please ask an administrator to run `!dropdown_setup`.")
                return

            # Send a setup modal to the user
            modal = TempChannelSetupModal(selected_categories[user_id][0])  # Use the first selected category for now
            await setup_channel.send(f"{member.mention} is setting up a temporary channel.",
                                     view=ContinueSetupView(selected_categories[user_id]))
            await asyncio.sleep(30)  # Wait for 30 seconds before sending the DM
            await member.send(embed=create_dm_embed(member.guild))  # Pass the guild object here

        # Check if the user left a temporary channel and if it's now empty
        if before.channel and before.channel.id in temporary_channels and len(before.channel.members) == 0:
            await before.channel.delete()
            del temporary_channels[before.channel.id]
            logging.info(f"Temporary channel '{before.channel.name}' deleted after being empty.")
    except nextcord.Forbidden:
        logging.error(f"Missing permissions to execute voice state update for {member.name}")
    except Exception as e:
        logging.error(f"Unexpected error in on_voice_state_update: {e}")


# ------------------------------#
#      Continue Setup View      #
# ------------------------------#

class ContinueSetupView(nextcord.ui.View):
    """View with a dropdown for selected categories and a continue button to open the setup modal."""

    def __init__(self, categories):
        super().__init__(timeout=300)
        self.categories = categories

        # Create a dropdown for the selected categories
        self.category_dropdown = nextcord.ui.Select(
            placeholder="Choose a category",
            options=[nextcord.SelectOption(label=category.name, value=str(category.id)) for category in categories]
        )
        self.add_item(self.category_dropdown)

        # Add a button to continue to the modal setup
        continue_button = nextcord.ui.Button(label="Continue Setup", style=nextcord.ButtonStyle.primary)
        continue_button.callback = self.open_modal
        self.add_item(continue_button)

    async def open_modal(self, interaction: nextcord.Interaction):
        """Open the setup modal with selected categories."""
        selected_category = nextcord.utils.get(interaction.guild.categories, id=int(self.category_dropdown.values[0]))
        modal = TempChannelSetupModal(selected_category)
        await interaction.response.send_modal(modal)


# ------------------------------#
#      Temp Channel Setup       #
# ------------------------------#

class TempChannelSetupModal(nextcord.ui.Modal):
    def __init__(self, category):
        super().__init__("Temporary Channel Setup", timeout=300)
        self.category = category

        # Add input fields for channel details
        self.add_item(
            nextcord.ui.TextInput(
                label="Channel Name",
                placeholder="Enter the name for your channel",
                required=True,
                max_length=100
            )
        )

        self.add_item(
            nextcord.ui.TextInput(
                label="User Limit",
                placeholder="Enter a number for max users (0 for unlimited)",
                required=True,
                max_length=2
            )
        )

        self.add_item(
            nextcord.ui.TextInput(
                label="Privacy",
                placeholder="Type 'public' or 'private' for channel visibility",
                required=True,
                max_length=10
            )
        )

    async def callback(self, interaction: nextcord.Interaction):
        """Callback for modal submission."""
        channel_name = self.children[0].value
        user_limit = int(self.children[1].value) if self.children[1].value.isdigit() else 0
        privacy = self.children[2].value.lower()

        overwrites = {
            interaction.guild.default_role: nextcord.PermissionOverwrite(connect=(privacy != "private")),
            interaction.user: nextcord.PermissionOverwrite(connect=True)
        }

        # Create the temporary voice channel
        new_channel = await interaction.guild.create_voice_channel(
            name=channel_name,
            category=self.category,
            user_limit=user_limit,
            overwrites=overwrites
        )
        temporary_channels[new_channel.id] = interaction.user.id
        await interaction.user.move_to(new_channel)

        # Log the action and clear the setup channel
        logging.info(f"Temporary channel '{channel_name}' created by {interaction.user.name} and user moved.")
        setup_channel = nextcord.utils.get(interaction.guild.text_channels, name="setup")
        if setup_channel:
            await setup_channel.purge(limit=100)

        # Close the modal
        await interaction.response.send_message("Temporary channel created and you have been moved.", ephemeral=True)


# -----------------------------#
#        Clear Command         #
# -----------------------------#

@bot.command(name="clear", help="Clear the current channel.")
@commands.has_permissions(administrator=True)
async def clear(ctx):
    """Clears all messages in the channel where the command is used."""
    await ctx.channel.purge(limit=100)
    logging.info(f"Channel '{ctx.channel.name}' cleared by administrator {ctx.author.name}.")
    await ctx.send(f"Channel '{ctx.channel.name}' has been cleared.", delete_after=5)


# -----------------------------#
#       Create DM Embed        #
# -----------------------------#

def create_dm_embed(guild):
    """Creates an embed for the DM message with the server's icon as thumbnail."""
    embed = nextcord.Embed(
        title="Setup Complete!",
        description="Thank you for using Reaper! Feedback is always welcome on our Discord server.",
        color=0x1ABC9C
    )
    # Use the guild (server) icon URL if available, otherwise use a placeholder or skip setting it
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
    else:
        embed.set_thumbnail(url="https://example.com/placeholder.png")  # Optional: Replace with a placeholder image URL

    embed.add_field(name="Discord Server", value="[Join our Discord](https://discord.gg/SEuJ6ZN4Bs)", inline=False)
    return embed


# ----------------------#
#      Run the Bot      #
# ----------------------#

try:
    bot.run(TOKEN)
except Exception as e:
    logging.error(f"Error when running the bot: {e}")
