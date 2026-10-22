import discord
import aiohttp
import helper_functions

"""
Dedicated solely to housing dynamic use actions for items.
Any function you want an item to be able to have as their 'use' should be defined here.
All functions declared here should be async for the sake of good code practice

Available parameters (i.e. things you can include in the parameters and have it automatically pull from the bot):
- `interaction` (discord.Interaction, i.e. the use of the command itself)
  - In order to send messages with the interaction, use interaction.followup.send (and the like)
- `session` (aiohttp session)
- anything global in here or in main.py
More parameters can be added in the actual function over in main.py
The full function name + parameters should be in the item info
"""

async def example(interaction: discord.Interaction, session: aiohttp.ClientSession):
    """
    A basic example function to show how one might set up a use action function
    In the item info this would be `"example(interaction, session)"`
    """
    user = interaction.user.id
    helper_functions.addMagia(user, 100)
    coolImage = await helper_functions.getImageFromURL(session, "https://nekos.best/api/v2/neko/9e63b4c3-6335-4fbe-ba02-6372a0099c75.png", "catgirl.png")
    if (coolImage != None):
        await interaction.followup.send(file=coolImage)
