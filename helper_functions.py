import discord
import aiohttp

from io import BytesIO
import json
import random

"""
Helper functions to keep main.py clean.
Generally, if you're using something in multiple places (or expect to in the future), then it should go here.
Particularly useful for hiding away aiohttp logic.
"""

Image = discord.File

def modlogEmbed(type: str, user: discord.Member | discord.User, moderator: discord.Member | discord.User, reason: str | None) -> discord.Embed:
    if reason is None:
        reason = "No reason specified"
    color : discord.Color
    match type:
        case "ban":
            color = discord.Color.red()
        case "kick":
            color = discord.Color.orange()
        case _:
            color = discord.Color.yellow()

    embedBody = f"**Member:** {user.name} ({user.mention})\n**Moderator:** {moderator.display_name}\n**Reason:** {reason}"
    return discord.Embed(title=f"{type}: {user.display_name}", colour=color, description=embedBody)

async def getImageFromURL(session: aiohttp.ClientSession, url: str, name: str = "image") -> Image | None:
    """Handles getting an image from a URL. Does not support video files."""
    async with session.get(url) as response:
        if (response.status == 200):
            mimeType = response.headers.get("content-type")
            if (mimeType is None):
                print(f"getImageFromURL: URL {url} did not return a content type!")
                return None
            fileCategory, fileType = mimeType.split('/')
            if (fileCategory != "image"):
                print(f"getImageFromURL: URL {url} did not return an image!")
                return None
            buffer = BytesIO(await response.read())
            filename = name + "." + fileType
            return discord.File(fp=buffer, filename=filename)
        else:
            print(f"getImageFromURL: URL {url} returned HTTP {response.status}!")
            return None

def addMagia(id: int, amount: int):
    """Adds Magia to a given user's balance"""
    with open("./userdata.json", 'r+') as file:
        data: dict = json.load(file)
        # Erase the contents of the file
        file.truncate(0)
        # Return pointer to the start of the file
        file.seek(0)
        userData: dict = data.get(str(id), {})
        balance: int = userData.get("balance", 0)
        balance += amount
        userData['balance'] = balance
        data[str(id)] = userData
        json.dump(data, file)

def removeMagia(id: int, amount: int):
    """Removes Magia from a given user's balance"""
    with open("./userdata.json", 'r+') as file:
        data: dict = json.load(file)
        # Erase the contents of the file
        file.truncate(0)
        # Return pointer to the start of the file
        file.seek(0)
        userData: dict = data.get(str(id), {})
        balance: int = userData.get("balance", 0)
        balance -= amount
        userData['balance'] = balance
        data[str(id)] = userData
        json.dump(data, file)

def addItem(id: int, item: str, amount: int = 1):
    """Adds an item to the user's inventory"""
    with open("./userdata.json", 'r+') as file:
        data: dict = json.load(file)
        # Erase the contents of the file
        file.truncate(0)
        # Return pointer to the start of the file
        file.seek(0)
        userData: dict = data.get(str(id), {})
        inventory: dict[str, int] = userData.get("inventory", {})
        inventory[item] = inventory.get(item, 0) + amount
        userData['inventory'] = inventory
        data[str(id)] = userData
        json.dump(data, file)

def removeItem(id: int, item: str, amount: int = 1):
    """Removes an item from the user's inventory"""
    with open("./userdata.json", 'r+') as file:
        data: dict = json.load(file)
        # Erase the contents of the file
        file.truncate(0)
        # Return pointer to the start of the file
        file.seek(0)
        userData: dict = data.get(str(id), {})
        inventory: dict[str, int] = userData.get("inventory", {})
        inventory[item] -= amount
        userData['inventory'] = inventory
        data[str(id)] = userData
        json.dump(data, file)

def getItemInfo(item: str, sources:list[str]) -> dict | None:
    """Gets the item info for an item for the purposes of a description or otherwise displaying it in a more user-friendly format"""
    for source in sources:
        with open(source) as file:
            data: dict = json.load(file)
            if item in data:
                return data[item]
    print(f"Info requested for Unknown Item ID {item}")
    return None

def gachaPull(gacha: str) -> str:
    """Handles the process of pulling for an item in the gacha system"""
    with open("./gachas.json") as gachaFile:
        data: dict = json.load(gachaFile)
        chosen: dict = data[gacha]
    # Fillers are miscellaneous books meant to fill in the gaps left by the other books
    fillers: list[str] = chosen.pop("FILLER")
    # How much is taken up by books with specified percentage odds
    totalPercent = 0
    options = []
    weights = []
    for item in chosen:
        options.append(item)
        weights.append(chosen[item])
        totalPercent += chosen[item]
    fillerWeight = (100 - totalPercent) / len(fillers)
    for filler in fillers:
        options.append(filler)
        weights.append(fillerWeight)
    return random.choices(options, weights)[0]
        