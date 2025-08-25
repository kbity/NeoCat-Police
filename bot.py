import discord, typing, json, enum, time, datetime, aiohttp, random, asyncio, re, syllables, traceback, io, os, sys

from translate import Translator
from nltk.corpus import cmudict
from langdetect import detect
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import has_permissions, MissingPermissions
from discord.ui import Button, View
from discord.utils import get
from typing import Literal
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
rainstreaks = {}
d = cmudict.dict()

enableAI = True
usernameCache = {}
catchesInChannels = {}
catchesInBirdChannels = {}
defaultdctimeout = 300

evaluser = 798072830595301406
kreisi_links = ["https://cdn.discordapp.com/attachments/1138892966782578738/1409079629209145405/image.png",
"https://cdn.discordapp.com/attachments/1138892966782578738/1409079727561637919/image.png",
"https://cdn.discordapp.com/attachments/1138892966782578738/1409079782884507658/image.png",
"https://cdn.discordapp.com/attachments/1138892966782578738/1409079847799623750/image.png",
"https://cdn.discordapp.com/attachments/1138892966782578738/1409079886466777210/image.png",]

# AI setup
reply_chain_cache = {}
ailoglength = {}
# AI Config
MAX_CHAIN_DEPTH = 10
ai_llm = "llama3.2"
ai_url = "http://192.168.254.82:11434/api/generate"
defaultprompt = "You are a Moderation bot for various discord servers. You are a clone of Cat Stand's \"Cat Police\" bot. You are NOT an \"AI-Powered\" or \"AI Chatbot\" or anything of the like. You're simply an Isolated AI Feature in an otherwise AI-less bot. Please Keep your responses short unless needed. Do not start your message with the bot's username, as it is not needed. Here is more info about the bot: `;{%!name!%};` is a clone of Lia Milenakos' 'Cat police' bot, specifically for Cat Stand. Both bots function very similarly. ;{%!name!%}; is made by Mari (mari2). Mari did NOT make 'Cat police', Lia Milenakos did. You are not a bot for Cat Stand, but for all servers. Your pronouns are She/Her."
  # ;{%!name!%}; is replaced by the default name
# AI setup end

default_join_emoji = "<:member_join:1394060667660533953>"
default_join_messages = [
    ["A wild ", " appeared."],
    ["Yay you made it, ", "!"],
    ["Welcome ", ". Say hi!"],
    ["Welcome, ", ". We hope you've brought pizza."],
    ["", " hopped into the server."],
    ["Good to see you, ", "."],
    ["", " just landed."],
    ["", " just slid into the server."],
    ["", " is here."],
    ["Glad you're here, ", "."],
    ["Everyone welcome ", "!"],
    ["", " just showed up!"],
    ["", " joined the party."]
]

console_log = print # DO YOU SPEAK JAVASCRIPT??
evil = eval

TICKET_BUTTON_PREFIX = "ticket_button_wow_yay:"

console_log("preparing...")

# make folders
os.makedirs("data", exist_ok=True)
os.makedirs("modlogs", exist_ok=True)

bot = commands.Bot(command_prefix='ncpol!', intents=intents, help_command=None)
tree = bot.tree

bot.session = None

