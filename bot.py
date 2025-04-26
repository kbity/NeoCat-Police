import discord
import typing
import json
import enum
import time
import datetime
import aiohttp
import random
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import has_permissions, MissingPermissions
from discord.ui import Button, View
from discord.utils import get
from typing import Literal

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='ploice!', intents=intents)
tree = bot.tree

bot.session = None

# Load existing data from db.json
def load_db():
    try:
        with open('db.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

# Save data to db.json
def save_db(data):
    with open('db.json', 'w') as f:
        json.dump(data, f, indent=4)

class truefalse(str, enum.Enum):
    Yes = "yes"
    No = "no"

def convert_time_to_seconds(time_str):
    time_unit = time_str[-1]  # Get the last character which indicates the unit (e.g., 'd')
    time_value = int(time_str[:-1])  # Get the numeric value (e.g., '4')

    if time_unit == 'w':
        return time_value * 604800  # 1 week = 604800 seconds
    elif time_unit == 'd':
        return time_value * 86400  # 1 day = 86400 seconds
    elif time_unit == 'h':
        return time_value * 3600  # 1 hour = 3600 seconds
    elif time_unit == 'm':
        return time_value * 60  # 1 minute = 60 seconds
    elif time_unit == 's':
        return time_value  # Already in seconds
    else:
        raise ValueError("Unsupported time unit")

@bot.event
async def on_ready():
    await bot.tree.sync()  # Synchronize the commands with Discord
    bot.session = aiohttp.ClientSession()
    print(f"yiur bto is runnign :3")

@bot.hybrid_command(name="speak", description="says something")
@app_commands.describe(message="what to says")
async def speak(ctx: commands.Context, message: str):
    try:
        await ctx.send(message)
    except Exception as e:
        await ctx.channel.send(f"504 internal server error\n-# {e}")

@bot.hybrid_command(name="ping", description="tests roundtrip latency")
async def ping(ctx: commands.Context):
    try:
        await ctx.send(f"<:amadaping:1280061745280454792> Pong!! ctqa brain has a latency of {round(bot.latency *1000)} ms")
    except Exception as e:
        await ctx.channel.send(f"504 internal server error\n-# {e}")

@bot.hybrid_command(name="info", description="about this bot")
async def info(ctx: commands.Context):
    embed = discord.Embed(
        title="About ctqa ploice",
        description="`ctqa ploice` is a clone of @milenako's 'Cat police' bot, specifically for Cat Stand. Both bots function very similarly, but with some changes, such as ctqa ploice lacking AI, dimentia chat, Cat Bot statistics commands, and not being hard coded for Cat Stand. ctqa ploice is inspired by tema5002's Cat Bot clone called `ctqa bto`, a clone of Cat Bot written in C# that is no longer online.",
        color=discord.Color.blue()
    )
    embed.set_footer(text="ctqa police v1.1.1")
    try:
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.channel.send(f"504 internal server error\n-# {e}")

@bot.hybrid_command(name="tip", description="unexpected tip")
async def info(ctx: commands.Context):
    tips = ["ctqa ploice was developed with the help of stella", "this bot is inspired by ctqa bto", "this bot allows for your server having its own yapping city", "ctqa bto has a planned C rewrite", "this bot is made of 74% ai slop", "i eat sand", "this bot lacks its own AI", "bird used to have moderation commands, but they sucked.", "unlike real cat police, ctqa ploice can be used in your own servers.", "this bot allows for an unlimited amount of starboards", "ctqa ploice is made in python using discord.py", "mari2 created ctqa ploice", "ctqa ploice has message logging", "yapping cities in ctqa ploice actually send the post author deleted images, unlike the real Cat Police", "the starboard spits out various console exceptions, despite working just fine"]
    try:
        await ctx.send("<:tips:1365575538986450996> "+random.choice(tips))
    except Exception as e:
        await ctx.channel.send(f"504 internal server error\n-# {e}")

@bot.hybrid_command(name="ban", description="yeet but harder")
@commands.has_permissions(ban_members=True)
@discord.app_commands.default_permissions(ban_members=True)
@app_commands.describe(user="the nerd to yeet")
@app_commands.describe(reason="reason (e.g. memes in general)")
async def ban(ctx: commands.Context, user: discord.User, reason: str = "No reason provided", appeal: truefalse = "yes"):
    # Define the button
    button = discord.ui.Button(label="Confirm", style=discord.ButtonStyle.secondary)

    # Define the callback function for the button
    async def button_callback(interaction: discord.Interaction):
        if interaction.user != ctx.author:
            await interaction.response.send_message("403 forbidden", ephemeral=True)
            return

        # Perform the ban and stuff
        try:
            db = load_db()
            # Retrieve the appeal message
            server_id = str(ctx.guild.id)
            appeal_info = db.get(server_id, {})
            # Ensure appeal_message is defined
            appeal_message = appeal_info.get("appeal_message", "you cant appeal this ban.") if appeal == "yes" else "you cant appeal this ban."
            await user.send(f"hello nerd you might have been banned from {ctx.guild.name} for `{reason}`. {appeal_message}")

       #you cant appeal this ban.
        except Exception as e:
            print(f"Failed to send DM: {e}")

        await interaction.guild.ban(user, reason=reason, delete_message_seconds=0)
        await log_action(ctx.guild, f"{user} was permanently banned by {ctx.author} for `{reason}`.")
        await interaction.response.edit_message(content=f"{user.mention} was permanently banned by {interaction.user.mention} for `{reason}`.", view=None)

    # Assign the callback to the button
    button.callback = button_callback

    view = discord.ui.View()
    view.add_item(button)
    try:
        await ctx.send(f"Banning {user.mention}?", view=view)
    except Exception as e:
        await ctx.channel.send(f"504 internal server error\n-# {e}")

@ban.error
async def ban_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send("403 forbidden", ephemeral=True)

@bot.hybrid_command(name="appeal", description="how did we get here")
@commands.has_permissions(manage_guild=True)
@discord.app_commands.default_permissions(manage_guild=True)
@app_commands.describe(appeal="how the fuck do you appeal")
async def speak(ctx: commands.Context, appeal: str):
    # Load the database
    db = load_db()

    # Save the appeal message and server ID
    server_id = str(ctx.guild.id)
    # Ensure the server ID exists in the database
    if server_id not in db:
        db[server_id] = {}

    db[server_id]["appeal_message"] = appeal


    # Save the updated database
    save_db(db)
    try:
        await log_action(ctx.guild, f"appeal message set to {appeal} for {ctx.guild.name} by {ctx.author}.")
        await ctx.send(f"appeal message set to {appeal} for {ctx.guild.name}")
    except Exception as e:
        await ctx.channel.send(f"504 internal server error\n-# {e}")

@bot.hybrid_command(name="kick", description="yeet")
@commands.has_permissions(kick_members=True)
@discord.app_commands.default_permissions(kick_members=True)
@app_commands.describe(user="the nerd to yeet")
@app_commands.describe(reason="reason (e.g. memes in general)")
async def kick(ctx: commands.Context, user: discord.User, reason: str):
    # Define the button
    button = discord.ui.Button(label="Confirm", style=discord.ButtonStyle.secondary)

    # Define the callback function for the button
    async def button_callback(interaction: discord.Interaction):
        if interaction.user != ctx.author:
            await interaction.response.send_message("403 forbidden", ephemeral=True)
            return

        # Perform the kick and stuff
        try:
            await user.send(f"hello nerd you might have been kicked from {ctx.guild.name} for `{reason}`.")
        except Exception as e:
            print(f"Failed to send DM: {e}")

        await interaction.guild.kick(user, reason=reason)
        await log_action(ctx.guild, f"{user} was kicked by {ctx.author} for `{reason}`.")
        await interaction.response.edit_message(content=f"{user.mention} was kicked by {interaction.user.mention} for `{reason}`.", view=None)

    # Assign the callback to the button
    button.callback = button_callback

    view = discord.ui.View()
    view.add_item(button)
    try:
        await ctx.send(f"Kicking {user.mention}?", view=view)
    except Exception as e:
        await ctx.channel.send(f"504 internal server error\n-# {e}")

@kick.error
async def kick_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send("403 forbidden", ephemeral=True)

@bot.hybrid_command(name="lock", description="lock emoji")
@commands.has_permissions(manage_channels=True)
@discord.app_commands.default_permissions(manage_channels=True)
async def lock(ctx: commands.Context):
    perms = ctx.channel.overwrites_for(ctx.guild.default_role)
    perms.send_messages=False
    await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=perms)
    await log_action(ctx.guild, f"🔒 {ctx.channel.mention} has been locked by {ctx.author.mention}")
    try:
        await ctx.send(f"🔒 {ctx.channel.mention} has been locked by {ctx.author.mention}")
    except Exception as e:
        await ctx.channel.send(f"504 internal server error\n-# {e}")
