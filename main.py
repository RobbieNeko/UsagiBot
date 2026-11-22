import discord
from discord.ext import commands
import aiohttp

import datetime
import json
import os

# Wildcard because we want to import all the helper functions
from helper_functions import *
import use_actions

"""
The main code for the bot.
The primary contents here should be commands and bot setup.
Helper functions should generally not go here, and should instead go in helper_functions.py
"""

#Change this to whatever your source code's link is, if you run a modified version
SOURCE_CODE_URL = "https://github.com/RobbieNeko/UsagiBot"
MODLOG_CHANNEL_ID = 1222257915973599302
REACTION_TRIGGERS: list
LAST_MAGIA_MESSAGE: dict[int, datetime.datetime] = {}
USAGI_COLOR: discord.Color = discord.Color.from_rgb(33, 26, 54) # Taken from her hair
SHOPS: list[str]
GACHAS: list[str]
GACHA_COST = 100 # Gachas are assumed to all be the same cost

if os.path.isfile("./warnlog.json") and not os.path.isfile("./userdata.json"):
    with open("./warnlog.json") as old:
        oldData = json.load(old)
        newData = {}
        for key, value in oldData:
            newData[key] = {"warnings": value}
        with open("./userdata.json", 'w') as new:
            json.dump(newData, new)
    # Delete old style of file
    os.remove("./warnlog.json")

if not os.path.isfile("./userdata.json"):
    with open("./userdata.json", 'w') as file:
        # Makes sure that the file is initialized with an empty dict if not found
        # Actual structure is dict[str, dict[str, Any]], where the keys of the parent dictionary are users, and the child dictionary is data
        json.dump({}, file)

if not os.path.isfile("./reactiontriggers.json"):
    with open("./reactiontriggers.json", 'w') as file:
        # Makes sure that the file is initialized with an empty array if not found
        # Actual structure is list[dict[str, str]]
        json.dump([], file)
        REACTION_TRIGGERS = []
else:
    # This is actually probably performance sensitive enough to warrant storing in RAM unless the list of triggers grows big enough to overwhelm the raspberry pi
    with open("./reactiontriggers.json") as file:
        REACTION_TRIGGERS = json.load(file)

with open("./config.json") as file:
    config = json.load(file)
    BOT_TOKEN = config['bot_token']
    MAGIA_EARN_DELAY: int = config['magia_earn_message_delay']
    MAGIA_EARN_AMOUNT: int = config['magia_earn_amount']
    ITEM_DEFINITIONS: list[str] = config['item_definitions_files']

if not os.path.isfile("./shop.json"):
    with open("./shop.json", 'w') as file:
        json.dump({}, file)
    SHOPS = []
else:
    with open("./shop.json") as file:
        data: dict = json.load(file)
        SHOPS = list(data.keys())

if not os.path.isfile("./gachas.json"):
    with open("./gachas.json", 'w') as file:
        json.dump({}, file)
    GACHAS = []
else:
    with open("./gachas.json") as file:
        data: dict = json.load(file)
        GACHAS = list(data.keys())

# Class added for customizability, namely the setup hook override
class UsagiBot(commands.Bot):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def setup_hook(self):
        # Sets things up, namely the global session
        self.session = aiohttp.ClientSession()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = UsagiBot(command_prefix="u!", intents=intents)

@bot.tree.command()
async def about(interaction: discord.Interaction):
    """Prints basic 'about' info"""
    info = discord.Embed(title='About UsagiBot')
    info.add_field(name="Developer(s)", value="RosaAeterna (aka NekoRobbie), RibbonTeaDream")
    info.add_field(name="Library", value="Discord.py")
    info.add_field(name="License", value="GNU AGPL v3")
    info.add_field(name="Version", value="0.0.4-0")
    await interaction.response.send_message(embed=info)

