import discord, base64
from discord.ext import commands
from discord import app_commands

class Base64(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="base64-decode", description="decode base64")
    @app_commands.describe(string="text")
    async def unb64(self, ctx: commands.Context, string: str):
        try:
            await ctx.response.send_message(f"decoded:\n`{base64.b64decode(string+'==').decode('utf-8')}`")
        except Exception as e:
            await ctx.channel.send(f"500 internal server error\n-# {e}")

    @app_commands.command(name="base64-encode", description="undecode base64")
    @app_commands.describe(string="text")
    async def b64(self, ctx: commands.Context, string: str):
        try:
            byte = base64.b64encode(bytes(string, 'utf-8')) # bytes
            await ctx.response.send_message(f"encoded:\n`{byte.decode('utf-8')}`")
        except Exception as e:
            await ctx.channel.send(f"500 internal server error\n-# {e}")

async def setup(bot):
    await bot.add_cog(Base64(bot))