@lock.error
async def kick_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send("403 forbidden", ephemeral=True)

@bot.hybrid_command(name="unlock", description="key emoji")
@commands.has_permissions(manage_channels=True)
@discord.app_commands.default_permissions(manage_channels=True)
async def unlock(ctx: commands.Context):
    perms = ctx.channel.overwrites_for(ctx.guild.default_role)
    perms.send_messages=True
    await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=perms)
    await log_action(ctx.guild, f"🔓 {ctx.channel.mention} has been unlocked by {ctx.author.mention}")
    try:
        await ctx.send(f"🔓 {ctx.channel.mention} has been unlocked by {ctx.author.mention}")
    except Exception as e:
        await ctx.channel.send(f"504 internal server error\n-# {e}")
@unlock.error
async def kick_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send("403 forbidden", ephemeral=True)

@bot.hybrid_command(name="mute", description="hahah imagine being a mute")
@commands.has_permissions(moderate_members=True)
@discord.app_commands.default_permissions(moderate_members=True)
@app_commands.describe(user="your free trial of talking has ended")
@app_commands.describe(lengh="lengh of no yap perms (e.g. 4d)")
@app_commands.describe(reason="i muted you becuz your annoying")
async def mute(ctx: commands.Context, user: discord.User, lengh: str, reason: str):
    clock = convert_time_to_seconds(lengh)
    try:
        await user.timeout(datetime.timedelta(seconds=clock), reason=f"{reason}")
        await log_action(ctx.guild, f"{user.mention} was muted by {ctx.author.mention} for `{reason}`! This mute expires <t:{round(time.time()) + clock}:R>")
        await ctx.send(f"{user.mention} was muted by {ctx.author.mention} for `{reason}`! This mute expires <t:{round(time.time()) + clock}:R>")
    except Exception as e:
        await ctx.channel.send(f"504 internal server error\n-# {e}")
    try:
        await user.send(f"hello nerd you might have been muted in {ctx.guild.name} for `{reason}`.")
    except Exception as e:
        print(f"Failed to send DM: {e}")