@bot.tree.command()
@discord.app_commands.default_permissions(manage_messages=True)
@discord.app_commands.checks.has_permissions(manage_messages=True)
@discord.app_commands.describe(trigger="Text you want to trigger on in the message")
@discord.app_commands.describe(message="Text you want to react with (optional)")
@discord.app_commands.describe(image="URL to the image you want to react with (optional)")
async def addreactiontrigger(interaction: discord.Interaction, trigger: str, message: str | None = None, image: str | None = None):
    """Adds a trigger to react to specific message content with a predefined message and/or image"""
    newTrigger = {"trigger": trigger, "message": message if message != None else '', 'image': image if image != None else '' }
    REACTION_TRIGGERS.append(newTrigger)
    with open("./reactiontriggers.json", 'w') as file:
        json.dump(REACTION_TRIGGERS, file)
    await interaction.response.send_message(f"Added new trigger for phrase {trigger}!", ephemeral=True)

@bot.tree.command()
@discord.app_commands.default_permissions(ban_members=True)
@discord.app_commands.checks.has_permissions(ban_members=True)
async def ban(interaction: discord.Interaction, user: discord.Member, reason: str | None = None):
    """Bans a user from the guild, sending a DM to them as well as putting it in the mod log"""
    author = interaction.user
    if (type(author) == discord.Member):
        if(author.roles[-1] <= user.roles[-1]):
            await interaction.response.send_message(f"You do not have the ability to ban {user.display_name}!", ephemeral=True)
            return
    channel = bot.get_channel(MODLOG_CHANNEL_ID)
    if type(channel) == discord.TextChannel:
        embed = modlogEmbed("ban", user, interaction.user, reason)
        await channel.send(embed=embed)
    try:
        await user.send(f"You have been banned from {interaction.guild}!{f"\n{reason}" if reason != None else ''}")
    except:
        print(f"Could not DM {user.name}")
    await user.ban(reason=reason)
    await interaction.response.send_message(f"Banned {user.display_name}!", ephemeral=True)

