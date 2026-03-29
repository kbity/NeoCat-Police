import discord, base64, random
from discord.ext import commands
from discord import app_commands

class Fun(commands.Cog):
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

    @app_commands.command(name="reverse", description="reverses text")
    @app_commands.describe(text="text to reverse")
    async def reverse(self, ctx: commands.Context, text: str):
        await ctx.response.send_message(text[::-1])

    @app_commands.command(name="randomcase", description="randomizes case of text")
    @app_commands.describe(text="text to randomize case")
    async def randomcase(self, ctx: commands.Context, text: str):
        kreisifed = ''.join(x.upper() if random.randint(0,1) else x for x in text.lower())
        await ctx.response.send_message(kreisifed)

    @app_commands.command(name="dice", description="roles an amount of dices with sides")
    @app_commands.describe(sides="d1 to d1000", count="1 to 100 dice")
    async def dice(self, ctx: commands.Context, sides: int = 6, count: int = 1):
        emojis = self.bot.custom_emojis

        if count < 1:
            await ctx.response.send_message(f"{emojis['neocat_cry']} you have **0** dice")
            return
        if count > 100:
            await ctx.response.send_message(f"{emojis['normal']} you try to roll the dice but **they scatter all over the place and you dont know what the hell you're doing**")
            return
        if (sides > 1000) or sides == 0:
            c = ""
            if count > 1:
                c = "c"
            await ctx.response.send_message(f"🎱 your spherical 'di{c}e' has rolled **away**")
            return
        if sides < 0:
            await ctx.response.send_message(f"get out")
            return

        if count == 1:
            if sides == 2:
                num = random.randint(1, 2)
                face = "Heads"
                if num == 2:
                    face = "Tails"
                await ctx.response.send_message(f"🪙 your coin has landed on **{face}** ({num})")
            else:
                await ctx.response.send_message(f"🎲 your d{sides} die has rolled a **{random.randint(1, sides)}**")
        else:
            diec = []
            for die in range(count):
                diec.append(random.randint(1, sides))
            await ctx.response.send_message(f"🎲 your d{sides} dice have rolled {diec} for a total of **{sum(diec)}**")

    @app_commands.command(name="tip", description="unexpected tip")
    @app_commands.describe(id = 'uhhhhhh')
    async def tip(self, ctx: commands.Context, id: int = None):
        tips = self.bot.tips
        emojis = self.bot.custom_emojis

        if id is None:
            await ctx.response.send_message(emojis["tips"]+" "+random.choice(tips))
        else:
            if 1 > id:
                await ctx.response.send_message(emojis["tips"]+" You're not funny.")
                return
            if id > len(tips):
                await ctx.response.send_message(f"limit is {len(tips)}")
            else:
                await ctx.response.send_message(emojis["tips"]+" "+tips[id-1])

async def setup(bot):
    await bot.add_cog(Fun(bot))