@mute.error
async def kick_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send("403 forbidden", ephemeral=True)

@bot.hybrid_command(name="nickname", description="change someone's identity (nickname)")
@commands.has_permissions(manage_nicknames=True)
@discord.app_commands.default_permissions(manage_nicknames=True)
@app_commands.describe(user="who do you want to rename")
@app_commands.describe(new_nickname="their new embarrassing identity")
async def nickname(ctx: commands.Context, user: discord.Member, new_nickname: str):
    try:
        await user.edit(nick=new_nickname)
        await ctx.send(f"{ctx.author.mention} renamed {user.mention} to `{new_nickname}`.")
        await log_action(ctx.guild, f"{ctx.author.mention} renamed {user.mention} to `{new_nickname}`.")
    except discord.Forbidden:
        await ctx.send("cant :skull:")
    except Exception as e:
        await ctx.channel.send(f"504 internal server error\n-# {e}")

@nickname.error
async def nickname_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send("403 forbidden", ephemeral=True)

@bot.hybrid_command(name="unmute", description="wtf i can talk")
@commands.has_permissions(moderate_members=True)
@discord.app_commands.default_permissions(moderate_members=True)
@app_commands.describe(user="Mods, unmute this person")
@app_commands.describe(reason="why ummute tbh")
async def unmute(ctx: commands.Context, user: discord.User, reason: str):
    try:
        await ctx.send(f"{user.mention} was unmuted by {ctx.author.mention} for `{reason}`.")
        await log_action(ctx.guild, f"{user.mention} was unmuted by {ctx.author.mention} for `{reason}`!")
        await user.timeout(None, reason=f"{reason}")
    except Exception as e:
        await ctx.channel.send(f"504 internal server error\n-# {e}")
