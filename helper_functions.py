import discord

"""
Helper functions to keep main.py clean.
Generally, if you're using something in multiple places (or expect to in the future), then it should go here.
Particularly useful for hiding away aiohttp logic.
"""

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