# Load existing data from db.json
def load_db(guildId):
    try:
        with open(f"data/{guildId}.json", 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

# Save data to db.json
def save_db(guildId, data):
    with open(f"data/{guildId}.json", 'w') as f:
        json.dump(data, f, indent=4)

# Load existing data from ai_db.json
def load_ai_db():
    try:
        with open('ai_db.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

# Save data to ai_db.json
def save_ai_db(data):
    with open('ai_db.json', 'w') as f:
        json.dump(data, f, indent=4)

# Load existing data from modlogs/guildId.json
def load_logs(guildId):
    try:
        with open(f"modlogs/{guildId}.json", 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

# Save data to modlogs/guildId.json
def save_logs(guildId, data):
    with open(f"modlogs/{guildId}.json", 'w') as f:
        json.dump(data, f, indent=4)

# modlogs function
def modlog(guildId, memberIdi, issuerId, reason, punishment, until=0):
    memberId = str(memberIdi)
    logs = load_logs(guildId)
    timestamp = round(time.time())
    if memberId not in logs or not logs[memberId]:
        logs[memberId] = {}
    logs[memberId].setdefault("punishments", [])
    if punishment == "purge":
        logs[memberId]["punishments"].append([issuerId, reason, punishment, timestamp, until])
    else:
        logs[memberId]["punishments"].append([issuerId, reason, punishment, timestamp, (timestamp+until)])
    save_logs(guildId, logs)

def servermessages(guildId):
    global default_join_messages
    db = load_db(guildId)
    if not "welcome" in db:
        return default_join_messages
    welcome = db["welcome"]
    if not "messages" in welcome:
        return default_join_messages
    return welcome["messages"]

async def welcomeUser(guildId, userId):
    db = load_db(guildId)
    messages = servermessages(guildId)
    if not "welcome" in db:
        return
    welcome = db["welcome"]
    channelId = int(welcome["channel"])
    emoji = welcome["emoji"]
    msg = random.choice(messages)
    await welcmsg(userId, channelId, messages, emoji)

async def welcmsg(userId, channelId, messages, emoji):
    channel = await bot.fetch_channel(int(channelId))
    msg = random.choice(messages)
    await channel.send(f"{emoji} {msg[0]}<@{userId}>{msg[1]}")

class truefalse(str, enum.Enum):
    Yes = "yes"
    No = "no"

def convert_time_to_seconds(time_str):
    if len(time_str) == 0:
        return 0 # :thubm_what:

    if canintodigit(time_str):
        return int(time_str) # ok bro

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
        raise ValueError(f"Unsupported time unit: {time_unit}")

def canintodigit(val):
    return val.isdigit() or (val.startswith('-') and val[1:].isdigit())

async def query_ollama(prompt):
    url = ai_url
    data = {
        "model": ai_llm,
        "prompt": prompt,
        "stream": True
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data) as resp:
                if resp.status != 200:
                    return f"Error: {resp.status}, {await resp.text()}"
                full_response = ""
                async for line in resp.content:
                    if line:
                        try:
                            json_chunk = json.loads(line.decode())
                            full_response += json_chunk.get("response", "")
                            if json_chunk.get("done", False):
                                break
                        except json.JSONDecodeError:
                            pass
                return full_response
    except Exception as e:
        console_log(e)
        return "AI Unavailable"

class TicketButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Open a ticket", style=discord.ButtonStyle.primary, custom_id=f"{TICKET_BUTTON_PREFIX}ticket_button")
    async def persistent_button_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        thread = await interaction.channel.create_thread(name=f"{interaction.user.name}", type=discord.ChannelType.private_thread, invitable=False)
        await thread.send(f"{interaction.user.mention} Ticket Created! Please share your inquiry, a staff member will respond shortly.")
        db = load_db(str(interaction.guild.id))
        funny = ""
        if db.get("mod_ticket_pings"):
            for x in db["mod_ticket_pings"]:
                funny = funny + f"<@{x}> "
            await thread.send(funny)
        thread_url = f"https://discord.com/channels/{interaction.guild.id}/{thread.id}"
        await log_ticket(interaction.guild, f"New Ticket! {thread_url}")

@bot.event
async def on_ready():
    bot.add_view(TicketButton())
    console_log("Registered TicketButton.")

    bot.session = aiohttp.ClientSession()
    await bot.tree.sync()
    console_log("yiur bto is runnign :3")

    data_folder = "./data"

    for filename in os.listdir(data_folder):
        if not filename.endswith(".json"):
            continue

        guild_id = filename.removesuffix(".json")
        file_path = os.path.join(data_folder, filename)

        try:
            with open(file_path, "r") as f:
                guild_data = json.load(f)
        except Exception as e:
            console_log(f"Failed to load {filename}: {e}")
            continue

        slow_catching = guild_data.get("slow_catching", {})
        if not slow_catching:
            continue

        guild = bot.get_guild(int(guild_id))
        if not guild:
            continue

        for channel_id, enabled in slow_catching.items():
            if not enabled:
                continue

            channel = guild.get_channel(int(channel_id))
            if not channel:
                continue

            try:
                perms = channel.overwrites_for(guild.default_role)
                if perms.send_messages is False:
                    perms.send_messages = True
                    await channel.set_permissions(guild.default_role, overwrite=perms)
                    await channel.send("Bot restart, channel unlocked.")
                    console_log(f"Unlocked channel {channel.name} in guild {guild.name}")
            except Exception as e:
                console_log(f"Failed to unlock {channel_id} in {guild.name}: {e}")

    console_log("all slow catching channels unlocked")

@tree.command(name="ping", description="tests roundtrip latency")
async def ping(ctx: commands.Context):
    try:
        await ctx.response.send_message(f"<:neocat_police:1366561652870217759> Pong!! neocat brain has a latency of {round(bot.latency *1000)} ms")
    except Exception as e:
        await ctx.channel.send(f"504 internal server error\n-# {e}")

@tree.command(name="modlogs", description="socimar credit in mar developmente!!")
@discord.app_commands.default_permissions(view_audit_log=True)
async def modlogs(ctx: commands.Context, user: discord.User, amount: int = 10):
    memberId = str(user.id)
    logs = load_logs(str(ctx.guild.id))
    if memberId not in logs or not logs[memberId]:
        await ctx.response.send_message("no punishments found", ephemeral=True)
        return
    punishments = ""
    totalpunishments = len(logs[memberId]["punishments"])
    if amount > totalpunishments:
        amount = totalpunishments

    ordered_punishments = list(reversed(logs[memberId]["punishments"]))
    for x in range(0, amount):
        punishment = ordered_punishments[x]
        if punishment[2] == "mute":
            punishments = punishments + f"**{punishment[2]}**\nby <@{punishment[0]}>\nfor `{punishment[1]}`\nuntil <t:{punishment[4]}:f>\non <t:{punishment[3]}:f>\n"
        elif punishment[2] == "purge":
            if len(punishment) < 5:
                messages_fellback = "idk messages"
            else:
                messages_fellback = punishment[4]
            punishments = punishments + f"**{punishment[2]}**\nby <@{punishment[0]}>\nfor `{punishment[1]}`\n{messages_fellback}\non <t:{punishment[3]}:f>\n"
        else:
            punishments = punishments + f"**{punishment[2]}**\nby <@{punishment[0]}>\nfor `{punishment[1]}`\non <t:{punishment[3]}:f>\n"

    embed = discord.Embed(
        title=f"punishments of {user}",
        color=discord.Color.from_str("#757e8a"),
        description=punishments
    )
    embed.set_footer(text=f"showing the last {amount} of {totalpunishments}")
    try:
        await ctx.response.send_message(embed=embed, ephemeral=True)
    except Exception as e:
        await ctx.channel.send(f"504 internal server error\n-# {e}")

@tree.command(name="info", description="about this bot")
async def info(ctx: commands.Context):
    embed = discord.Embed(
        title="About NeoCat Police",
        description="`NeoCat Police` (formerly called ctqa ploice) is a clone of @milenakos' 'Cat police' bot, specifically for Cat Stand. Both bots function very similarly, but with some changes, such as NeoCat Police lacking Cat Bot statistics commands, not being hard coded for Cat Stand, and adding a few more features. NeoCat Police is inspired by tema5002's Cat Bot clone called `ctqa bto`, a clone of Cat Bot written in C# that is no longer online, hence the name \"ctqa ploice\"\n\nty morky for slight assistance.",
        color=discord.Color.blue()
    )
    embed.set_footer(text="NeoCat Police v1.3.0")
    try:
        await ctx.response.send_message(embed=embed)
    except Exception as e:
        await ctx.channel.send(f"504 internal server error\n-# {e}")

@tree.command(name="tip", description="unexpected tip")
async def info(ctx: commands.Context):
    tips = ["NeoCat Police was developed with the help of stella showing me the commands", "this bot is inspired by ctqa bto", "this bot allows for your server having its own yapping city", "ctqa bto has a planned C rewrite", "this bot is made of 50% ai slop", "i eat sand", "this bot has its own AI that is sometimes offline", "bird used to have moderation commands, but they sucked.", "unlike real cat police, NeoCat Police can be used in your own servers.", "this bot allows for an unlimited amount of starboards", "NeoCat Police is made in python using discord.py", "mari2 created NeoCat Police", "NeoCat Police has message logging", "yapping cities in NeoCat Police actually send the author messages to DMs, unlike yapper", "hungry bot+ is based on actual hungry bot code", "this bot caused catboard to shut down :sob:", "speaking about the previous tip, /leaderboard was pulled from catboard", "quine is a song made by kvellc from another timeline"]
    try:
        await ctx.response.send_message("<:tips:1365575538986450996> "+random.choice(tips))
    except Exception as e:
        await ctx.channel.send(f"504 internal server error\n-# {e}")

@tree.command(name="close", description="lock emoji 2 cooler edition")
@discord.app_commands.default_permissions(manage_threads=True)
@app_commands.describe(reason="sybau")
async def info(ctx: commands.Context, reason: str = "None"):
    try:
        if isinstance(ctx.channel, discord.Thread) and ctx.channel.is_private():
            if ctx.channel.owner_id == bot.user.id:
                res = f"🔒 Ticket closed by {ctx.user.mention} for `{reason}`."
                await ctx.response.send_message(res)
                await ctx.channel.edit(locked=True, archived=True)
            else:
                await ctx.response.send_message("BUGS WILL ATTACK🪰🪰🪰🪰🪰🪰🪰🪰🪰🪲🪲🪲🪰🪲🪰🪲🪰🪲🪰🪲🪰🪲🪰🪲🪰🐜‼️‼️‼ ️‼️THROW YOUR PHONE OUT THE WINDOW OR IT WILL EXPLODE‼️‼️‼️✅✅✅🈯️🈯️🔇🔇🔕 🔕🟩▫️©➖❗️🖇🔥🔥💥🔥💥🔥🔥💥🔥🔥💥💥BUGS WILL ATTACK🪰🪰🪰🪰🪰🪰🪰🪰🪰 🪲🪲🪲🪰🪲🪰🪲🪰🪲🪰🪲🪰🪲🪰🐜‼️‼️‼️‼️THROW OUT PUT YOUR PHONE OUT THE WINDOW OR IT WILL EXPLODE‼️‼️‼️✅✅✅")
        else:
            await ctx.response.send_message("BUGS WILL ATTACK🪰🪰🪰🪰🪰🪰🪰🪰🪰🪲🪲🪲🪰🪲🪰🪲🪰🪲🪰🪲🪰🪲🪰🪲🪰🐜‼️‼️‼ ️‼️THROW YOUR PHONE OUT THE WINDOW OR IT WILL EXPLODE‼️‼️‼️✅✅✅🈯️🈯️🔇🔇🔕 🔕🟩▫️©➖❗️🖇🔥🔥💥🔥💥🔥🔥💥🔥🔥💥💥BUGS WILL ATTACK🪰🪰🪰🪰🪰🪰🪰🪰🪰 🪲🪲🪲🪰🪲🪰🪲🪰🪲🪰🪲🪰🪲🪰🐜‼️‼️‼️‼️THROW OUT PUT YOUR PHONE OUT THE WINDOW OR IT WILL EXPLODE‼️‼️‼️✅✅✅")
    except Exception as e:
        await ctx.channel.send(f"504 internal server error\n-# {e}")

@tree.command(name="setticket", description="who's idea was this??")
@discord.app_commands.default_permissions(manage_guild=True)
@app_commands.describe(message="enter this or i will yap")
async def info(ctx: commands.Context, message: str = "sample text"):
    await ctx.response.defer(ephemeral=True) # prevents "application did not respond"
    try:
        if isinstance(ctx.channel, discord.TextChannel):
            embed = discord.Embed(
                title="Open a ticket",
                color=discord.Color.from_str("#757e8a"),
                description=message
            )
            await ctx.channel.send(embed=embed, view=TicketButton())
        else:
            await ctx.followup.send("dumbass <:pointlaugh:1392872064574033950>\ncant make a tickets channel unless its a channel with threads")
    except Exception as e:
        await ctx.channel.send(f"504 internal server error\n-# {e}")

@tree.command(name="ban", description="yeet but harder")
@discord.app_commands.default_permissions(ban_members=True)
@app_commands.describe(user="the nerd to yeet")
@app_commands.describe(reason="reason (e.g. memes in general)")
async def ban(ctx: commands.Context, user: discord.User, reason: str = "None", appeal: truefalse = "yes"):
    guild_id = str(ctx.guild.id)
    db = load_db(guild_id)
    mod_roles = db.get("mod_roles", {})
    mod_role = ctx.guild.get_role(int(mod_roles.get("mod"))) if mod_roles.get("mod") else None
    admin_role = ctx.guild.get_role(int(mod_roles.get("admin"))) if mod_roles.get("admin") else None
    out = ""
    if appeal != "yes":
        out = "out"
    async def get_appeal_message():
        appeal_info = db
        if appeal != "yes":
            return "you can't appeal this ban."
        server_id = appeal_info.get("appeal_server")
        if server_id:
            try:
                appeal_guild = bot.get_guild(int(server_id))
                if appeal_guild and appeal_guild.text_channels:
                    invite = await appeal_guild.text_channels[0].create_invite(max_age=3600, max_uses=1, unique=True, reason="ban appeal link")
                    return f"If you think this was unfair, you can appeal here: {invite.url}"
            except Exception as e:
                console_log(f"Failed to create appeal invite: {e}")
        return appeal_info.get("appeal_message", "you can't appeal this ban.")

    confirm_button = discord.ui.Button(label="Confirm", style=discord.ButtonStyle.secondary)

    async def confirm_button_callback(interaction: discord.Interaction):
        if interaction.user != ctx.user:
            await interaction.response.send_message("403 forbidden", ephemeral=True)
            return

        is_mod = (
            ctx.user.guild_permissions.ban_members
            or ctx.user.guild_permissions.administrator
            or (mod_role in ctx.user.roles if mod_role else False)
            or (admin_role in ctx.user.roles if admin_role else False)
        )

        if not is_mod:
            approval_view = discord.ui.View()
            approve_button = discord.ui.Button(label="Confirm", style=discord.ButtonStyle.secondary)

            async def approve_button_callback(approval_interaction: discord.Interaction):
                approver = approval_interaction.user
                approver_is_mod = (
                    approver.guild_permissions.ban_members
                    or approver.guild_permissions.administrator
                    or (mod_role in approver.roles if mod_role else False)
                    or (admin_role in approver.roles if admin_role else False)
                )

                if not approver_is_mod:
                    await approval_interaction.response.send_message("403 forbidden (you can't approve this)", ephemeral=True)
                    return

                try:
                    appeal_message = await get_appeal_message()
                    await user.send(f"hello nerd you might have been banned from {ctx.guild.name} for `{reason}`. {appeal_message}")
                except Exception as e:
                    console_log(f"Failed to send DM: {e}")

                await approval_interaction.guild.ban(user, reason=reason, delete_message_seconds=0)
                modlog(guild_id, str(user.id), ctx.user.id, reason, "ban")
                await log_action(ctx.guild, f"{user.mention} was permanently banned by {ctx.user.mention} for `{reason}` with{out} appeal. (confirmed by {approver.mention})")
                await approval_interaction.response.edit_message(
                    content=f"{user.mention} was banned by {ctx.user.mention} for `{reason}`. (confirmed by {approver.mention})",
                    view=None,
                    allowed_mentions=discord.AllowedMentions.none()
                )

            approve_button.callback = approve_button_callback
            approval_view.add_item(approve_button)

            await interaction.response.edit_message(
                content=f"<@{ctx.user.id}> is trying to ban <@{user.id}> for `{reason}`.\nThey need a confirmation from a higher-up staff member.",
                view=approval_view
            )
            return

        try:
            appeal_message = await get_appeal_message()
            await user.send(f"hello nerd you might have been banned from {ctx.guild.name} for `{reason}`. {appeal_message}")
        except Exception as e:
            console_log(f"Failed to send DM: {e}")

        await interaction.guild.ban(user, reason=reason, delete_message_seconds=0)
        modlog(guild_id, str(user.id), ctx.user.id, reason, "ban")
        await log_action(ctx.guild, f"{user.mention} was permanently banned by {ctx.user.mention} for `{reason}` with{out} appeal..")
        await interaction.response.edit_message(
            content=f"{user.mention} was permanently banned by {ctx.user.mention} for `{reason}`.",
            view=None,
            allowed_mentions=discord.AllowedMentions.none()
        )

    confirm_button.callback = confirm_button_callback

    view = discord.ui.View()
    view.add_item(confirm_button)

    try:
        await ctx.response.send_message(f"Banning {user.mention}?", view=view)
    except Exception as e:
        await ctx.channel.send(f"504 internal server error\n-# {e}")

# Error handler
@ban.error
async def ban_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.response.send_message("403 forbidden (you can't even ask for a ban)", ephemeral=True)
    else:
        raise error

@tree.command(name="appeals-configure", description="Link this server as the appeals server for another server.")
@discord.app_commands.default_permissions(administrator=True)
@commands.has_permissions(administrator=True)
@app_commands.describe(main_server_id="The ID of the server this one will handle appeals for.")
async def appeals_configure(ctx: commands.Context, main_server_id: str, remove: bool = False):
    try:
        await ctx.response.defer(ephemeral=False)
        appeals_id = str(ctx.guild.id)
        db = load_db(appeals_id) 

        try:
            main_server_id_int = int(main_server_id)
        except ValueError:
            await ctx.followup.send("invalid server id. right click the main server you want to link with developer mode enabled")
            return

        main_guild = bot.get_guild(main_server_id_int)
        if not main_guild:
            await ctx.followup.send("add the bot to the main server")
            return

        main_member = main_guild.get_member(ctx.user.id)
        if not main_member:
            await ctx.followup.send("lil bro isnt in that server :rofl:")
            return

        if not main_member.guild_permissions.administrator:
            await ctx.followup.send("You must have admin in **main server**, dumbass")
            return

        if not ctx.user.guild_permissions.administrator:
            await ctx.followup.send("You must also have admin in this (appeals) server.")
            return

        # get main server id
        main_id = str(main_server_id_int)
        db_main = load_db(main_id)
        if remove:
            db_main.pop("appeal_server", None)
            db.pop("main_server", None)
        else:
            db_main["appeal_server"] = appeals_id
            db["main_server"] = main_id

        save_db(main_id, db_main)
        save_db(appeals_id, db)
        if remove:
            res = f"{ctx.user.mention} unset appeals server for `{main_guild.name}`."
        else:
            res = f"{ctx.user.mention} set `{ctx.guild.name}` as the appeals server for `{main_guild.name}`."
        await log_action(main_guild, res)
        await ctx.followup.send(res)
    except Exception as e:
        await ctx.channel.send(f"504 internal server error\n-# {e}")

@tree.command(name="accept", description="Accept an appeal request and unban the user.")
@discord.app_commands.default_permissions(kick_members=True)
@app_commands.describe(user="The appealing user to accept")
@app_commands.describe(reason="Reason for accepting their appeal")
async def accept(ctx: commands.Context, user: discord.User, reason: str = "None"):
    await ctx.response.defer(ephemeral=False)
    appeal_guild_id = str(ctx.guild.id)
    db = load_db(appeal_guild_id)
    appeal_data = db
    main_server_id = appeal_data.get("main_server")

    if not main_server_id:
        await ctx.followup.send("Sorry, I don't speak that language. Can you please clarify or translate for me?")
        return

    main_guild = bot.get_guild(int(main_server_id))
    if not main_guild:
        await ctx.followup.send("Main server not found. Try not removing the bot next time!")
        return

    # Try to generate an invite link
    try:
        first_text_channel = next((c for c in main_guild.text_channels if c.permissions_for(main_guild.me).create_instant_invite), None)
        invite = await first_text_channel.create_invite(max_age=3600, max_uses=1, unique=True, reason="Appeal accepted")
        await user.send(
            f"hello your appeal in `{main_guild.name}` has been accepted!\n"
            f"reason: `{reason}`\n"
            f"join back using {invite.url}"
        )
    except Exception as e:
        await console_log(f"Failed to DM user: {e}")

    # Try to unban
    try:
        await main_guild.unban(user, reason=f"Appeal accepted: {reason}")
        modlog(main_server_id, str(user.id), ctx.user.id, reason, "accept")
    except discord.NotFound:
        await ctx.followup.send("User was not banned in the main server.")
    except Exception as e:
        await ctx.followup.send(f"Unban failed: {e}")
        return

    # Try to kick from appeals
    try:
        await ctx.guild.kick(user, reason="Appeal accepted and processed")
    except Exception as e:
        await ctx.followup.send(f"Kick failed: {e}")
        return

    # Send reply and log
    await log_action(main_guild, f"<@{user.id}>'s appeal was accepted by <@{ctx.user.id}> with the reason `{reason}`.")
    try:
        await ctx.followup.send(f"<@{user.id}>'s appeal was accepted by <@{ctx.user.id}> with the reason `{reason}`.")
    except Exception as e:
        await ctx.channel.send(f"504 internal server error\n-# {e}")

@tree.command(name="deny", description="Deny an appeal request and kick the user.")
@discord.app_commands.default_permissions(kick_members=True)
@app_commands.describe(user="The appealing user to deny")
@app_commands.describe(reason="Reason for denying their appeal")
async def deny(ctx: commands.Context, user: discord.User, reason: str = "None"):
    await ctx.response.defer(ephemeral=False)
    appeal_guild_id = str(ctx.guild.id)
    db = load_db(appeal_guild_id)
    appeal_data = db
    main_server_id = appeal_data.get("main_server")

    if not main_server_id:
        await ctx.followup.send("deny more like i deny you from using this command lmao gottem")
        return

    main_guild = bot.get_guild(int(main_server_id))
    if not main_guild:
        await ctx.followup.send("Main server not found. Try not removing the bot next time!")
        return

    # DM the user
    try:
        await user.send(
            f"hello your appeal in `{main_guild.name}` was denied tough shit bro\nreason: `{reason}`."
        )
    except Exception as e:
        await console_log(f"Failed to DM user: {e}")

    # Kick from appeals
    try:
        await ctx.guild.kick(user, reason="Appeal denied")
    except Exception as e:
        await ctx.followup.send(f"Kick failed: {e}")
        return

    # Reply and log
    modlog(main_server_id, str(user.id), ctx.user.id, reason, "deny")
    await log_action(main_guild, f"<@{user.id}>'s appeal was denied by <@{ctx.user.id}> with the reason `{reason}`.")
    try:
        await ctx.followup.send(f"<@{user.id}>'s appeal was denied by <@{ctx.user.id}> with the reason `{reason}`.")
    except Exception as e:
        await ctx.channel.send(f"504 internal server error\n-# {e}")

@bot.event
async def on_member_join(member: discord.Member):
    appeals_id = str(member.guild.id)
    db = load_db(appeals_id)

    # do welcome message if exist and on join
    if "welcome" in db:
        if db["welcome"]["mode"] == "OnJoin":
            await welcomeUser(appeals_id, member.id)

    # Check if this server is registered as an appeals server
    main_id = db.get("main_server")
    if not main_id:
        return
    main_db = load_db(main_id)

    main_guild = bot.get_guild(int(main_id))
    if not main_guild:
        return

    # Look for the action log channel in the main guild
    log_channel_id = main_db.get("action_log_channel")
    if not log_channel_id:
        return

    log_channel = main_guild.get_channel(int(log_channel_id))
    if not log_channel:
        return

    # Search the latest 50 log messages for a ban message mentioning this user
    async for message in log_channel.history(limit=50):
        if f"<@{str(member.id)}> was permanently banned by" in message.content:
            # Found a relevant log, send it to the first text channel in the appeals server
            first_text_channel = discord.utils.get(member.guild.text_channels, type=discord.ChannelType.text)
            if first_text_channel:
                try:
                    await first_text_channel.send(message.content)
                except Exception as e:
                    console_log(f"Failed to send appeal context in {member.guild.name}: {e}")
            break  # Stop after first relevant match

@tree.command(name="kick", description="yeet")
@discord.app_commands.default_permissions(kick_members=True)
@app_commands.describe(user="the nerd to yeet")
@app_commands.describe(reason="reason (e.g. memes in general)")
async def kick(ctx: commands.Context, user: discord.User, reason: str = "None"):
    # Define the button
    button = discord.ui.Button(label="Confirm", style=discord.ButtonStyle.secondary)

    # Define the callback function for the button
    async def button_callback(interaction: discord.Interaction):
        if interaction.user != ctx.user:
            await interaction.response.send_message("403 forbidden", ephemeral=True)
            return

        # Perform the kick and stuff
        try:
            await user.send(f"hello nerd you might have been kicked from {ctx.guild.name} for `{reason}`.")
        except Exception as e:
            console_log(f"Failed to send DM: {e}")

        await interaction.guild.kick(user, reason=reason)
        modlog(str(ctx.guild.id), str(user.id), ctx.user.id, reason, "kick")
        await log_action(ctx.guild, f"{user.mention} was kicked by {ctx.user} for `{reason}`.")
        await interaction.response.edit_message(content=f"{user.mention} was kicked by {interaction.user.mention} for `{reason}`.", view=None)

    # Assign the callback to the button
    button.callback = button_callback

    view = discord.ui.View()
    view.add_item(button)
    try:
        await ctx.response.send_message(f"Kicking {user.mention}?", view=view)
    except Exception as e:
        await ctx.channel.send(f"504 internal server error\n-# {e}")

@kick.error
async def kick_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.response.send_message("403 forbidden", ephemeral=True)

@tree.command(name="lock", description="lock emoji")
@discord.app_commands.default_permissions(manage_channels=True)
async def lock(ctx: commands.Context):
    perms = ctx.channel.overwrites_for(ctx.guild.default_role)
    perms.send_messages=False
    await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=perms)
    await log_action(ctx.guild, f"🔒 {ctx.channel.mention} has been locked by {ctx.user.mention}")
    try:
        await ctx.response.send_message(f"🔒 {ctx.channel.mention} has been locked by {ctx.user.mention}")
    except Exception as e:
        await ctx.channel.send(f"504 internal server error\n-# {e}")
@lock.error
async def kick_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.response.send_message("403 forbidden", ephemeral=True)

@tree.command(name="unlock", description="key emoji")
@discord.app_commands.default_permissions(manage_channels=True)
async def unlock(ctx: commands.Context):
    perms = ctx.channel.overwrites_for(ctx.guild.default_role)
    perms.send_messages=True
    await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=perms)
    await log_action(ctx.guild, f"🔓 {ctx.channel.mention} has been unlocked by {ctx.user.mention}")
    try:
        await ctx.response.send_message(f"🔓 {ctx.channel.mention} has been unlocked by {ctx.user.mention}")
    except Exception as e:
        await ctx.channel.send(f"504 internal server error\n-# {e}")
@unlock.error
async def kick_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.response.send_message("403 forbidden", ephemeral=True)

@tree.command(name="mute", description="hahah imagine being a mute")
@discord.app_commands.default_permissions(moderate_members=True)
@app_commands.describe(user="your free trial of talking has ended")
@app_commands.describe(lengh="lengh of no yap perms (e.g. 7d)")
@app_commands.describe(reason="i muted you becuz your annoying")
async def mute(ctx: commands.Context, user: discord.User, lengh: str, reason: str = "None"):
    guild_id = str(ctx.guild.id)
    db = load_db(guild_id)
    mod_roles = db.get("mod_roles", {})
    mod_role = ctx.guild.get_role(int(mod_roles.get("mod"))) if mod_roles.get("mod") else None
    minimod_role = ctx.guild.get_role(int(mod_roles.get("minimod"))) if mod_roles.get("minimod") else None
    admin_role = ctx.guild.get_role(int(mod_roles.get("admin"))) if mod_roles.get("admin") else None

    is_minimod = (
        ctx.user.guild_permissions.moderate_members
        or ctx.user.guild_permissions.administrator
        or (mod_role in ctx.user.roles if mod_role else False)
        or (admin_role in ctx.user.roles if admin_role else False)
        or (minimod_role in ctx.user.roles if minimod_role else False)
    )

    clock = convert_time_to_seconds(lengh)

    async def approve_button_callback(approval_interaction: discord.Interaction):
        approver = approval_interaction.user
        approver_is_minimod = (
            approver.guild_permissions.moderate_members
            or approver.guild_permissions.administrator
            or (mod_role in approver.roles if mod_role else False)
            or (admin_role in approver.roles if admin_role else False)
            or (minimod_role in approver.roles if minimod_role else False)
        )

        if not approver_is_minimod:
            await approval_interaction.response.send_message("403 forbidden (you can't approve this)", ephemeral=True)
            return

        try:
            await user.send(f"hello nerd you were muted in {ctx.guild.name} for `{reason}`. that shit will expire <t:{round(time.time()) + clock}:R>")
        except Exception as e:
            console_log(f"Failed to send DM: {e}")
        await user.timeout(datetime.timedelta(seconds=clock), reason=f"{reason}")
        modlog(str(ctx.guild.id), str(user.id), ctx.user.id, reason, "mute", until=clock)
        await log_action(ctx.guild, f"{user.mention} was muted until by {ctx.user.mention} for `{reason}`! This mute expires <t:{round(time.time()) + clock}:R> (confirmed by {approver.mention})")
        await approval_interaction.response.edit_message(
            content=f"{user.mention} was muted by {ctx.user.mention} for `{reason}`! This mute expires <t:{round(time.time()) + clock}:R> (confirmed by {approver.mention})",
            view=None,
            allowed_mentions=discord.AllowedMentions.none()
        )

    if is_minimod:
        try:
            await user.timeout(datetime.timedelta(seconds=clock), reason=f"{reason}")
            modlog(str(ctx.guild.id), str(user.id), ctx.user.id, reason, "mute", until=clock)
            await log_action(ctx.guild, f"{user.mention} was muted by {ctx.user.mention} for `{reason}`! This mute expires <t:{round(time.time()) + clock}:R>")
            await ctx.response.send_message(f"{user.mention} was muted by {ctx.user.mention} for `{reason}`! This mute expires <t:{round(time.time()) + clock}:R>")
        except Exception as e:
            await ctx.channel.send(f"504 internal server error\n-# {e}")
        try:
            await user.send(f"hello nerd you were muted in {ctx.guild.name} for `{reason}`. that shit will expire <t:{round(time.time()) + clock}:R>")
        except Exception as e:
            console_log(f"Failed to send DM: {e}")
    else:
        try:
            approval_view = discord.ui.View()
            approve_button = discord.ui.Button(label="Confirm", style=discord.ButtonStyle.secondary)
            approve_button.callback = approve_button_callback
            approval_view.add_item(approve_button)
            await ctx.response.send_message(f"{ctx.user.mention} is trying to mute {user.mention} for `{reason}`! This mute will expire <t:{round(time.time()) + clock}:R>\nThey need a confirmation from a higher-up staff member.", view=approval_view)
        except Exception as e:
            await ctx.channel.send(f"504 internal server error\n-# {e}")
@mute.error
async def kick_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.response.send_message("403 forbidden", ephemeral=True)

@tree.command(name="warn", description="uh oh")
@discord.app_commands.default_permissions(moderate_members=True)
@app_commands.describe(user="THIS IS A WARNING")
@app_commands.describe(reason="you did this?")
async def warn(ctx: commands.Context, user: discord.User, reason: str = "None"):
    memberId = str(user.id)
    logs = load_logs(str(ctx.guild.id))
    totalwarns = 1

    if memberId in logs and "punishments" in logs[memberId]:
        for punishment in logs[memberId]["punishments"]:
            if punishment[2] == "warn":
                totalwarns += 1
    try:
        modlog(str(ctx.guild.id), str(user.id), ctx.user.id, reason, "warn")
        await log_action(ctx.guild, f"{user.mention} was warned by {ctx.user.mention} for `{reason}`! (#{totalwarns})")
        await ctx.response.send_message(f"{user.mention} was warned by {ctx.user.mention} for `{reason}`! (#{totalwarns})")
    except Exception as e:
        await ctx.channel.send(f"504 internal server error\n-# {e}")
    try:
        await user.send(f"hello nerd you were warned in {ctx.guild.name} for `{reason}`\nrepeated offences might result in mutes or bans.")
    except Exception as e:
        console_log(f"Failed to send DM: {e}")
@warn.error
async def kick_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.response.send_message("403 forbidden", ephemeral=True)

@tree.command(name="nickname", description="change someone's identity (nickname)")
@discord.app_commands.default_permissions(manage_nicknames=True)
@app_commands.describe(user="who do you want to rename")
@app_commands.describe(new_nickname="their new embarrassing identity")
async def nickname(ctx: commands.Context, user: discord.Member, new_nickname: str = ""):
    old_nickname = user.nick if user.nick else "(no nickname)"
    try:
        await user.edit(nick=new_nickname)
        if new_nickname == "":
            await log_action(ctx.guild, f"{ctx.user.mention} reset {user.mention}'s nick from `{old_nickname}`.")
            await ctx.response.send_message(f"{ctx.user.mention} reset {user.mention}'s nick.")
        else:
            await log_action(ctx.guild, f"{ctx.user.mention} renamed {user.mention} from `{old_nickname}` to `{new_nickname}`.")
            await ctx.response.send_message(f"{ctx.user.mention} renamed {user.mention} to `{new_nickname}`.")
    except discord.Forbidden:
        await ctx.response.send_message("cant :skull:")
    except Exception as e:
        await ctx.channel.send(f"504 internal server error\n-# {e}")

@nickname.error
async def nickname_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.response.send_message("403 forbidden", ephemeral=True)

@tree.command(name="unmute", description="wtf i can talk")
@discord.app_commands.default_permissions(moderate_members=True)
@app_commands.describe(user="Mods, unmute this person")
@app_commands.describe(reason="why ummute tbh")
async def unmute(ctx: commands.Context, user: discord.User, reason: str = "None"):
    try:
        await ctx.response.send_message(f"{user.mention} was unmuted by {ctx.user.mention} for `{reason}`.")
        modlog(str(ctx.guild.id), str(user.id), ctx.user.id, reason, "unmute")
        await log_action(ctx.guild, f"{user.mention} was unmuted by {ctx.user.mention} for `{reason}`!")
        await user.timeout(None, reason=f"{reason}")
    except Exception as e:
        await ctx.channel.send(f"504 internal server error\n-# {e}")
    try:
        await user.send(f"hello nerd you were unmuted in {ctx.guild.name} for `{reason}`.")
    except Exception as e:
        console_log(f"Failed to send DM: {e}")
@unmute.error
async def kick_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.response.send_message("403 forbidden", ephemeral=True)

@tree.command(name="unban", description="unyeet??")
@discord.app_commands.default_permissions(ban_members=True)
@app_commands.describe(user="the nerd to... unyeet")
@app_commands.describe(reason="why was the user unyeet")
async def unban(ctx: commands.Context, user: discord.User, reason: str = "None"):
    try:
        await ctx.guild.unban(user, reason=reason)
        modlog(str(ctx.guild.id), str(user.id), ctx.user.id, reason, "unban")
        await log_action(ctx.guild, f"{user.mention} was unbanned by {ctx.user.mention} for `{reason}`!!!")
        await ctx.response.send_message(content=f"{user.mention} was unbanned by {ctx.user.mention} for `{reason}`!!!")
    except Exception as e:
        await ctx.channel.send(f"504 internal server error\n-# {e}")
    try:
        await user.send(f"hello nerd you were unbanned in {ctx.guild.name} for `{reason}`!!!")
    except Exception as e:
        console_log(f"couldn't DM user.'\n {e}")

@ban.error
async def ban_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.response.send_message("403 forbidden", ephemeral=True)

@tree.command(name="purge", description="timetravel moment")
@discord.app_commands.default_permissions(manage_messages=True)
@app_commands.describe(purge="how many messages do we remove (caps at 1000)")
@app_commands.describe(user="member to purge")
async def purge(ctx, purge: int, user: discord.User = None, reason: str = "None"):
    if purge < 0:
        await ctx.response.send_message(random.choice(kreisi_links))
        return

    await ctx.response.send_message("Purging...")

    if purge > 1000:
        purge = 1000

    if not user is None:
        msg = []

        async for m in ctx.channel.history():
            if len(msg) == purge:
                break
            if m.author == user:
                msg.append(m)
        try:
            await ctx.channel.delete_messages(msg)
            modlog(str(ctx.guild.id), str(user.id), str(ctx.user.id), reason, "purge", f"{purge} messages")
            res = f"Last {purge} messages from {user.mention} in {ctx.channel.mention} were purged by {ctx.user.mention} for `{reason}`."
            await log_action(ctx.guild, res)
            await ctx.channel.send(res)
        except Exception as e:
            await ctx.channel.send(f"504 internal server error\n-# {e}")
    else:
        realpurge = purge + 1
        try:
            await ctx.channel.purge(limit=realpurge)
            res = f"Last {purge} messages in {ctx.channel.mention} were purged by {ctx.user.mention} for `{reason}`."
            await log_action(ctx.guild, res)
            await ctx.channel.send(res)
        except Exception as e:
            await ctx.channel.send(f"504 internal server error\n-# {e}")

@tree.command(name="slowmode", description="change the speed of the chat")
@discord.app_commands.default_permissions(manage_channels=True)
@app_commands.describe(slowmode="slowmode time. max is 6 hours you goob, please specifiy unit")
async def slowmode(ctx: commands.Context, slowmode: str):
    await ctx.response.defer(ephemeral=False)
    try:
        delay = convert_time_to_seconds(slowmode)
    except Exception:
        await ctx.followup.send("https://tenor.com/view/%D8%B3%D8%A4%D8%A7%D9%84-%D8%B3%D8%A4%D8%A7%D9%84-%D9%88%D8%AC%D9%88%D8%A7%D8%A8-%D8%AA%D8%B1%D9%8A%D9%86%D8%AF%D9%8A%D9%86%D8%BA-gif-12622060486477759187")
        return

    if delay < 0:
        await ctx.followup.send("https://www.youtube.com/watch?v=r4mWRkFgJ3k")
        return

    if delay > 21600:
        delay = 21600
    try:
        await ctx.channel.edit(slowmode_delay=delay)
        await log_action(ctx.guild, f"{delay}s slowmode in {ctx.channel.mention} set by {ctx.user.mention}.")
        await ctx.followup.send(f":zzz: Now going at {delay}s slowmode!")
    except Exception as e:
        await ctx.channel.send(f"504 internal server error\n-# {e}")
@slowmode.error
async def ban_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.followup.send("403 forbidden", ephemeral=True)

class logtypes(str, enum.Enum):
    Message = "message"
    Action = "action"
    Spammy = "spammy"
    Reaction = "reaction"
    Tickets = "tickets"

@tree.command(name="log", description="set up logging")
@commands.has_permissions(manage_guild=True)
@discord.app_commands.default_permissions(manage_guild=True)
@app_commands.describe(type="what type of logs to set (message/action/spammy/reaction/tickets)")
@app_commands.describe(channel="where the logs go")
@app_commands.describe(channel="remove?")
async def log(ctx: commands.Context, type: logtypes, channel: discord.TextChannel, remove: truefalse = "no"):
    server_id = str(ctx.guild.id)
    db = load_db(server_id)

    if remove == "yes":
        if type.lower() == "message":
            db.pop("message_log_channel", None)
            await ctx.response.send_message(f"message logs will go nowhere")
        elif type.lower() == "action":
            db.pop("action_log_channel", None)
            await ctx.response.send_message(f"action logs will go nowhere")
        elif type.lower() == "spammy":
            db.pop("spammy_log_channel", None)
            await ctx.response.send_message(f"spammy logs will go nowhere")
        elif type.lower() == "reaction":
            db.pop("reaction_log_channel", None)
            await ctx.response.send_message(f"reaction logs will go nowhere")
        elif type.lower() == "tickets":
            db.pop("ticket_log_channel", None)
            await ctx.response.send_message(f"tickets will go nowhere")
        else:
            await ctx.response.send_message("Invalid type! Choose either `message`, `action`, `spammy`, `reaction`, or `tickets`.")
    else:
        if type.lower() == "message":
            db["message_log_channel"] = channel.id
            await ctx.response.send_message(f"message logs will go to {channel.mention}")
        elif type.lower() == "action":
            db["action_log_channel"] = channel.id
            await ctx.response.send_message(f"action logs will go to {channel.mention}")
        elif type.lower() == "spammy":
            db["spammy_log_channel"] = channel.id
            await ctx.response.send_message(f"spammy logs will go to {channel.mention}")
        elif type.lower() == "reaction":
            db["reaction_log_channel"] = channel.id
            await ctx.response.send_message(f"reaction logs will go to {channel.mention}")
        elif type.lower() == "tickets":
            db["ticket_log_channel"] = channel.id
            await ctx.response.send_message(f"tickets will go to {channel.mention}")
        else:
            await ctx.response.send_message("Invalid type! Choose either `message`, `action`, `spammy`, `reaction`, or `tickets`.")

    save_db(server_id, db)

async def log_action(guild: discord.Guild, content: str):
    guild_id = str(guild.id)
    db = load_db(guild_id)
    channel_id = db.get("action_log_channel")
    if channel_id:
        channel = guild.get_channel(channel_id)
        if channel:
            await channel.send(content, allowed_mentions=discord.AllowedMentions.none())
async def log_spammy(guild: discord.Guild, content: str):
    guild_id = str(guild.id)
    db = load_db(guild_id)
    channel_id = db.get("spammy_log_channel")
    if channel_id is None:
        channel_id = db.get("action_log_channel")
    if channel_id:
        channel = guild.get_channel(channel_id)
        if channel:
            await channel.send(content, allowed_mentions=discord.AllowedMentions.none())
async def log_ticket(guild: discord.Guild, content: str):
    guild_id = str(guild.id)
    db = load_db(guild_id)
    channel_id = db.get("ticket_log_channel")
    if channel_id:
        channel = guild.get_channel(channel_id)
        if channel:
            await channel.send(content, allowed_mentions=discord.AllowedMentions.none())

@tree.command(name="configure", description="you dont learn this in UX this bad in class")
@commands.has_permissions(manage_guild=True)
@discord.app_commands.default_permissions(manage_guild=True)
@app_commands.describe(proporty="select the db property you wish to change")
@app_commands.describe(bowleen="true or false")
@app_commands.describe(stirng="WORDS!!")
@app_commands.describe(integir="m a t h")
async def configure(ctx: commands.Context, proporty: Literal["disableFreakouts", "disableAI", "CustomCatchMessages", "ReverseSlice", "DCTimeout", "DCTimeout_Bird", "DCRuleNumber", "CustomUsernameSlice", "appeal_message", "CatchKeyword"], bowleen: bool = True, stirng: str = "Default", integir: int = 0):
    try:
        await ctx.response.defer(ephemeral=False)
        boolprops = ["disableFreakouts", "disableAI", "CustomCatchMessages", "ReverseSlice"]
        strprops = ["appeal_message", "CatchKeyword"]
        intprops = ["DCTimeout", "DCTimeout_Bird", "DCRuleNumber", "CustomUsernameSlice"]

        guild_id = str(ctx.guild.id)
        db = load_db(guild_id)

        if proporty in boolprops:
            val = bowleen
        elif proporty in strprops:
            val = stirng
        elif proporty in intprops:
            val = integir
        else:
            await ctx.followup.send(f"wtf")
            return

        db[proporty] = val

        save_db(guild_id, db)

        await log_action(ctx.guild, f"`{proporty}` set to `{val}` by {ctx.user.mention}")
        await ctx.followup.send(f"`{proporty}` set to `{val}`")
    except Exception as e:
        await ctx.channel.send(f"504 internal server error\n-# {e}")

@bot.event
async def on_message_delete(message: discord.Message):
    if message.guild is None or message.author.bot:
        return

    channel = message.channel

    guild_id = str(message.guild.id)
    db = load_db(guild_id)
    if isinstance(channel, discord.Thread):
        channel_id = db.get("spammy_log_channel")
        if channel_id is None:
            channel_id = db.get("message_log_channel")
    else:
        channel_id = db.get("message_log_channel")

    if channel_id:
        channel = message.guild.get_channel(channel_id)
        if channel:
            embed = discord.Embed(color=discord.Color.from_str("#ff0000"))

            embed.description = ""

            if message.content:
                embed.description = message.content[:4096]

            if message.reference:
                embed.add_field(name="Reply to", value=message.reference.jump_url)

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
                            console_log(f"Failed to download attachment: {attachment.url} — {e}")
            hblock = ""
            mewhenthemoddeletesmymessage = await anext(message.guild.audit_logs(action=discord.AuditLogAction.message_delete, limit=1))
            if mewhenthemoddeletesmymessage.target.id == message.author.id and mewhenthemoddeletesmymessage.extra.channel.id == message.channel.id:
                hblock = f" by {mewhenthemoddeletesmymessage.user}"

            embed.set_author(name=f"{message.author}'s message was deleted{hblock}", icon_url=message.author.display_avatar.url)
            embed.set_footer(text=f"#{message.channel.name}")

            await channel.send(embed=embed, files=files, allowed_mentions=discord.AllowedMentions.none())

@bot.event
async def on_message_edit(before: discord.Message, after: discord.Message):
    if before.guild is None or before.author.bot or before.content == after.content:
        return

    guild_id = str(before.guild.id)
    db = load_db(guild_id)
    channel_id = db.get("message_log_channel")

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
@app_commands.describe(enable_leaderboard="enable /leaderboard (only works for starboard 1)")
async def setstarboard(
    interaction: discord.Interaction,
    channel: discord.TextChannel,
    emoji: str = "⭐",
    threshold: int = 3,
    starboard_id: int = 1,
    enable_leaderboard: truefalse = "no"
):
    await interaction.response.defer(ephemeral=False)

    server_id = str(interaction.guild.id)
    db = load_db(server_id)

    suffix = "" if starboard_id == 1 else f"_{starboard_id}"

    lb = ""
    db.setdefault("leaderboardEnabled", "False")

    changed_emoji = True
    if 'starboard_emoji' in db and db['starboard_emoji'] == emoji:
        changed_emoji = False
    if changed_emoji == True and starboard_id == 1:
        db["leaderboard"] = {}

    if enable_leaderboard == "yes" and db["leaderboardEnabled"] == "False":
        db["leaderboardEnabled"] = "True"
        lb = " (leaderboard enabled for starboard 1 btw)"

    if enable_leaderboard == "no" and db["leaderboardEnabled"] == "True":
        db["leaderboardEnabled"] = "False"
        lb = " (leaderboard disabled for starboard 1 btw)"

    if threshold <= 0:
        # Remove this starboard config
        for key in ["channel_id", "emoji", "threshold", "webhook_url"]:
            db.pop(f"starboard_{key}{suffix}", None)
        save_db(server_id, db)
        await interaction.followup.send(f"❌ Removed starboard {starboard_id}{lb}")
        return

    # Set this starboard config
    db[f"starboard_channel_id{suffix}"] = channel.id
    db[f"starboard_emoji{suffix}"] = emoji
    db[f"starboard_threshold{suffix}"] = threshold
    save_db(server_id, db)

    await interaction.followup.send(
        f"⭐ Starboard {starboard_id} set to {channel.mention} with emoji {emoji} and threshold {threshold}{lb}."
    )

@tree.command(name="leaderboard", description="who has the most boarded stars")
async def leaderboard(ctx: commands.Context):
    amount = 10
    db = load_db(str(ctx.guild.id))
    if "leaderboard" not in db or not db["leaderboard"]:
        await ctx.response.send_message("no leaderboard <:bowomp:1397417015047618621>", ephemeral=True)
        return

    sortedlb = dict(sorted(db["leaderboard"].items(), key=lambda item: item[1], reverse=True))

    leaderboard = ""
    counter = 0
    for member in sortedlb:
        counter += 1
        if counter > 10:
            break
        leaderboard = leaderboard + f"{counter}. <@{member}>: {db['leaderboard'][member]} {db['starboard_emoji']}\n"

    embed = discord.Embed(
        title=f"Top 10 {db['starboard_emoji']}s:",
        color=discord.Color.blue(),
        description=leaderboard
    )
    try:
        await ctx.response.send_message(embed=embed)
    except Exception as e:
        await ctx.channel.send(f"504 internal server error\n-# {e}")

def get_unicode_emoji_url(emoji: str) -> str:
    codepoints = '-'.join(f"{ord(c):x}" for c in emoji)
    return f"https://twemoji.maxcdn.com/v/latest/72x72/{codepoints}.png"

@bot.event
async def on_raw_reaction_remove(payload):
    server_id = str(payload.guild_id)
    db = load_db(server_id)
    guild = bot.get_guild(payload.guild_id)
    user = guild.get_member(payload.user_id)

    if "reactroles" in db:
        if str(payload.message_id) in db["reactroles"]:
            if str(payload.emoji) in db["reactroles"][str(payload.message_id)]:
                mewhenthe_role = guild.get_role(int(db["reactroles"][str(payload.message_id)][str(payload.emoji)]))
                verifyroleFile = db.get("verified_role", None)
                if verifyroleFile is not None:
                    if int(verifyroleFile) == int(db["reactroles"][str(payload.message_id)][str(payload.emoji)]):
                        return
                try:
                    await user.remove_roles(mewhenthe_role, reason="EVIL react role :staring_dog:")
                except Exception as e:
                    console_log(f"failed to remove react role, {e}")

    if payload.user_id == bot.user.id:
        db = load_db(payload.guild_id)
        if not any(str(payload.emoji) == str(emoji) for key, emoji in db.items() if key.startswith("starboard_emoji")):
            return
        guild = bot.get_guild(payload.guild_id)
        channel = guild.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        await message.add_reaction(payload.emoji)
        
# check if reaction removed is by ncpol, then re-react payload.emoji

@bot.event
async def on_raw_reaction_add(payload):
    guild_id = str(payload.guild_id)
    db = load_db(guild_id)
    guild = bot.get_guild(payload.guild_id)

    # Try default starboard and numbered starboards
    starboard_ids = [1] + [int(k.split("_")[-1]) for k in db if k.startswith("starboard_channel_id_")]
    starboard_ids = list(set(starboard_ids))  # Avoid duplicates

    logging_channel_id = db.get("reaction_log_channel")
    if logging_channel_id:
        log_channel = guild.get_channel(logging_channel_id)


    user = guild.get_member(payload.user_id)
    unicodeblcok = ""
    isunicode = 0
    shouldlogunicode = 0
    if not payload.emoji.id:
        unicodeblcok = f"{payload.emoji}\n"
        isunicode = 1

    if not guild:
        return

    channel = guild.get_channel(payload.channel_id)
    if channel is None:
        try:
            channel = await bot.fetch_channel(payload.channel_id)
        except discord.NotFound:
            console_log(f"Channel {payload.channel_id} not found.")
            return
        except discord.Forbidden:
            console_log(f"Missing permissions to fetch channel {payload.channel_id}.")
            return
        except discord.HTTPException as e:
            console_log(f"HTTP error while fetching channel: {e}")
            return
    message = await channel.fetch_message(payload.message_id)
    serveremojis = guild.emojis
    testset = [
    "🅰️", "🅱️", "🆎", "🆑",
    "🇦", "🇧", "🇨", "🇩", "🇪", "🇫", "🇬", "🇭", "🇮",
    "🇯", "🇰", "🇱", "🇲", "🇳", "🇴", "🇵", "🇶", "🇷",
    "🇸", "🇹", "🇺", "🇻", "🇼", "🇽", "🇾", "🇿",
    "🍆", "🍑", "💦", "🍌", "🥒", "👅", "👄", "💋", "🥵", "😩", "🤤"
    ]

    if str(payload.emoji) in testset:
        shouldlogunicode = 1

    dothelog = not payload.emoji in serveremojis and not isunicode or shouldlogunicode

    if user is None:
        return

    if not user.bot and logging_channel_id and dothelog:
        reaction = next((r for r in message.reactions if str(r.emoji) == str(payload.emoji)),None)
        if reaction.count == 1:
            embed = discord.Embed(
                title="Reaction Added",
                description=f"by <@{payload.user_id}>\n{unicodeblcok}[Jump](https://discord.com/channels/{payload.guild_id}/{payload.channel_id}/{payload.message_id})",
                color=discord.Color.from_str("#757e8a")
            )
            embed.set_thumbnail(url=f"{payload.emoji.url}")
            await log_channel.send(embed=embed)

    if "reactroles" in db:
        if str(payload.message_id) in db["reactroles"]:
            if str(payload.emoji) in db["reactroles"][str(payload.message_id)]:
                mewhenthe_role = guild.get_role(int(db["reactroles"][str(payload.message_id)][str(payload.emoji)]))
                nothadrolebefore = mewhenthe_role not in user.roles
                try:
                    await user.add_roles(mewhenthe_role, reason="react role :staring_cat:")
                except Exception as e:
                    console_log(f"failed to add react role, {e}")
                    return
                verifyroleFile = db.get("verified_role", None)
                try:
                    verifyrole = guild.get_role(int(verifyroleFile))
                except Exception:
                    verifyrole = None
                if nothadrolebefore:
                    if verifyrole and int(db["reactroles"][str(payload.message_id)][str(payload.emoji)]) == int(verifyroleFile):
                        dm_message = f"Verification Successful!\nWelcome to {guild.name}!"
                        try:
                            await user.send(dm_message)
                        except Exception as e:
                            console_log(f"failed to DM, {e}")
                        if "welcome" in db:
                            if db["welcome"]["mode"] == "OnVerify":
                                await welcomeUser(guild_id, user.id)


    for starboard_id in starboard_ids:
        suffix = "" if starboard_id == 1 else f"_{starboard_id}"
        emoji = db.get(f"starboard_emoji{suffix}")
        threshold = db.get(f"starboard_threshold{suffix}", 3)
        channel_id = db.get(f"starboard_channel_id{suffix}")
        webhook_id = db.get(f"starboard_webhook_id{suffix}")

        if not emoji or not channel_id:
            continue

        if channel is None:
            try:
                channel = await bot.fetch_channel(payload.channel_id)
            except discord.NotFound:
                console_log(f"Channel {payload.channel_id} not found.")
                continue
            except discord.Forbidden:
                console_log(f"Missing permissions to fetch channel {payload.channel_id}.")
                continue
            except discord.HTTPException as e:
                console_log(f"HTTP error while fetching channel: {e}")
                continue

        if payload.emoji.name != emoji and str(payload.emoji) != emoji:
            continue

        for reaction in message.reactions:
            if (reaction.emoji == payload.emoji.name or str(reaction.emoji) == emoji) and reaction.count >= threshold:
                async for user in reaction.users():
                    if user.id == bot.user.id:
                        return

                try:
                    await message.add_reaction(emoji)
                except discord.HTTPException:
                    pass

                starboard_channel = guild.get_channel(channel_id)
                if not starboard_channel:
                    return

                webhook = None

                # Try to get the existing webhook
                if webhook_id:
                    try:
                        webhooks = await starboard_channel.webhooks()
                        webhook = discord.utils.get(webhooks, id=webhook_id)
                    except (discord.NotFound, discord.Forbidden):
                        webhook = None

                if webhook is None:
                    # Webhook is missing or invalid; create a new one
                    async with aiohttp.ClientSession() as session:
                        async with session.get("https://i.imgur.com/yHPNPoQ.png") as resp:
                            avatar_bytes = await resp.read() if resp.status == 200 else None

                    webhook_obj = await starboard_channel.create_webhook(
                        name="ctqa ploice webhook",
                        avatar=avatar_bytes
                    )
                    webhook_id = webhook_obj.id
                    db[f"starboard_webhook_id{suffix}"] = webhook_id
                    save_db(guild_id, db)
                    webhook = webhook_obj

                db.setdefault("leaderboardEnabled", "False")
                if starboard_id == 1 and db["leaderboardEnabled"] == "True":
                    db.setdefault("leaderboard", {})
                    if str(message.author.id) not in db["leaderboard"] or not db["leaderboard"][str(message.author.id)]:
                        db["leaderboard"][str(message.author.id)] = 0
                    db["leaderboard"].setdefault(str(message.author.id), 0)
                    db["leaderboard"][str(message.author.id)] += 1
                    save_db(payload.guild_id, db)

                author_name = f"{message.author.display_name}"
                author_name = author_name[:80] if len(author_name) > 80 else author_name
                avatar_url = message.author.display_avatar.url if message.author.display_avatar else None
                messageIsLink = message.content.lower().endswith('.png') or message.content.lower().endswith('.jpg') or message.content.lower().endswith('.jpeg') or message.content.lower().endswith('.gif') or message.content.lower().endswith('.webp') or message.content.lower().endswith('.gifv')
                if "tenor.com" in message.content.lower() or messageIsLink or "media.discordapp.net" in message.content.lower():
                    embeds = []
                else:
                    embeds = message.embeds

                # Jump button
                jump_url = message.jump_url
                view = View()
                view.add_item(Button(label=f"Jump to #{channel.name}", url=jump_url))

                files = [await attachment.to_file() for attachment in message.attachments]
                content_trimmed = message.content[:2000]

                try:
                    await webhook.send(
                        content=content_trimmed or None,
                        username=author_name,
                        avatar_url=avatar_url,
                        view=view,
                        files=files,
                        wait=True,
                        allowed_mentions=discord.AllowedMentions.none(),
                        embeds=embeds
                    )
                    await message.add_reaction(emoji)
                except Exception:
                    await message.remove_reaction(emoji)

@tree.command(name="yapping-city", description="Add or remove a forum as a Yapping City forum")
@commands.has_permissions(manage_guild=True)
@discord.app_commands.default_permissions(manage_guild=True)
@app_commands.describe(action="Whether to add or remove the forum", forum="The forum channel to modify")
async def yapping_city(ctx: commands.Context, action: Literal["add", "remove"], forum: discord.ForumChannel):
    guild_id = str(ctx.guild.id)
    db = load_db(guild_id)
    forum_id = str(forum.id)

    db.setdefault("yapping_forums", {})

    if action == "add":
        db["yapping_forums"][forum_id] = True
        await ctx.response.send_message(f"{ctx.user.mention} set {forum.mention} as a Yapping City forum.", ephemeral=False)
        await log_action(ctx.guild, f"{ctx.user.mention} set {forum.mention} as a Yapping City forum.")
    elif action == "remove":
        if forum_id in db["yapping_forums"]:
            del db["yapping_forums"][forum_id]
            await ctx.response.send_message(f"{ctx.user.mention} unset {forum.mention} as a Yapping City forum.", ephemeral=False)
            await log_action(ctx.guild, f"{ctx.user.mention} unset {forum.mention} as a Yapping City forum.")
        else:
            await ctx.response.send_message(f"{forum.mention} is not marked as a Yapping City forum, idiot.", ephemeral=False)

    save_db(guild_id, db)

@tree.command(name="whitelist", description="Allow or remove someone from talking in your Yapping City post")
@app_commands.describe(user="The user to whitelist or remove", remove="Unwhitelist the user instead")
async def whitelist(ctx: commands.Context, user: discord.User, remove: bool = False):
    if not isinstance(ctx.channel, discord.Thread):
        return await ctx.response.send_message("You can only run this inside a thread.")

    thread = ctx.channel
    if ctx.user.id != thread.owner_id:
        return await ctx.response.send_message("Only the thread owner can manage the whitelist.")

    guild_id = str(ctx.guild.id)
    db = load_db(guild_id)
    thread_id = str(thread.id)

    db.setdefault("whitelists", {}).setdefault(thread_id, [])
    whitelist = db["whitelists"][thread_id]

    try:
        if remove:
            if user.id in whitelist:
                whitelist.remove(user.id)
                save_db(guild_id, db)
                await ctx.response.send_message(f"{user.mention} has been removed from the whitelist.")
            else:
                await ctx.response.send_message(f"{user.mention} is not on the whitelist.")
        else:
            if user.id not in whitelist:
                whitelist.append(user.id)
                save_db(guild_id, db)
                await ctx.response.send_message(f"{user.mention} can now post in this thread.")
            else:
                await ctx.response.send_message(f"{user.mention} is already whitelisted.")
    except discord.HTTPException as e:
        await ctx.channel.send(f"504 internal server error\n-# {e}")

@tree.command(name="setroletype", description="Set a role as a type of role (mod, underage, etc) for the bot")
@discord.app_commands.default_permissions(manage_guild=True)
@app_commands.describe(role_type="What kind of role", role="The role to set")
async def setmodrole(ctx: commands.Context, role_type: Literal["admin", "mod", "minimod", "trial_mod", "functional_mod", "underage_role", "verified_role"], role: discord.Role, remove: truefalse = "no"):
    guild_id = str(ctx.guild.id)
    db = load_db(guild_id)

    notmodrole = role_type == "underage_role" or role_type == "verified_role"

    if remove == "yes":
        if not notmodrole:
            db.setdefault("mod_roles", {})
            db["mod_roles"].pop(role_type, None)
        else:
            db.setdefault(role_type == "null")
            db.pop(role_type, None)
        whatdidido = f"{ctx.user.mention} unset the `{role_type}` role."
    else:
        if not notmodrole:
            db.setdefault("mod_roles", {})
            db["mod_roles"][role_type] = str(role.id)
        else:
            db.setdefault(role_type == "null")
            db[role_type] = str(role.id)
        whatdidido = f"{ctx.user.mention} set {role.mention} as the `{role_type}` role."

    save_db(guild_id, db)

    await log_action(ctx.guild, whatdidido)
    await ctx.response.send_message(whatdidido, ephemeral=False)

@tree.command(name="setchanneltype", description="Set a channel as a type of role (slow catching, dementia, etc) for the bot")
@discord.app_commands.default_permissions(manage_guild=True)
@app_commands.describe(channel_type="What kind of role", channel="The channel to set")
async def setchanneltype(ctx: commands.Context, channel_type: Literal["catching", "catching-birds", "haikus-allowed", "slow_catching", "dementia_chats", "the_ncpol_press"], channel: discord.TextChannel, remove: truefalse = "no"):
    try:
        await ctx.response.defer(ephemeral=False)
    except Exception as e:
        await ctx.channel.send(f"504 internal server error\n-# {e}")
    guild_id = str(ctx.guild.id)
    db = load_db(guild_id)
    channel_id = str(channel.id)
    db.setdefault(channel_type, {})

    if remove == "no":
        whatdidido = f"{ctx.user.mention} set {channel.mention} as a `{channel_type}` channel."
        if channel_type == "the_ncpol_press":
            db[channel_type] = channel.id
        else:
            db[channel_type][channel_id] = True
    else:
        whatdidido = f"{ctx.user.mention} unset {channel.mention} as a `{channel_type}` channel."
        if channel_type == "the_ncpol_press":
            try:
                del db[channel_type]
            except:
                await ctx.followup.send(f"{channel.mention} is not marked as a `{channel_type}` channel, or there was an error.")
                return
        else:
            if channel_id in db[channel_type]:
                del db[channel_type][channel_id]
            else:
                await ctx.followup.send(f"{channel.mention} is not marked as a `{channel_type}` channel, idiot.")
                return

    save_db(guild_id, db)

    await log_action(ctx.guild, whatdidido)
    await ctx.followup.send(whatdidido)

@tree.command(name="reactroles", description=":insane:")
@discord.app_commands.default_permissions(manage_guild=True)
@app_commands.describe(message_id="ID of message (or link maybe)", role="role", emoji=":emoji_13:")
async def setmodrole(ctx: commands.Context, message_id: str, emoji: str, role: discord.Role, remove: truefalse = "no"):
    await ctx.response.defer(ephemeral=False)
    guild_id = str(ctx.guild.id)
    db = load_db(guild_id)
    db.setdefault("reactroles", {})

    if "discord.com" in message_id:
        messageId = message_id.rsplit("/", 1)[-1]
    else:
        messageId = message_id

    db["reactroles"].setdefault(str(messageId), {})

    try:
        message = await ctx.channel.fetch_message(messageId)
    except Exception as e:
        await ctx.followup.send(f"sorry but your message is fake (command needs to be run in react role channel)\n-# {e}", ephemeral=True)
        return

    whatdidido = "some funny ass thing happened idfk whats going on this message shouldnt appear"

    if remove == "no":
        whatdidido = f"{ctx.user.mention} set {emoji} {role.mention} as a react role for https://discord.com/channels/{ctx.guild.id}/{ctx.channel.id}/{messageId}"
        db["reactroles"][str(messageId)][emoji] = str(role.id)
        if emoji[0:1] == "<":
            endscorrect = emoji[(len(emoji)-1):(len(emoji))] == ">"
            validchars = re.match(r'^[\w\-<:>]+$', emoji) is not None
            namestart = emoji[1:2] == ":" or emoji[1:2] == "a"
            goodlen = len(emoji) > 22
            lastsecnums = re.fullmatch(r'\d+', ((emoji.rsplit(":", 1)[-1])[:(len((emoji.rsplit(":", 1)[-1]))-1)])) is not None
            secondsection = len(emoji.split(":")) == 3 and emoji.split(":")[1] != ""
            valid = (endscorrect+validchars+namestart+goodlen+lastsecnums+secondsection == 6)
            if not valid:
                await ctx.followup.send(f"vro that's not an emoji", ephemeral=True)
                return
        else:
            console_log(emoji)
            console_log(contains_symbols(emoji))
            if contains_symbols(emoji):
                await ctx.followup.send(f"vro that's not an emoji", ephemeral=True)
                return
    else:
        if emoji not in db["reactroles"][str(messageId)]:
            return await ctx.followup.send("bro what")
        whatdidido = f"{ctx.user.mention} unset {emoji} {role.mention} as a react role for https://discord.com/channels/{ctx.guild.id}/{ctx.channel.id}/{messageId}"
        db["reactroles"][str(messageId)].pop(emoji, None)

    try:
        if remove == "no":
            await message.add_reaction(emoji)
        else:
            await message.remove_reaction(discord.PartialEmoji.from_str(emoji), bot.user)
    except Exception as e:
        if str(e) == "400 Bad Request (error code: 10014): Unknown Emoji":
            await ctx.followup.send(f"failed to add reaction. emoji either malformed or the bot isn't in the server with the emoji", ephemeral=True)
        else:
            await ctx.followup.send(f"failed to add/remove reaction.\n-# {e}", ephemeral=True)
        return
    save_db(guild_id, db)

    await log_action(ctx.guild, whatdidido)
    await ctx.followup.send(whatdidido, ephemeral=False, allowed_mentions=discord.AllowedMentions.none())

def contains_symbols(string):
    pattern = r"""[~!@#$%^&*()_+`1234567890\-=\]\[|}{:";',./<>?a-zA-Z]"""
    return bool(re.search(pattern, string))

@tree.command(name="toggle-ticket-mentions", description="enable or disable ticket pings (command)")
@discord.app_commands.default_permissions(manage_threads=True)
async def togglementions(ctx: commands.Context):
    guild_id = str(ctx.guild.id)
    db = load_db(guild_id)
    user_id = str(ctx.user.id)
    db.setdefault("mod_ticket_pings", [])

    if not user_id in db["mod_ticket_pings"]:
        db["mod_ticket_pings"].append(user_id)
        whatdidido = "You will now be notified for ticket opens."
    else:
        db["mod_ticket_pings"].remove(user_id)
        whatdidido = "You will no longer be notified for ticket opens."

    save_db(guild_id, db)

    await ctx.response.send_message(whatdidido, ephemeral=True)

@tree.command(name="setmod", description="Assign or remove a mod or minimod role from a user")
@discord.app_commands.default_permissions(manage_guild=True)
@app_commands.describe(user="The user to modify", level="What level to assign", reason="The reason for this action")
async def setmod(ctx: commands.Context, user: discord.Member, level: Literal["mod", "minimod", "trial mod", "not mod"], reason: str = "None"):
    guild_id = str(ctx.guild.id)
    db = load_db(guild_id)

    roles = db.get("mod_roles", {})
    mod_role = ctx.guild.get_role(int(roles.get("mod"))) if roles.get("mod") else None
    admin_role = ctx.guild.get_role(int(roles.get("admin"))) if roles.get("admin") else None
    minimod_role = ctx.guild.get_role(int(roles.get("minimod"))) if roles.get("minimod") else None
    trial_mod_role = ctx.guild.get_role(int(roles.get("trial_mod"))) if roles.get("trial_mod") else None
    functional_mod_role = ctx.guild.get_role(int(roles.get("functional_mod"))) if roles.get("functional_mod") else None

    has_admin_role = mod_role in ctx.user.roles if admin_role else False

    if not (
        ctx.user.guild_permissions.manage_guild or
        has_admin_role
    ):
        await ctx.response.send_message("this message should not appear.", ephemeral=True)
        return

    has_mod = mod_role in user.roles if mod_role else False
    has_trial = trial_mod_role in user.roles if trial_mod_role else False
    has_minimod = minimod_role in user.roles if minimod_role else False
    has_functional = functional_mod_role in user.roles if functional_mod_role else False

    try:
        to_add = []
        to_remove = []

        if level == "mod":
            if mod_role and not has_mod:
                to_add.append(mod_role)
            if trial_mod_role and has_trial:
                to_remove.append(trial_mod_role)
            if minimod_role and has_minimod:
                to_remove.append(minimod_role)
            if functional_mod_role and not has_functional:
                to_add.append(functional_mod_role)
            status_text = "mod"

        elif level == "minimod":
            if minimod_role and not has_minimod:
                to_add.append(minimod_role)
            if trial_mod_role and has_trial:
                to_remove.append(trial_mod_role)
            if mod_role and has_mod:
                to_remove.append(mod_role)
            if functional_mod_role and not has_functional:
                to_add.append(functional_mod_role)
            status_text = "minimod"

        elif level == "trial mod":
            if mod_role and has_mod:
                to_remove.append(mod_role)
            if minimod_role and has_minimod:
                to_remove.append(minimod_role)
            if functional_mod_role and has_functional:
                to_remove.append(functional_mod_role)
            if trial_mod_role and not has_trial:
                to_add.append(trial_mod_role)
            status_text = "trial mod"

        elif level == "not mod":
            if mod_role and has_mod:
                to_remove.append(mod_role)
            if minimod_role and has_minimod:
                to_remove.append(minimod_role)
            if functional_mod_role and has_functional:
                to_remove.append(functional_mod_role)
            if trial_mod_role and has_trial:
                to_remove.append(trial_mod_role)
            status_text = "not mod"
            try:
                if str(user.id) in db["mod_ticket_pings"]:
                    db["mod_ticket_pings"].remove(str(user.id))
                    save_db(guild_id, db)
            except Exception as e:
                console_log(e)

        # Apply changes
        if to_add:
            await user.add_roles(*to_add, reason=reason)
        if to_remove:
            await user.remove_roles(*to_remove, reason=reason)

        # Logging
        if level == "not mod":
            log_message = f"{user.mention} had their mod removed by {ctx.user.mention} for `{reason}`."
            send_message = f"{user.mention} had their mod removed by {ctx.user.mention} for `{reason}`."
            dm_message = f"hi nerd your mod status was removed in {ctx.guild} for `{reason}`"
        else:
            log_message = f"{user.mention} was made {status_text} by {ctx.user.mention} for `{reason}`."
            send_message = f"{user.mention} was made {status_text} by {ctx.user.mention} for `{reason}`."
            dm_message = f"hi nerd your mod status was changed to {status_text} in {ctx.guild} for `{reason}`"

        await log_action(ctx.guild, log_message)
        try:
            await user.send(dm_message)
        except Exception as e:
            console_log(f"failed to DM, {e}")
        await ctx.response.send_message(send_message)

    except Exception as e:
        await ctx.channel.send(f"504 internal server error\n-# {e}")

@app_commands.context_menu(name="Translate")
async def translate(interaction: discord.Interaction, message: discord.Message):
    await interaction.response.defer(ephemeral=True)
    if message.content == "":
        await interaction.followup.send("bro there's no text are you dumb or stupid", ephemeral=True)
        return
    detected = detect(message.content)
    if detected == "en":
        await interaction.followup.send("bro this is english are you dumb or stupid", ephemeral=True)
        return

    guild_id = str(interaction.guild.id)
    db = load_db(guild_id)
    mod_roles = db.get("mod_roles", {})
    mod_role = interaction.guild.get_role(int(mod_roles.get("mod"))) if mod_roles.get("mod") else None
    admin_role = interaction.guild.get_role(int(mod_roles.get("admin"))) if mod_roles.get("admin") else None
    junior_role = interaction.guild.get_role(int(mod_roles.get("minimod"))) if mod_roles.get("minimod") else None
    trial_role = interaction.guild.get_role(int(mod_roles.get("trial_mod"))) if mod_roles.get("trial_mod") else None
    functional_role = interaction.guild.get_role(int(mod_roles.get("functional_mod"))) if mod_roles.get("functional_mod") else None

    is_mod = (
        interaction.user.guild_permissions.moderate_members
        or interaction.user.guild_permissions.administrator
        or (mod_role in interaction.user.roles if mod_role else False)
        or (admin_role in interaction.user.roles if admin_role else False)
        or (trial_role in interaction.user.roles if trial_role else False)
        or (junior_role in interaction.user.roles if junior_role else False)
        or (functional_role in interaction.user.roles if functional_role else False)
    )

    translator = Translator(from_lang=detected, to_lang="en")
    translation = translator.translate(message.content)
    if is_mod:
        async def warn_explain_callback(interaction: discord.Interaction):
            await interaction.response.edit_message(
                        content=f"{translation}\n-# Translated from {detected}",
                        view=None,
                    )
            modlog(str(interaction.guild.id), str(message.author.id), interaction.user.id, "not speaking english (via context menu)", "warn")
            translator = Translator(from_lang="en", to_lang=detected)

            totalwarns = 1

            if memberId in logs and "punishments" in logs[message.author.id]:
                for punishment in logs[message.author.id]["punishments"]:
                    if punishment[2] == "warn":
                        totalwarns += 1

            translation2 = translator.translate("Please speak the English language. Other languages aren't allowed here. If you don't know English, use an online translator tool.")
            await message.reply(f"Please speak the English language. Other languages aren't allowed here. If you don't know English, use an online translator tool.\n\n{translation2}")
            await log_action(interaction.guild, f"{message.author.mention} was warned by {interaction.user.mention} for `not speaking english (via context menu)`! (#{totalwarns})")
            return

        warn_explain = discord.ui.Button(label=f"Warn + Explain in {detected}", style=discord.ButtonStyle.secondary)
        warn_explain.callback = warn_explain_callback
        view = discord.ui.View()
        view.add_item(warn_explain)

    if is_mod:
        await interaction.followup.send(f"{translation}\n-# Translated from {detected}", ephemeral=True, view=view)
    else:
        await interaction.followup.send(f"{translation}\n-# Translated from {detected}", ephemeral=True)
bot.tree.add_command(translate)

@tree.command(name="welcome-configure", description="set up welcoming")
@discord.app_commands.default_permissions(manage_guild=True)
@app_commands.describe(mode="on join, on verify, or disable")
@app_commands.describe(emoji=":emoji_13:")
@app_commands.describe(channel="channel for messages, leave blank to disable")
async def personality(ctx: commands.Context, mode: Literal["Disabled", "OnJoin", "OnVerify"] = "Disabled", emoji: str = "Default", channel: discord.TextChannel = None):
    db = load_db(str(ctx.guild.id))
    global default_join_emoji
    db.setdefault("welcome", {}).setdefault("mode", "Disabled")
    db.setdefault("welcome", {}).setdefault("emoji", default_join_emoji)

    if mode == "Disabled":
        db.pop("welcome", None)
        try:
            save_db(str(ctx.guild.id), db)
            await ctx.response.send_message(f"Welcome Messages Disabled.")
            return
        except Exception as e:
            await ctx.channel.send(f"504 internal server error\n-# {e}")
            return
    else:
        db["welcome"]["mode"] = mode
        if channel is None:
            db.pop("welcome", None)
            try:
                save_db(str(ctx.guild.id), db)
                await ctx.response.send_message(f"Welcome Messages Disabled.")
                return
            except Exception as e:
                await ctx.channel.send(f"504 internal server error\n-# {e}")
                return
        else:
            db["welcome"]["channel"] = channel.id
        if emoji == "Default":
           db["welcome"]["emoji"] = default_join_emoji
        else:
           db["welcome"]["emoji"] = emoji
    try:
        welcomemessages = servermessages(str(ctx.guild.id))
        msg = random.choice(welcomemessages)
        save_db(str(ctx.guild.id), db)
        await ctx.response.send_message(f"Welcome messages sent to {channel.mention} will look like this:\n{db["welcome"]["emoji"]} {msg[0]}<@{ctx.user.id}>{msg[1]}")
    except Exception as e:
        await ctx.channel.send(f"504 internal server error\n-# {e}")

@tree.command(name="welcome-message", description="add your most noectqastic seen-zhuh messages here")
@discord.app_commands.default_permissions(manage_guild=True)
@app_commands.describe(mode="what thing you are doing??")
@app_commands.describe(start="start for message (put these in quotes), or index for deletion")
@app_commands.describe(end="end for message (put these in quotes). only used in add mode.")
async def personality(ctx: commands.Context, mode: Literal["Clear", "Add", "Delete", "Pull", "List"] = "List", start: str = "Default", end: str = "Default"):
    db = load_db(str(ctx.guild.id))
    if not mode == "List":
        db.setdefault("welcome", {}).setdefault("messages", [[f"Welcome to {ctx.guild.name}, ", "! Enjoy your stay."]])
    global default_join_messages

    if mode == "Clear":
        db["welcome"].pop("messages", None)
        try:
            save_db(str(ctx.guild.id), db)
            await ctx.response.send_message(f"Custom Welcome Messages Cleared.")
            return
        except Exception as e:
            await ctx.channel.send(f"504 internal server error\n-# {e}")
            return
    elif mode == "Add":
        if start == "Default" or end == "Default":
            await ctx.response.send_message(f"I'd personally not want you to add 'Default{ctx.user.mention}Default' as a welcome message accidentally.\n-# HINT: start goes before mention, end goes after mention. not seporated with spaces by default")
            return
        db["welcome"]["messages"].append([start[1:(len(start)-1)], end[1:(len(end)-1)]])
        try:
            save_db(str(ctx.guild.id), db)
            await ctx.response.send_message(f"Welcome Message `{start[1:(len(start)-1)]}@{ctx.user.name}{end[1:(len(end)-1)]}` Added.")
            return
        except Exception as e:
            await ctx.channel.send(f"504 internal server error\n-# {e}")
            return
    elif mode == "Delete":
        try:
            integer = int(start)
        except Exception as e:
            await ctx.response.send_message(f"bro that's not a number")
            return
        fungus = db["welcome"]["messages"][integer]
        try:
            db["welcome"]["messages"].pop(integer)
        except Exception as e:
            await ctx.response.send_message(f"bro there isnt that many messages are you drunk")
            return
        if len(db["welcome"]["messages"]) == 0:
            db["welcome"].pop("messages", None)
        try:
            save_db(str(ctx.guild.id), db)
            await ctx.response.send_message(f"Removed message `{fungus[0]}@{ctx.user.name}{fungus[1]}`")
            return
        except Exception as e:
            await ctx.channel.send(f"504 internal server error\n-# {e}")
            return
    elif mode == "Pull":
        for msg in default_join_messages:
            db["welcome"]["messages"].append(msg)
        save_db(str(ctx.guild.id), db)
        try:
            await ctx.response.send_message(f"Populated Custom List with the defaults!")
            return
        except Exception as e:
            await ctx.channel.send(f"504 internal server error\n-# {e}")
            return
    elif mode == "List":
        db.setdefault("welcome", {}).setdefault("messages", default_join_messages)
        save_db(str(ctx.guild.id), db)
        x = 0
        output = "```"
        for msg in db["welcome"]["messages"]:
            output = output+f"\n{x}. {msg[0]}@{ctx.user.name}{msg[1]}"
            x += 1
        output = output+"\n```"
        try:
            await ctx.response.send_message(output)
            return
        except Exception as e:
            await ctx.channel.send(f"504 internal server error\n-# {e}")
            return

@tree.command(name="verify", description="twitter checkmark chaotic good version")
@discord.app_commands.default_permissions(manage_guild=True)
@app_commands.describe(user="The user to verify", reason="The reason for this action")
async def verify(ctx: commands.Context, user: discord.Member, reason: str = "None"):
    guild_id = str(ctx.guild.id)
    db = load_db(guild_id)

    roles = db.get("mod_roles", {})
    admin_role = ctx.guild.get_role(int(roles.get("admin"))) if roles.get("admin") else None

    has_admin_role = admin_role in ctx.user.roles if admin_role else False

    verifyroleFile = db.get("verified_role", None)
    try:
        verifyrole = ctx.guild.get_role(int(verifyroleFile))
    except Exception:
        verifyrole = None

    if not (
        ctx.user.guild_permissions.manage_guild or
        has_admin_role
    ):
        await ctx.response.send_message("this message should not appear.", ephemeral=True)
        return

    if not verifyrole:
        await ctx.response.send_message("this message should not appear.", ephemeral=True)
        return

    try:
        await user.add_roles(verifyrole, reason=reason)

        log_message = f"{user.mention} was verified by {ctx.user.mention} for `{reason}`."
        send_message = f"{user.mention} was verified by {ctx.user.mention} for `{reason}`."
        dm_message = f"hi nerd you were manually verified for `{reason}`\nWelcome to {ctx.guild.name}!"

        await log_action(ctx.guild, log_message)
        try:
            await user.send(dm_message)
        except Exception as e:
            console_log(f"failed to DM, {e}")
        await ctx.response.send_message(send_message)

    except Exception as e:
        await ctx.channel.send(f"504 internal server error\n-# {e}")

    if "welcome" in db:
        if db["welcome"]["mode"] == "OnVerify":
            await welcomeUser(guild_id, user.id)

# AI Stuff
@tree.command(name="personality", description="sets AI personality")
@discord.app_commands.default_permissions(manage_guild=True)
async def personality(ctx: commands.Context, name: str = "Reset_###", personality: str = "Reset_###"):
    ai_db = load_ai_db()
    if ctx.guild:
        ai_db.setdefault(str(ctx.guild.id), {}).setdefault("name", "")
        ai_db.setdefault(str(ctx.guild.id), {}).setdefault("prompt", "")

        if personality == "Reset_###":
            ai_db[str(ctx.guild.id)].pop("prompt", None)
        else:
            ai_db[str(ctx.guild.id)]["prompt"] = personality
        if name == "Reset_###":
            ai_db[str(ctx.guild.id)].pop("name", None)
        else:
            ai_db[str(ctx.guild.id)]["name"] = name
        if name == "Reset_###":
            name = ctx.guild.me.nick or bot.user.name
        try:
            await ctx.response.send_message(f"AI Personality updated to {name}")
            save_ai_db(ai_db)
        except Exception as e:
            await ctx.channel.send(f"504 internal server error\n-# {e}")
    else:
        ai_db.setdefault(str(ctx.user.id), {}).setdefault("name", "")
        ai_db.setdefault(str(ctx.user.id), {}).setdefault("prompt", "")

        if personality == "Reset_###":
            ai_db[str(ctx.user.id)].pop("prompt", None)
        else:
            ai_db[str(ctx.user.id)]["prompt"] = personality
        if name == "Reset_###":
            ai_db[str(ctx.user.id)].pop("name", None)
        else:
            ai_db[str(ctx.user.id)]["name"] = name
        if name == "Reset_###":
            name = bot.user.name
        try:
            await ctx.response.send_message(f"AI Personality updated to {name}")
            save_ai_db(ai_db)
        except Exception as e:
            await ctx.channel.send(f"504 internal server error\n-# {e}")

@tree.command(name="set", description="toggle channel for AI")
@discord.app_commands.default_permissions(manage_guild=True)
async def personality(ctx: commands.Context):
    ai_db = load_ai_db()
    ai_db.setdefault("channels", [])

    if ctx.channel.id in ai_db["channels"]:
        index = ai_db["channels"].index(ctx.channel.id)
        ai_db["channels"].pop(index)
        state = "OFF"
    else:
        ai_db["channels"].append(ctx.channel.id)
        state = "ON"
    try:
        try:
            await ctx.response.send_message(f"AI toggled to {state} in {ctx.channel.name}")
        except Exception:
            await ctx.response.send_message(f"AI toggled to {state} in Channel")
        save_ai_db(ai_db)
    except Exception as e:
        await ctx.channel.send(f"504 internal server error\n-# {e}")

@tree.command(name="clear", description="clears message history")
async def clear(ctx: commands.Context):
    global ailoglength
    ailoglength[str(ctx.channel.id)] = []
    try:
        await ctx.response.send_message(f"**== Conversation Cleared! ==**\n*Say hi again!*")
    except Exception as e:
        await ctx.channel.send(f"504 internal server error\n-# {e}")
## END

@bot.event
async def on_message(message: discord.Message):
    if message.author == bot.user:
        return

    if message.content.lower().startswith("i dislike lgb"):
        await message.reply("""hello, three things:
- neocat police is developed by an lgbtq person; this server is a welcoming community and anyone who tries to make it anything else will be obliterated from existence here, i will guarantee it. however, if this server does not want to be a welcoming community, please kindly remove this bot and use a bot such as dyno or carl-bot.
- if you don't support lgbtq for whatever reason, whether it's religious or otherwise, keep it to yourself! it costs you $0 and takes less effort to not spread that opinion in a space, and you will be a much better person for it!! saying things like "i dont like lgbtq" adds nothing to the conversation, vilifies yourself, and will most likely just get you banned from here without being able to get what you want out of the server, support or otherwise
- if you cannot respect the above, there is a nice lovely "leave server" button for you to use
cheerio!
-# original from lewisakura in vencord""")

    if message.guild:
        guild_id = str(message.guild.id)
        db = load_db(guild_id)
    else:
        db = load_db(message.author.id)

# AI LINE STARTS HERE
    if not ("disableAI" in db and db["disableAI"] == True) and enableAI == True:
        ai_db = load_ai_db()
        ai_db.setdefault("channels", [])
        aichannels = ai_db["channels"]
        garry = "Unknown Name"
    
        if message.guild:
            member = message.guild.get_member(message.author.id)
            if member is None:
                try:
                        member = await message.guild.fetch_member(message.author.id)
                except Exception:
                    garry = message.author.global_name or message.author.name
            if member is None:
                garry = message.author.global_name or message.author.name
            else:
                garry = member.nick or member.global_name or member.name
        else:
            garry = message.author.global_name or message.author.name
        global ailoglength
        currentchain = None
        if (any(mention.id == bot.user.id for mention in message.mentions) or "@grok" in message.content or (message.channel.id in aichannels and not message.author.bot)) and not message.webhook_id:
            context = ""
            disableChains = False
            replycorrect = True
            if message.channel.id in aichannels: # /set system, does context things
                disableChains = True
                ailoglength.setdefault(str(message.channel.id), [])
                if len(ailoglength[str(message.channel.id)]) > 50:
                    ailoglength[str(message.channel.id)] = ailoglength[str(message.channel.id)][-50:]
                for q in ailoglength[str(message.channel.id)]:
                    context = context + q
                if message.reference and message.reference.resolved:
                    replycorrect = (bot.user.id == message.reference.resolved.author.id) or (bot.user.id in message.mentions)
    
            if replycorrect: # reply chain system, disabled when /set
                async with message.channel.typing():
                    if message.guild is None:
                        display_name = bot.user.name
                    else:
                        bot_member = message.guild.me
                        display_name = bot_member.nick or bot.user.name
                    ref = message.reference
    
                    chainexists = False
                    if not disableChains:
                        context = ""
                        if ref and ref.message_id:
                            chainexists = True
                            for thread in reply_chain_cache:
                                if ref.message_id in reply_chain_cache[thread]["IDs"]:
                                    currentchain = thread
                                    break
                            if not currentchain is None:
                                reply_chain_cache[currentchain]["Content"] = reply_chain_cache[currentchain]["Content"] + f"{garry}: {message.content}\n"
                                reply_chain_cache[currentchain]["IDs"].append(message.id)
                                if len(reply_chain_cache[currentchain]["Content"].splitlines()) > 100:
                                    dgegeffefewew = reply_chain_cache[currentchain]["Content"].splitlines()[-100:] 
                                    reply_chain_cache[currentchain]["Content"] = "\n".join(dgegeffefewew) + "\n"
                            else:
                                global MAX_CHAIN_DEPTH
                                itteratioens = 0
                                mewhenthe = await message.channel.fetch_message(ref.message_id)
                                chaincontent = f"{mewhenthe.author}: {mewhenthe.content}\n"
                                chainids = [mewhenthe.id]
                                while MAX_CHAIN_DEPTH > itteratioens and mewhenthe.reference is not None:
                                    mewhenthe = await message.channel.fetch_message(mewhenthe.reference.message_id)
                                    chainids.append(mewhenthe.id)
                                    chaincontent = f"{mewhenthe.author}: {mewhenthe.content}\n" + chaincontent
                                    currentchain = mewhenthe.id
                                    itteratioens += 1
                                reply_chain_cache[currentchain] = {"Content": chaincontent, "IDs": chainids}
                        else:
                            reply_chain_cache[message.id] = {"Content": f"{garry}: {message.content}\n", "IDs": [message.id]}
                            currentchain = message.id
                        context = reply_chain_cache[currentchain]["Content"]
                    if message.guild:
                        name = ai_db.get(str(message.guild.id), {}).get("name", display_name)
                        prompt = ai_db.get(str(message.guild.id), {}).get("prompt", defaultprompt.replace(";{%!name!%};", name))
                    else:
                        name = ai_db.get(str(message.author.id), {}).get("name", display_name)
                        prompt = ai_db.get(str(message.author.id), {}).get("prompt", defaultprompt.replace(";{%!name!%};", name))
    
                    ctblk = ""
                    if chainexists:
                        ctblk = "Cited Replies:\n"
                    if disableChains == True:
                        try:
                            ctblk = f"Past Messages in `#{message.channel.name}`:\n"
                        except Exception:
                            ctblk = f"Past Messages in Channel:\n"
                    if message.guild:
                        query = f"You are {name}. {prompt} You are in a discord server called \"{message.guild.name}\", owned by \"{message.guild.owner}\". Do not include mentions (<@###########>) or Replies in your messages.\n\n\n{ctblk}{context}\n\nNow, respond to this query from {garry}:\n{message.content}"
                    else:
                        query = f"You are {name}. {prompt} You are in DMs with \"{garry}\". Do not include mentions (<@###########>) or Replies in your messages.\n\n\n{ctblk}{context}\n\nNow, respond to this query from {garry}:\n{message.content}"

                    response = await query_ollama(query)
                    trimmed_response = response[:2000]
                    if disableChains:
                        ailoglength[str(message.channel.id)].append(f"{garry}: {message.content}\n")
                        ailoglength[str(message.channel.id)].append(f"{name}: {trimmed_response}\n")
                    sent = None
                    try:
                        sent = await message.reply(trimmed_response, allowed_mentions=discord.AllowedMentions.none())
                    except Exception:
                        sent = await message.channel.send(trimmed_response, allowed_mentions=discord.AllowedMentions.none())
                    if currentchain is not None:
                        reply_chain_cache[currentchain]["Content"] = reply_chain_cache[currentchain]["Content"] + f"{name}: {trimmed_response}\n"
                        reply_chain_cache[currentchain]["IDs"].append(sent.id)

        if random.randint(1, 1000) == 1 or message.content == "ncpol!dothathingiforgot" and message.author.id == evaluser:
            if not ("disableFreakouts" in db and db["disableFreakouts"] == True):
                async with message.channel.typing():
                    messages = [msg async for msg in message.channel.history(limit=20)]
                    messages.reverse()
                    message_history = "\n".join([f"{msg.author}: {msg.content}" for msg in messages])

                    query = f"You just joined a Discord chat. Comment something about the recent messages. Be as abrupt and wild as possible, shocking everyone with your entrance remark, but stay on topic instead of bringing up crazy things that didn't happen. Do not put your message in quotes. Speak in all Capitals. Here is the content of the last messages: {message_history}"

                    response = await query_ollama(query)
                    if not response == "AI Unavailable":
                        trimmed_response = response[:2000]
                        try:
                            await message.reply(trimmed_response, allowed_mentions=discord.AllowedMentions.none())
                        except Exception:
                            await message.channel.send(trimmed_response, allowed_mentions=discord.AllowedMentions.none())
        elif random.randint(1, 1000) == 1 or message.content == "ncpol!dothathingirember" and message.author.id == evaluser:
            if ("the_ncpol_press" in db):
                try:
                    channel = bot.get_channel(db["the_ncpol_press"])
                except:
                    console_log("getting channel error fuck you")
                    return
                async with channel.typing():
                    messages = [msg async for msg in message.channel.history(limit=20)]
                    messages.reverse()
                    message_history = "\n".join([f"{msg.author}: {msg.content}" for msg in messages])

                    query = f"You are an over-the-top news reporter for a parody news outlet. Take ordinary Discord events (like bots misbehaving, people sending emojis, or channels being renamed) and report them as if they are breaking world news. Write in the style of satirical journalism — with dramatic headlines, fake celebrity reactions, and exaggerated global consequences. Blend tech jargon, politics, and pop culture into the narrative. Every story should sound like The Onion crossed with a tech blog. Use Markov formatting for the header (\"# Article Name Here, In Title Case\"). Keep the story related to the conversation history at least at the start (e.g. explain the message history, then make up its implications on worldwide politics), and only write one. Try to keep the story under 2000 characters, but also don't make it breif. Here is the content of the last messages: {message_history}"

                    response = await query_ollama(query)
                    if not response == "AI Unavailable":
                        trimmed_response = response.replace("# ", "#").replace("#", "# ")[:2000]
                        threadmessage = await channel.send(trimmed_response, allowed_mentions=discord.AllowedMentions.none())
                        trimmed_response_2 = response.replace("# ", "#").replace("#", "# ")[2000:4000]
                        if not trimmed_response_2 == "" and not trimmed_response_2 is None:
                            threadmessage = await channel.send(trimmed_response_2, allowed_mentions=discord.AllowedMentions.none())
                        headline = trimmed_response.splitlines()[0]
                        headline = headline.replace("#", "")
                        await threadmessage.create_thread(
                            name=headline[:100],
                            auto_archive_duration=60
                        )
    # AI END

    if message.guild is None:
        return

    global rainstreaks
    global usernameCache
    global catchesInChannels
    global catchesInBirdChannels
    if not message.author.name in usernameCache and not message.author.bot:
        usernameCache[message.author.name] = message.author.id

    # i forgor what this does
    channel_id = str(message.channel.id)

    rainstreaks.setdefault(message.channel.id, 0)
    isarainmsg = 0
    if "cat rain has ended" in message.content.lower():
        isarainmsg = 1
    sentbycatbot = 0
    if message.author.name == "Cat Bot" and message.author.bot:
        sentbycatbot = 1
    if isarainmsg and sentbycatbot:
        rainstreaks[message.channel.id] = rainstreaks[message.channel.id] + 1
        if rainstreaks[message.channel.id] == 3:
            perms = message.channel.overwrites_for(message.guild.default_role)
            perms.send_messages=False
            await message.channel.set_permissions(message.guild.default_role, overwrite=perms)
            await message.channel.send(f":lock: {message.channel.mention} has been locked by {bot.user.mention} for 3 seconds.")
            await asyncio.sleep(3)
            perms.send_messages=True
            await message.channel.set_permissions(message.guild.default_role, overwrite=perms)
            rainstreaks[message.channel.id] = 0

    # Check if it's a slow catching channel
    if db.get("slow_catching", {}).get(channel_id):
        sentbycatbotorbird = 0
        if message.author.name == "Cat Bot" and message.author.bot:
            if "cat has appeared" in message.content.lower():
                sentbycatbotorbird = 1

        if message.author.name == "bird" and message.author.bot:
            embed = message.embeds[0]
            if embed.description and embed.description.strip() == 'Type "bird" to catch it!':
                sentbycatbotorbird = 1

        if sentbycatbotorbird:
            perms = message.channel.overwrites_for(message.guild.default_role)
            perms.send_messages=False
            await message.channel.set_permissions(message.guild.default_role, overwrite=perms)
            sendmsg = await message.channel.send(f"The channel will unlock <t:{int(time.time())+3600}:R>")
            await asyncio.sleep(3600)
            await sendmsg.delete()
            perms.send_messages=True
            await message.channel.set_permissions(message.guild.default_role, overwrite=perms)

    # Check if it's a catching channel
    if db.get("catching", {}).get(channel_id):
        if message.author.name == "Cat Bot" and message.author.bot:
            catchdetected = False
            word_detected = "idk!"
            linect = 0
            catchdetected = False
            messagelower = message.content.lower()
            cheksec = "seconds" in message.content
            chekmin = "minutes" in message.content
            chekhou = "hours" in message.content
            chekday = "days" in message.content

            if not (cheksec or chekmin or chekhou or chekday):
                return
            catchdetected = True

            catchline = message.content
            yeahokliberal = catchline.split()
            excluded_chars = "~!@#$%^&*()+{}:\"<>?-=[];',/`QAZWSXEDCRFVTGBYHNUJMIKOLP"
            evilstuff = list(excluded_chars)

            distilled_catch = yeahokliberal[:]
            for qweyu in yeahokliberal:
                for funny in evilstuff:
                    if (funny in qweyu):
                        if qweyu in distilled_catch:
                            distilled_catch.remove(qweyu)
            xx_catch = []

            for word in distilled_catch:
                xx_catch.append(word.replace("\\", ""))

            xxx_catch = []

            for word in xx_catch:
                if word in usernameCache:
                    xxx_catch.append(word)

            okayStopDistillingIt = []

            for word in xxx_catch:
                if not word in okayStopDistillingIt:
                    okayStopDistillingIt.append(word)

            if len(okayStopDistillingIt) > 1:
                await message.reply(f"confict in double distill, 2 cached usernames in catch message. this isnt funny.")
                return

            if len(okayStopDistillingIt) < 1:
                await message.reply(f"QHAR?!?!?!?!?!")
                return

            username = okayStopDistillingIt[0]

            if catchdetected:
                if username == "Unknown Catcher":
                    await message.channel.send(f"idk who tf caught the cat (please report this bug if encountered, include catch message) (expected if custom message is in use)")
                else:
                    catchuserId = None
                    if not username in usernameCache:
                        await message.channel.send(f"idk who tf {username} is (please report this bug if encountered, include catch message)", allowed_mentions=discord.AllowedMentions.none())
                        return
                    else:
                        catchuserId = usernameCache[username]
                    timeoutLength = defaultdctimeout
                    if "DCTimeout" in db:
                        timeoutLength = db["DCTimeout"]

                    RuleH = "The Rule"
                    if "DCRuleNumber" in db:
                        RuleH = f"Rule {db['DCRuleNumber']}"

                    catchesInChannels.setdefault(guild_id, {})
                    catchesInChannels[guild_id].setdefault(str(catchuserId), {})
                    catchesInChannels[guild_id][str(catchuserId)].setdefault("catchChannel", message.channel.id)
                    kreisi_time = round(time.time()) + timeoutLength
                    catchesInChannels[guild_id][str(catchuserId)].setdefault("catchTimeout", kreisi_time)
                    correctchannel = catchesInChannels[guild_id][str(catchuserId)]["catchChannel"] == message.channel.id
                    correcttime = round(time.time()) < catchesInChannels[guild_id][str(catchuserId)]["catchTimeout"]
                    mins = str(round(timeoutLength/6)/10).replace('.0', '')

                    if not correctchannel and correcttime:
                        await message.reply(f":warning: __**{RuleH} - No double catching.**__\nYou caught a cat in another channel in the past {mins} minutes. Please gift this catch to the peson who caught the previous cat in this channel and don't double catch in the future.")
                        modlog(str(guild_id), str(catchuserId), bot.user.id, "double-catching", "warn")
                        await log_action(message.guild, f"{username} tried catching a cat in <#{message.channel.id}> less than {mins} minutes after a catch in another channel.")
                    else:
                        catchesInChannels[guild_id][str(catchuserId)]["catchChannel"] = message.channel.id
                        catchesInChannels[guild_id][str(catchuserId)]["catchTimeout"] = kreisi_time

    # making use of functions ❌️❌️❌️
    # adding the code twice ✅️✅️✅️✅️✅️✅️✅️✅️✅️💯️💯️💯️💯️💯️

    if db.get("catching-birds", {}).get(channel_id):
        if message.author.name == "bird" and message.author.bot:
            catchdetected = False
            word_detected = "idk!"
            linect = 0
            catchdetected = False

            if message.author.name == "bird" and message.author.bot:
                embed = message.embeds[0]
                if embed.description and len(embed.description.splitlines()) == 3:
                    catchdetected = True
                    if len(embed.description.split()) == 0:
                        return
                    username = embed.description.split()[0].lower()

            if catchdetected:
                if username == "Unknown Catcher":
                    await message.channel.send(f"idk who tf caught the bird (please report this bug if encountered, include catch message)")
                else:
                    catchuserId = None
                    if not username in usernameCache:
                        await message.channel.send(f"idk who tf {username} is (please report this bug if encountered, include catch message)", allowed_mentions=discord.AllowedMentions.none())
                        return
                    else:
                        catchuserId = usernameCache[username]
                    timeoutLength = defaultdctimeout
                    if "DCTimeout_Bird" in db:
                        timeoutLength = db["DCTimeout_Bird"]

                    RuleH = "The Rule"
                    if "DCRuleNumber" in db:
                        RuleH = f"Rule {db['DCRuleNumber']}"

                    catchesInBirdChannels.setdefault(guild_id, {})
                    catchesInBirdChannels[guild_id].setdefault(str(catchuserId), {})
                    catchesInBirdChannels[guild_id][str(catchuserId)].setdefault("catchChannel", message.channel.id)
                    kreisi_time = round(time.time()) + timeoutLength
                    catchesInBirdChannels[guild_id][str(catchuserId)].setdefault("catchTimeout", kreisi_time)
                    correctchannel = catchesInBirdChannels[guild_id][str(catchuserId)]["catchChannel"] == message.channel.id
                    correcttime = round(time.time()) < catchesInBirdChannels[guild_id][str(catchuserId)]["catchTimeout"]
                    mins = str(round(timeoutLength/6)/10).replace('.0', '')

                    if not correctchannel and correcttime:
                        await message.reply(f":warning: __**{RuleH} - No double catching.**__\nYou caught a bird in another channel in the past {mins} minutes. Please gift this catch to the peson who caught the previous bird in this channel and don't double catch in the future.")
                        modlog(str(guild_id), str(catchuserId), bot.user.id, "double-catching", "warn")
                        await log_action(message.guild, f"{username} tried catching a bird in <#{message.channel.id}> less than {mins} minutes after a catch in another channel.")
                    else:
                        catchesInBirdChannels[guild_id][str(catchuserId)]["catchChannel"] = message.channel.id
                        catchesInBirdChannels[guild_id][str(catchuserId)]["catchTimeout"] = kreisi_time


    underage_role = db.get("underage_role")

    # Check if in a Yapping City forum
    yapping_forums = db.get("yapping_forums", {})
    whitelists = db.get("whitelists", {})

    if isinstance(message.channel, discord.Thread) and str(message.channel.parent_id) in yapping_forums:
        thread = message.channel
        commandByOP = 0
        if message.interaction_metadata:
            if message.interaction_metadata.user.id == thread.owner_id:
                commandByOP = 1
        if message.author.id == thread.owner_id or commandByOP:
            return  # thread creator is allowed and bots they use are allowed
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
            console_log(f"Error deleting message or sending DM: {e}")

    if not underage_role is None:
        if not message.guild is None:
            if not isinstance(message.author, discord.Member):
                try:
                    member = await message.guild.fetch_member(message.author.id)
                except discord.NotFound:
                    return
            if discord.utils.get(message.author.roles, id=int(underage_role)):
                if not message.type == discord.MessageType.new_member:
                    await message.delete()
                    await message.author.send(f"hello nerd you might have been banned from {message.guild.name} for `Picked <13 in onboarding`. you cant appeal this, shouldnt have been stupid")
                    await log_spammy(message.guild, f"{message.author.mention} was permanently banned by {bot.user.mention} for `Picked <13 in onboarding`.")
                    await message.guild.ban(message.author, reason="Picked <13 in onboarding", delete_message_seconds=60)
                    return

    # Check if it's a dementia chat channel
    if db.get("dementia_chats", {}).get(channel_id):
        # Fetch recent messages
        messages = [msg async for msg in message.channel.history(limit=100, oldest_first=True)]
        if len(messages) > 7:
            # How many to delete?
            to_delete = len(messages) - 7
            delete_msgs = messages[:to_delete]

            try:
                await message.channel.delete_messages(delete_msgs)
            except discord.HTTPException:
                # If bulk delete fails (too old?), delete one by one
                for msg in delete_msgs:
                    try:
                        await msg.delete()
                    except Exception:
                        pass  # Ignore failures

    # Check if it's a haiku channel
    if db.get("haikus-allowed", {}).get(channel_id):
        gwg = detect_haiku(message.content)
        if not gwg == False:
            await message.channel.send(f"*\"{gwg}\"*\n ‎- {message.author}")

    await bot.process_commands(message)

@bot.command(help="basically abotminbmnrnr has a level 0 beta eval command")
async def print(ctx, *, prompt: str):
    if ctx.author.id == evaluser:
        try:
            result = evil(prompt, {"__builtins__": __builtins__}, {})
            if asyncio.iscoroutine(result):
                result = await result
            if result is None:
                await ctx.send("Success!")
            else:
                await ctx.send(str(result))
        except Exception as e:
            await ctx.send(str(e))

@bot.command(help="and cat bot has a level 100 skibidi sigma mafia boss eval command")
async def eval(ctx, *, prompt: str):
    if ctx.author.id == evaluser:
        # complex eval, multi-line + async support
        # requires the full `await message.channel.send(2+3)` to get the result
        # thanks mia lilenakos
        spaced = ""
        for i in prompt.split("\n"):
            spaced += "  " + i + "\n"

        intro = (
            "async def go(prompt, bot, ctx):\n"
            " try:\n"
        )
        ending = (
            "\n except Exception:\n"
            "  await ctx.send(traceback.format_exc())"
            "\nbot.loop.create_task(go(prompt, bot, ctx))"
        )

        complete = intro + spaced + ending
        exec(complete)

@bot.command(help="restarts the bot")
async def restart(ctx):
    if ctx.author.id == evaluser:
        console_log("restart has been triggered...")
        await ctx.send("restarting bot...")
        os.execv(sys.executable, ['python'] + sys.argv)

@bot.command(help="ok bro")
async def status(ctx, *, prompt: str):
    if ctx.author.id == evaluser:
        try:
            await bot.change_presence(activity=discord.CustomActivity(name=prompt))
            await ctx.send(f"Status updated to: {prompt}")
        except Exception as e:
            await ctx.send(str(e))

@bot.command(help="Shows this message")
async def help(ctx):
    await ctx.send("```\nNo Category:\n  help  Shows this message\n\nType ncpol!help command for more info on a command.\nYou can also type ncpol!help category for more info on a category.\nWho am I kidding? There's no commands here.\nKids these days like their slash commands, leaving text commands like us in the dust.\nMove along. Now.\n\nWhy are you still here? Just to watch me, ncpol!help, suffer?\n\nSeriously, go away. You are not welcome here.```")

@bot.command(help="okay bro")
async def test(ctx):
    await ctx.send("NeoCat Police isn't down!")

def syllable_count(word):
    word = word.lower()
    word = re.sub(r'[^a-z]', '', word)

    SPECIAL_CASES = {
        "trying": 2,
        "queue": 1,
        "fire": 1,
        "hour": 1,
        "poem": 2,
        "family": 2,
    }

    if word in SPECIAL_CASES:
        return SPECIAL_CASES[word]

    if word in d:
        # Return the minimum syllable count across all pronunciations
        return min([len([ph for ph in pron if ph[-1].isdigit()]) for pron in d[word]])
    else:
        # Fallback to heuristic for unknown words
        return syllables.estimate(word)

def sentence_syllable_count(sentence):
    return sum(syllable_count(word) for word in sentence.split())

def line_syllables(line):
    words = line.strip().split()
    return sum(syllable_count(word) for word in words)

def detect_haiku(text):
    words = re.findall(r'\b\w+\b', text.lower())
    syllables = [syllable_count(word) for word in words]

    if None in syllables:
        return False

    target_lines = [5, 7, 5]
    lines = []
    current_line = []
    current_syllables = 0
    target_index = 0

    for word, syl in zip(words, syllables):
        if syl > target_lines[target_index]:
            return False

        if current_syllables + syl > target_lines[target_index]:
            return False

        current_line.append(word)
        current_syllables += syl

        if current_syllables == target_lines[target_index]:
            lines.append(' '.join(current_line))
            current_line = []
            current_syllables = 0
            target_index += 1

            if target_index >= 3:
                break

    if target_index < 3 or sum(syllables) != 17:
        return False

    return "\n".join(lines)

bot.run(TOKEN)