@unmute.error
async def kick_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send("403 forbidden", ephemeral=True)

@bot.hybrid_command(name="unban", description="unyeet??")
@commands.has_permissions(ban_members=True)
@discord.app_commands.default_permissions(ban_members=True)
@app_commands.describe(user="the nerd to... unyeet")
@app_commands.describe(reason="why was the user unyeet")
async def unban(ctx: commands.Context, user: discord.User, reason: str = "No reason provided"):
    try:
        await ctx.guild.unban(user, reason=reason)
        await log_action(ctx.guild, f"{user.mention} was unbanned by {ctx.author.mention} for `{reason}`!!!")
        await ctx.send(content=f"{user.mention} was unbanned by {ctx.author.mention} for `{reason}`!!!")
    except Exception as e:
        await ctx.channel.send(f"504 internal server error\n-# {e}")

@ban.error
async def ban_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send("403 forbidden", ephemeral=True)

@bot.hybrid_command(name="purge", description="Ooh, live the dream with a time machine")
@commands.has_permissions(manage_messages=True)
@discord.app_commands.default_permissions(manage_messages=True)
@app_commands.describe(user="user to purge")
@app_commands.describe(limit="max ammount is 1000")
async def purge(ctx: commands.Context, limit: int, user: discord.User = None):
    # Ensure the limit is within bounds
    limit = max(1, min(limit, 1000))

    # Define a check function to filter messages
    def check(msg):
        return user is None or msg.author == user

    # Perform the bulk delete
    deleted = await ctx.channel.purge(limit=limit, check=check)

    # Send a confirmation message
    try:
        await ctx.send(content=f"Last {len(deleted)} messages{' from ' + user.mention if user else ''} were purged by {ctx.author.mention}.")
        await log_action(ctx.guild, f"Last {len(deleted)} messages{' from ' + user.mention if user else ''} were purged by {ctx.author.mention}.")
    except Exception as e:
        await ctx.channel.send(f"504 internal server error\n-# {e}")
@ban.error
async def ban_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send("403 forbidden", ephemeral=True)

@bot.hybrid_command(name="slowmode", description="change the speed of the chat")
@commands.has_permissions(manage_channels=True)
@discord.app_commands.default_permissions(manage_channels=True)
@app_commands.describe(slowmode="slowmode time. max is 6 hours you goob, please specifiy unit")
async def slowmode(ctx: commands.Context, slowmode: str):
    delay = convert_time_to_seconds(slowmode)
    try:
        await ctx.channel.edit(slowmode_delay=delay)
        await log_action(ctx.guild, f"{slowmode} slowmode in {ctx.channel.mention} set by {ctx.author.mention}.")
        await ctx.send(f":zzz: Now going at {slowmode} slowmode!")
    except Exception as e:
        await ctx.channel.send(f"504 internal server error\n-# {e}")
@slowmode.error
async def ban_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send("403 forbidden", ephemeral=True)

@bot.hybrid_command(name="log", description="set up logging")
@commands.has_permissions(manage_guild=True)
@discord.app_commands.default_permissions(manage_guild=True)
@app_commands.describe(type="what type of logs to set (message/action)")
@app_commands.describe(channel="where the logs go")
async def log(ctx: commands.Context, type: str, channel: discord.TextChannel):
    db = load_db()
    server_id = str(ctx.guild.id)

    if server_id not in db:
        db[server_id] = {}

    if type.lower() == "message":
        db[server_id]["message_log_channel"] = channel.id
        await ctx.send(f"message logs will go to {channel.mention}")
    elif type.lower() == "action":
        db[server_id]["action_log_channel"] = channel.id
        await ctx.send(f"action logs will go to {channel.mention}")
    else:
        await ctx.send("Invalid type! Choose either `message` or `action`.")

    save_db(db)

