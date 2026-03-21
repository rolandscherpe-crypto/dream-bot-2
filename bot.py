import os
import sqlite3
import discord
from discord import app_commands
from discord.ext import commands

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.messages = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

DB_PATH = "bot.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS guild_settings (
        guild_id INTEGER PRIMARY KEY,
        welcome_channel_id INTEGER,
        welcome_message TEXT,
        premium_enabled INTEGER DEFAULT 0
    )
    """)

    conn.commit()
    conn.close()


def set_welcome(guild_id: int, channel_id: int, message: str):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO guild_settings (guild_id, welcome_channel_id, welcome_message)
        VALUES (?, ?, ?)
        ON CONFLICT(guild_id) DO UPDATE SET
            welcome_channel_id = excluded.welcome_channel_id,
            welcome_message = excluded.welcome_message
    """, (guild_id, channel_id, message))

    conn.commit()
    conn.close()


def get_guild_settings(guild_id: int):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        SELECT welcome_channel_id, welcome_message, premium_enabled
        FROM guild_settings
        WHERE guild_id = ?
    """, (guild_id,))

    row = cur.fetchone()
    conn.close()
    return row


def is_premium(guild_id: int) -> bool:
    row = get_guild_settings(guild_id)
    return bool(row and row[2] == 1)


@bot.event
async def on_ready():
    init_db()
    await tree.sync()
    print(f"Eingeloggt als {bot.user}")


@bot.event
async def on_member_join(member: discord.Member):
    settings = get_guild_settings(member.guild.id)
    if not settings:
        return

    welcome_channel_id, welcome_message, _premium = settings

    if not welcome_channel_id or not welcome_message:
        return

    channel = member.guild.get_channel(welcome_channel_id)
    if channel:
        msg = welcome_message.replace("{user}", member.mention).replace("{server}", member.guild.name)
        await channel.send(msg)


@tree.command(name="setup_welcome", description="Setzt den Willkommenskanal und die Nachricht.")
@app_commands.checks.has_permissions(administrator=True)
async def setup_welcome(
    interaction: discord.Interaction,
    channel: discord.TextChannel,
    message: str
):
    if interaction.guild is None:
        await interaction.response.send_message("Dieser Befehl funktioniert nur in einem Server.", ephemeral=True)
        return

    set_welcome(interaction.guild.id, channel.id, message)
    await interaction.response.send_message(
        f"Willkommensnachricht gesetzt für {channel.mention}.",
        ephemeral=True
    )


@tree.command(name="premium_status", description="Zeigt den Premium-Status dieses Servers.")
async def premium_status(interaction: discord.Interaction):
    if interaction.guild is None:
        await interaction.response.send_message("Dieser Befehl funktioniert nur in einem Server.", ephemeral=True)
        return

    premium = is_premium(interaction.guild.id)
    text = "Premium ist aktiv." if premium else "Premium ist nicht aktiv."
    await interaction.response.send_message(text, ephemeral=True)


@tree.command(name="announce", description="Sendet eine Ankündigung (Premium-Funktion).")
@app_commands.checks.has_permissions(manage_guild=True)
async def announce(interaction: discord.Interaction, text: str):
    if interaction.guild is None:
        await interaction.response.send_message("Dieser Befehl funktioniert nur in einem Server.", ephemeral=True)
        return

    if not is_premium(interaction.guild.id):
        await interaction.response.send_message(
            "Diese Funktion ist Premium.",
            ephemeral=True
        )
        return

    if interaction.channel is None:
        await interaction.response.send_message("Kanal nicht gefunden.", ephemeral=True)
        return

    await interaction.channel.send(f"📢 {text}")
    await interaction.response.send_message("Ankündigung gesendet.", ephemeral=True)


@setup_welcome.error
async def setup_welcome_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.errors.MissingPermissions):
        await interaction.response.send_message(
            "Du brauchst Administrator-Rechte für diesen Befehl.",
            ephemeral=True
        )


@announce.error
async def announce_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.errors.MissingPermissions):
        await interaction.response.send_message(
            "Du brauchst die Berechtigung 'Server verwalten' für diesen Befehl.",
            ephemeral=True
        )


if not TOKEN:
    raise ValueError("DISCORD_TOKEN ist nicht gesetzt.")

bot.run(TOKEN)
