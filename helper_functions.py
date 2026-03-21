import discord
import aiohttp

from io import BytesIO
import json

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