async def log_action(guild: discord.Guild, content: str):
    db = load_db()
    guild_id = str(guild.id)
    channel_id = db.get(guild_id, {}).get("action_log_channel")
    if channel_id:
        channel = guild.get_channel(channel_id)
        if channel:
            await channel.send(content, allowed_mentions=discord.AllowedMentions.none())

import aiohttp
import io

@bot.event
async def on_message_delete(message: discord.Message):
    if message.guild is None or message.author.bot:
        return

    db = load_db()
    guild_id = str(message.guild.id)
    channel_id = db.get(guild_id, {}).get("message_log_channel")

    if channel_id:
        channel = message.guild.get_channel(channel_id)
        if channel:
            embed = discord.Embed(color=discord.Color.from_str("#ff0000"))

            if message.content:
                embed.description = message.content[:4096]

            files = []
            if message.attachments:
                # Attempt to download each attachment
                async with aiohttp.ClientSession() as session:
                    for attachment in message.attachments:
                        try:
                            async with session.get(attachment.url) as resp:
                                if resp.status == 200:
                                    data = await resp.read()
                                    fp = io.BytesIO(data)
                                    fp.seek(0)
                                    files.append(discord.File(fp, filename=attachment.filename))
                        except Exception as e:
                            print(f"Failed to download attachment: {attachment.url} — {e}")

            embed.set_author(name=f"{message.author}'s message was deleted", icon_url=message.author.display_avatar.url)
            embed.set_footer(text=f"#{message.channel.name}")

            await channel.send(embed=embed, files=files, allowed_mentions=discord.AllowedMentions.none())

@bot.event
async def on_message_edit(before: discord.Message, after: discord.Message):
    if before.guild is None or before.author.bot or before.content == after.content:
        return

    db = load_db()
    guild_id = str(before.guild.id)
    channel_id = db.get(guild_id, {}).get("message_log_channel")

    if channel_id:
        channel = before.guild.get_channel(channel_id)
        if channel:
            embed = discord.Embed(
                color=discord.Color.from_str("#757e8a")
            )
            embed.add_field(name="Before", value=before.content[:1024], inline=False)
            embed.add_field(name="After", value=after.content[:1024], inline=False)
            embed.set_author(name=str(f"{before.author} edited their message"), icon_url=before.author.display_avatar.url)
            embed.set_footer(text=f"#{before.channel.name}")
            await channel.send(embed=embed, allowed_mentions=discord.AllowedMentions.none())


@bot.tree.command(name="starboard", description="where good messages go")
@commands.has_permissions(manage_guild=True)
@discord.app_commands.default_permissions(manage_guild=True)
@app_commands.describe(channel="WHAT !")
@app_commands.describe(emoji=":staring_ctqa:")
@app_commands.describe(threshold="how many people need to care, 0 to delete")
@app_commands.describe(starboard_id="ID for this starboard (1 = default)")
async def setstarboard(
    interaction: discord.Interaction,
    channel: discord.TextChannel,
    emoji: str = "⭐",
    threshold: int = 3,
    starboard_id: int = 1
):
    await interaction.response.defer(ephemeral=False)

    db = load_db()
    server_id = str(interaction.guild.id)

    if server_id not in db:
        db[server_id] = {}

    suffix = "" if starboard_id == 1 else f"_{starboard_id}"

    if threshold <= 0:
        # Remove this starboard config
        for key in ["channel_id", "emoji", "threshold", "webhook_url"]:
            db[server_id].pop(f"starboard_{key}{suffix}", None)
        save_db(db)
        await interaction.followup.send(f"❌ Removed starboard {starboard_id}")
        return

    # Set this starboard config
    db[server_id][f"starboard_channel_id{suffix}"] = channel.id
    db[server_id][f"starboard_emoji{suffix}"] = emoji
    db[server_id][f"starboard_threshold{suffix}"] = threshold
    save_db(db)

    await interaction.followup.send(
        f"⭐ Starboard {starboard_id} set to {channel.mention} with emoji {emoji} and threshold {threshold}."
    )