@bot.tree.command()
@discord.app_commands.describe(user="User you want to check the balance of (optional, defaults to yourself)")
async def balance(interaction: discord.Interaction, user: discord.Member | discord.User | None = None):
    """Shows you the Magia balance of yourself or another member!"""
    user = user if not (user is None) else interaction.user
    with open("./userdata.json") as file:
        data: dict = json.load(file)
        userData: dict = data.get(str(user.id), {})
        userBalance: int = userData.get("balance", 0)
    await interaction.response.send_message(f"{"Your" if user == interaction.user else user.display_name + "'s"} balance is {userBalance} Magia!")

@bot.tree.command()
async def buy(interaction: discord.Interaction, item: str):
    """Buys an item from the shop!"""
    with open("./shop.json") as file:
        data: dict[str, dict[str, int]] = json.load(file)
        for shop in data.values():
            if item in shop:
                addItem(interaction.user.id, item)
                removeMagia(interaction.user.id, shop[item])
                await interaction.response.send_message(f"You have bought a(n) {item}!")
                return
    await interaction.response.send_message(f"I couldn't find {item} in any of the shops!")

@bot.tree.command()
@discord.app_commands.default_permissions(moderate_members=True)
@discord.app_commands.checks.has_permissions(moderate_members=True)
async def cleartimeout(interaction: discord.Interaction, user: discord.Member):
    """Clears the timeout for the given user. (Idempotent)"""
    await user.timeout(None)
    await interaction.response.send_message(f"Cleared timeout for {user.display_name}")

@bot.tree.command()
@discord.app_commands.default_permissions(moderate_members=True)
@discord.app_commands.checks.has_permissions(moderate_members=True)
async def clearwarnings(interaction: discord.Interaction, user: discord.Member):
    """Clears the warnings for the given user. (Idempotent)"""
    with open("./userdata.json", 'r+') as file:
        data: dict = json.load(file)
        # Erase the contents of the file
        file.truncate(0)
        # Return pointer to the start of the file
        file.seek(0)
        # This should work even if they aren't in the data file at all
        userData: dict = data.get(str(user.id), {})
        userData["warnings"] = []
        data[str(user.id)] = userData
        json.dump(data, file)
    await interaction.response.send_message(f"Cleared warnings for {user.display_name}")

@bot.tree.command()
@discord.app_commands.choices(choices = [discord.app_commands.Choice(name=x.upper().replace('_', ' '), value=x) for x in GACHAS])
async def gacha(interaction: discord.Interaction, choices: discord.app_commands.Choice[str]):
    """Lets you make a pull from a gacha!"""
    result = gachaPull(choices.value)
    addItem(interaction.user.id, result)
    removeMagia(interaction.user.id, GACHA_COST)
    await interaction.response.send_message(f"You pulled a {result}!")

@bot.tree.command()
async def inventory(interaction: discord.Interaction, user: discord.User | discord.Member | None = None):
    """Lets you view the inventory of yourself or another member!"""
    if (user is None):
        user = interaction.user
    embedTitle = f"{user.display_name}'s Inventory"
    embedBody = ""

    with open("./userdata.json") as file:
        data: dict= json.load(file)
        userData = data.get(str(user.id), {})
        inventory: dict[str, int] = userData.get("inventory", {})
        for item in inventory:
            info = getItemInfo(item, ITEM_DEFINITIONS)
            if info is None:
                continue
            embedBody += f"{inventory[item]}x {info["name"]} (`{item}`)"
    embed = discord.Embed(title=embedTitle, description=embedBody, color=USAGI_COLOR)
    await interaction.response.send_message(embed=embed)

@bot.tree.command()
async def items(interaction: discord.Interaction, item: str):
    """Displays the info about a given item"""
    info = getItemInfo(item, ITEM_DEFINITIONS)
    if info is None:
        await interaction.response.send_message("I couldn't find that item, sorry!")
    else:
        embedBody = f"ID: {item}\nName: {info['name']}\nDescription: {info['description']}\nSell Value: {info['value']}"
        if isinstance(info['use'], str):
            embedBody += f"\nUse: {info['use']}"
        await interaction.response.send_message(embed=discord.Embed(description=embedBody, color=USAGI_COLOR))

@bot.tree.command()
@discord.app_commands.default_permissions(kick_members=True)
@discord.app_commands.checks.has_permissions(kick_members=True)
async def kick(interaction: discord.Interaction, user: discord.Member, reason: str | None = None):
    """Kicks a user from the guild, sending a DM to them as well as putting it in the mod log"""
    author = interaction.user
    if (type(author) == discord.Member):
        if(author.roles[-1] <= user.roles[-1]):
            await interaction.response.send_message(f"You do not have the ability to ban {user.display_name}!", ephemeral=True)
            return
    channel = bot.get_channel(MODLOG_CHANNEL_ID)
    if type(channel) == discord.TextChannel:
        embed = modlogEmbed("kick", user, interaction.user, reason)
        await channel.send(embed=embed)
    try:
        await user.send(f"You have been kicked from {interaction.guild}!{f"\n{reason}" if reason != None else ''}")
    except:
        print(f"Could not DM {user.name}")
    await user.kick(reason=reason)
    await interaction.response.send_message(f"Kicked {user.display_name}!", ephemeral=True)

@bot.tree.command()
@discord.app_commands.default_permissions(moderate_members=True)
@discord.app_commands.checks.has_permissions(moderate_members=True)
async def listwarnings(interaction: discord.Interaction, user: discord.Member):
    """Lists the past warnings for the user in question"""
    with open("./userdata.json") as file:
        data: dict = json.load(file)
        userData: dict = data.get(str(user.id), {})
        warnings: list = userData.get("warnings", [])
    if len(warnings) == 0:
        await interaction.response.send_message(f"{user.display_name} does not have any warnings!")
    else:
        response = f"{user.display_name} has {len(warnings)} warnings:"
        for warning in warnings:
            response += '\n' + warning
        await interaction.response.send_message(response)

@bot.tree.command()
@discord.app_commands.default_permissions(manage_messages=True)
@discord.app_commands.checks.has_permissions(manage_messages=True)
@discord.app_commands.describe(trigger="The text which triggers the reaction you want to delete")
async def removereactiontrigger(interaction: discord.Interaction, trigger: str):
    """Removes a trigger to react to specific message content with a predefined message and/or image"""
    for item in REACTION_TRIGGERS:
        if trigger == item["trigger"]:
            REACTION_TRIGGERS.remove(item)
            with open("./reactiontriggers.json", 'w') as file:
                json.dump(REACTION_TRIGGERS, file)
            await interaction.response.send_message("Removed the specified trigger!", ephemeral=True)
            return
    await interaction.response.send_message("Could not find the specified trigger!", ephemeral=True)

@bot.tree.command()
async def sell(interaction: discord.Interaction, item: str):
    user = interaction.user
    with open("./userdata.json") as file:
        data: dict= json.load(file)
        userData = data.get(str(user.id), {})
        inventory: dict[str, int] = userData.get("inventory", {})
        if inventory.get(item, 0) == 0:
            await interaction.response.send_message(f"You don't have any {item} to sell!")
            return
    itemInfo = getItemInfo(item, ITEM_DEFINITIONS)
    if itemInfo is None:
        print(f"User {user.display_name} tried to sell their item {item} without valid definition!")
        await interaction.response.send_message(f"Uh oh, you appear to have {item}, but I don't know its info!")
    else:
        removeItem(user.id, item)
        addMagia(user.id, itemInfo['value'])
        await interaction.response.send_message(f"Successfully sold a(n) {item}!")

@bot.tree.command()
@discord.app_commands.choices(choices = [discord.app_commands.Choice(name=x.upper().replace('_', ' '), value=x) for x in SHOPS])
async def shop(interaction: discord.Interaction, choices: discord.app_commands.Choice[str]):
    """Shows the items in a shop to the user!"""
    with open("./shop.json") as file:
        data: dict[str, dict[str, int]] = json.load(file)
        items: dict[str, int] = data[choices.value]
    embed = discord.Embed(title=f"Shop - {choices.name}")
    for item, cost in items:
        embed.add_field(name=item, value=f"Cost: {cost}")
    await interaction.response.send_message(embed)

@bot.tree.command()
async def source(interaction: discord.Interaction):
    """Get a link to the source code!"""
    await interaction.response.send_message(f"Here's my source code!\n{SOURCE_CODE_URL}")

@bot.tree.command()
@discord.app_commands.default_permissions(moderate_members=True)
@discord.app_commands.checks.has_permissions(moderate_members=True)
@discord.app_commands.describe(length="The integer number of minutes you want to time someone out for")
async def timeout(interaction: discord.Interaction, user: discord.Member, length: int, reason: str | None = None):
    """Applies a timeout to the user in the guild, sending a DM to them as well as putting it in the mod log"""
    author = interaction.user
    if (type(author) == discord.Member):
        if(author.roles[-1] <= user.roles[-1]):
            await interaction.response.send_message(f"You do not have the ability to timeout {user.display_name}!", ephemeral=True)
            return
    delta = datetime.timedelta(minutes=int(length))
    channel = bot.get_channel(MODLOG_CHANNEL_ID)
    if type(channel) == discord.TextChannel:
        embed = modlogEmbed("timeout", user, interaction.user, reason)
        await channel.send(embed=embed)
    try:
        await user.send(f"You have been timed out from {interaction.guild} for {length} minute(s)!{f"\n{reason}" if reason != None else ''}")
    except:
        print(f"Could not DM {user.name}")
    await user.timeout(delta, reason=reason)
    await interaction.response.send_message(f"Timed out {user.display_name} for {length} minute(s)!", ephemeral=True)

@bot.tree.command()
async def useitem(interaction: discord.Interaction, item: str):
    """Activates the 'use' function of an item, if present."""
    # I have no clue what the heck anyone is going to add as a function for the items' uses, so I'm gonna play it safe and assume we need a followup here
    await interaction.response.defer()
    with open("./userdata.json") as file:
        data = json.load(file)
        userData = data.get(str(interaction.user.id), {})
        inventory: dict[str, int] = userData.get("inventory", {})
        if inventory.get(item, 0) == 0:
            await interaction.followup.send(f"You don't have any {item} to use!")
            return
    
    itemInfo = getItemInfo(item, ITEM_DEFINITIONS)
    if itemInfo is None:
        print(f"User {interaction.user.display_name} tried to use their item {item} without valid definition!")
        await interaction.followup.send(f"Uh oh, you appear to have {item}, but I don't know its info!")
    else:
        useAction = itemInfo.get("use", None)
        if useAction is None:
            await interaction.followup.send(f"Your {item} doesn't have a use defined!")
        else:
            session = bot.session
            eval(f"await use_actions.{useAction}")
            removeItem(interaction.user.id, item)

@bot.tree.command()
@discord.app_commands.default_permissions(moderate_members=True)
@discord.app_commands.checks.has_permissions(moderate_members=True)
async def warn(interaction: discord.Interaction, user: discord.Member, reason: str):
    """Warns a user in the guild, sending a DM to them as well as putting it in the mod log. Also logs the warning in a file to keep track."""
    channel = bot.get_channel(MODLOG_CHANNEL_ID)
    if type(channel) == discord.TextChannel:
        embed = modlogEmbed("warn", user, interaction.user, reason)
        await channel.send(embed=embed)
    try:
        await user.send(f"You have been warned in {interaction.guild}!\n{reason}")
    except:
        print(f"Could not DM {user.name}")
    # This is TECHNICALLY blocking, but async file handling doesn't really work
    # And this is being run on a single core system so threaded approaches probably don't work any better
    with open("./userdata.json", 'r+') as file:
        data: dict = json.load(file)
        # Erase the contents of the file
        file.truncate(0)
        # Return pointer to the start of the file
        file.seek(0)
        userData: dict = data.get(str(user.id), {})
        warnings: list = userData.get("warnings", [])
        warnings.append(reason)
        userData['warnings'] = warnings
        data[str(user.id)] = userData
        json.dump(data, file)
    await interaction.response.send_message(f"Warned {user.display_name}!", ephemeral=True)
    
@bot.event
async def on_message(message: discord.Message):
    # Do not recursively trigger ourselves, or get triggered by other bots
    if message.author.bot:
        return
    
    # Handle Magia gain for the economy
    if (message.author.id in LAST_MAGIA_MESSAGE):
        if (message.created_at - LAST_MAGIA_MESSAGE[message.author.id]).total_seconds() > MAGIA_EARN_DELAY:
            addMagia(message.author.id, MAGIA_EARN_AMOUNT)
            LAST_MAGIA_MESSAGE[message.author.id] = datetime.datetime.now()
    else:
        addMagia(message.author.id, MAGIA_EARN_AMOUNT)
        LAST_MAGIA_MESSAGE[message.author.id] = datetime.datetime.now()
    
    # Handle actual commands, because this is probably eating the normal way to define them
    if message.content.startswith("u!"):
        if message.content == "u!sync":
            print("Attempting to sync slash commands")
            # Only the owner(s) should be able to do this
            # Necessary for slash commands to populate
            if bot.is_owner(message.author):
                await bot.tree.sync()
        return

    # Handles reaction triggers
    # Only the first found trigger occurs
    for trigger in REACTION_TRIGGERS:
        if trigger["trigger"] in message.content:
            text: str | None = None if trigger["message"] == '' else trigger["message"]
            if trigger["image"] != '':
                file = await getImageFromURL(bot.session, trigger["image"], "reaction")
                if (file != None):
                    await message.channel.send(content=text, file=file)
                    return
            await message.channel.send(content=text)
            return

# Add custom status!
@bot.event
async def on_ready():
    print('USAGI online!')
    await bot.change_presence(activity=discord.CustomActivity(name='Patrolling the celestia library! | <3 to you all!', emoji='⭐'))

bot.run(BOT_TOKEN)
