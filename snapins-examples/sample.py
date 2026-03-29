import discord
from discord.ext import commands
from discord import app_commands

class SampleSnapin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="snapin-command", description="Snapin test command")
    async def ping(self, interaction: discord.Interaction):
        await interaction.response.send_message("Add commands with a *Snap*-in!")

    @app_commands.command(name="error", description="error")
    async def ping(self, interaction: discord.Interaction):
        raise Exception("a bunch of wild ducks flew by and caused an error.")

async def setup(bot):
    await bot.add_cog(SampleSnapin(bot))