@bot.event
async def on_raw_reaction_add(payload):
    db = load_db()
    server_id = str(payload.guild_id)

    if server_id not in db:
        return

    # Try default starboard and numbered starboards
    starboard_ids = [1] + [int(k.split("_")[-1]) for k in db[server_id] if k.startswith("starboard_channel_id_")]
    starboard_ids = list(set(starboard_ids))  # Avoid duplicates

    for starboard_id in starboard_ids:
        suffix = "" if starboard_id == 1 else f"_{starboard_id}"
        emoji = db[server_id].get(f"starboard_emoji{suffix}")
        threshold = db[server_id].get(f"starboard_threshold{suffix}", 3)
        channel_id = db[server_id].get(f"starboard_channel_id{suffix}")
        webhook_url = db[server_id].get(f"starboard_webhook_url{suffix}")

        if not emoji or not channel_id:
            continue

        if payload.emoji.name != emoji and str(payload.emoji) != emoji:
            continue

        guild = bot.get_guild(payload.guild_id)
        channel = guild.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)

        for reaction in message.reactions:
            if (reaction.emoji == payload.emoji.name or str(reaction.emoji) == emoji) and reaction.count >= threshold:
                async for user in reaction.users():
                    if user.id == bot.user.id:
                        return

                try:
                    await message.add_reaction(emoji)
                except discord.HTTPException:
                    pass

                starboard_channel = bot.get_channel(channel_id)
                if not starboard_channel:
                    return

                webhook = None
                if webhook_url:
                    try:
                        webhook = discord.Webhook.from_url(webhook_url, session=bot.session)
                        # Check if the webhook is valid
                        async with aiohttp.ClientSession() as session:
                            async with session.get(webhook_url) as resp:
                                if resp.status != 200:
                                    # If the webhook is not valid, remove it from the database
                                    del db[server_id][f"starboard_webhook_url{suffix}"]
                                    save_db(db)
                                    webhook_url = None
                    except discord.InvalidData:
                        # If the webhook is not valid, remove it from the database
                        del db[server_id][f"starboard_webhook_url{suffix}"]
                        save_db(db)
                        webhook_url = None

                if webhook is None or webhook_url is None:
                    async with aiohttp.ClientSession() as session:
                        async with session.get("https://i.imgur.com/yHPNPoQ.png") as resp:
                            avatar_bytes = await resp.read() if resp.status == 200 else None

                    webhook_obj = await starboard_channel.create_webhook(
                        name="ctqa ploice webhook",
                        avatar=avatar_bytes
                    )
                    webhook_url = webhook_obj.url
                    db[server_id][f"starboard_webhook_url{suffix}"] = webhook_url
                    save_db(db)
                    webhook = webhook_obj

                author_name = f"{message.author.display_name} (#{channel.name})"
                author_name = author_name[:80] if len(author_name) > 80 else author_name
                avatar_url = message.author.avatar.url if message.author.avatar else None
                jump_url = message.jump_url
                button = Button(label="Jump to message", url=jump_url)
                view = View()
                view.add_item(button)
                files = [await attachment.to_file() for attachment in message.attachments]

                await webhook.send(
                    content=message.content or None,
                    username=author_name,
                    avatar_url=avatar_url,
                    view=view,
                    files=files,
                    wait=True
                )

@bot.hybrid_command(name="yapping-city", description="Add or remove a forum as a Yapping City forum")
@commands.has_permissions(manage_guild=True)
@discord.app_commands.default_permissions(manage_guild=True)
@app_commands.describe(action="Whether to add or remove the forum", forum="The forum channel to modify")
async def yapping_city(ctx: commands.Context, action: Literal["add", "remove"], forum: discord.ForumChannel):
    db = load_db()
    guild_id = str(ctx.guild.id)
    forum_id = str(forum.id)

    db.setdefault(guild_id, {}).setdefault("yapping_forums", {})

    if action == "add":
        db[guild_id]["yapping_forums"][forum_id] = True
        await ctx.send(f"{ctx.author.mention} set {forum.mention} as a Yapping City forum.", ephemeral=False)
        await log_action(ctx.guild, f"{ctx.author.mention} set {forum.mention} as a Yapping City forum.")
    elif action == "remove":
        if forum_id in db[guild_id]["yapping_forums"]:
            del db[guild_id]["yapping_forums"][forum_id]
            await ctx.send(f"{ctx.author.mention} unset {forum.mention} as a Yapping City forum.", ephemeral=False)
            await log_action(ctx.guild, f"{ctx.author.mention} unset {forum.mention} as a Yapping City forum.")
        else:
            await ctx.send(f"{forum.mention} is not marked as a Yapping City forum, idiot.", ephemeral=False)

    save_db(db)

@bot.hybrid_command(name="whitelist", description="Allow or remove someone from talking in your Yapping City post")
@app_commands.describe(user="The user to whitelist or remove", remove="Unwhitelist the user instead")
async def whitelist(ctx: commands.Context, user: discord.User, remove: bool = False):
    if not isinstance(ctx.channel, discord.Thread):
        return await ctx.send("You can only run this inside a thread.")

    thread = ctx.channel
    if ctx.author.id != thread.owner_id:
        return await ctx.send("Only the thread owner can manage the whitelist.")

    db = load_db()
    guild_id = str(ctx.guild.id)
    thread_id = str(thread.id)

    db.setdefault(guild_id, {}).setdefault("whitelists", {}).setdefault(thread_id, [])
    whitelist = db[guild_id]["whitelists"][thread_id]

    try:
        if remove:
            if user.id in whitelist:
                whitelist.remove(user.id)
                save_db(db)
                await ctx.send(f"{user.mention} has been removed from the whitelist.")
            else:
                await ctx.send(f"{user.mention} is not on the whitelist.")
        else:
            if user.id not in whitelist:
                whitelist.append(user.id)
                save_db(db)
                await ctx.send(f"{user.mention} can now post in this thread.")
            else:
                await ctx.send(f"{user.mention} is already whitelisted.")
    except discord.HTTPException as e:
        await ctx.channel.send(f"504 internal server error\n-# {e}")

@bot.event
async def on_message(message: discord.Message):
    if message.guild is None or message.author.bot:
        return

    db = load_db()
    guild_id = str(message.guild.id)

    # Check if in a Yapping City forum
    yapping_forums = db.get(guild_id, {}).get("yapping_forums", {})
    whitelists = db.get(guild_id, {}).get("whitelists", {})

    if isinstance(message.channel, discord.Thread) and str(message.channel.parent_id) in yapping_forums:
        thread = message.channel
        if message.author.id == thread.owner_id:
            return  # thread creator is allowed
        if str(thread.id) in whitelists and message.author.id in whitelists[str(thread.id)]:
            return  # whitelisted user is allowed

        try:
            # Download attachments first
            files = []
            if message.attachments:
                async with aiohttp.ClientSession() as session:
                    for attachment in message.attachments:
                        async with session.get(attachment.url) as resp:
                            if resp.status == 200:
                                data = await resp.read()
                                fp = io.BytesIO(data)
                                fp.seek(0)
                                files.append(discord.File(fp, filename=attachment.filename))

            await message.delete()

            # Build the embed
            embed = discord.Embed(color=discord.Color.from_str("#ff0000"))

            if message.content:
                embed.description = message.content[:4096]

            embed.set_author(name=f"{message.author}'s message was deleted", icon_url=message.author.display_avatar.url)
            embed.set_footer(text=f"#{message.channel.name}")

            thread_owner = await message.guild.fetch_member(thread.owner_id)
            await thread_owner.send(embed=embed, files=files, allowed_mentions=discord.AllowedMentions.none())
        except Exception as e:
            print(f"Error deleting message or sending DM: {e}")

bot.run("TOKEN")

