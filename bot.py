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
@bot.event
async def on_member_join(member):
    role_name = "Mitglied"

    role = discord.utils.get(member.guild.roles, name=role_name)

    if role:
        await member.add_roles(role)
        print(f"{member} hat die Rolle {role_name} bekommen")
    else:
        print("Rolle nicht gefunden!")
class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Ticket erstellen", style=discord.ButtonStyle.green, custom_id="create_ticket")
    async def create_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.guild is None:
            await interaction.response.send_message("Das geht nur in einem Server.", ephemeral=True)
            return

        guild = interaction.guild
        user = interaction.user

        category = discord.utils.get(guild.categories, name="Tickets")
        if category is None:
            category = await guild.create_category("Tickets")

        existing_channel = discord.utils.get(guild.text_channels, name=f"ticket-{user.name.lower()}")
        if existing_channel:
            await interaction.response.send_message(
                f"Du hast schon ein Ticket: {existing_channel.mention}",
                ephemeral=True
            )
            return

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True)
        }

        channel = await guild.create_text_channel(
            name=f"ticket-{user.name.lower()}",
            category=category,
            overwrites=overwrites
        )

        await channel.send(
            f"{user.mention} willkommen in deinem Ticket.\n"
            f"Ein Moderator wird sich bald kümmern.\n\n"
            f"Zum Schließen: `/close_ticket`"
        )

        await interaction.response.send_message(
            f"Dein Ticket wurde erstellt: {channel.mention}",
            ephemeral=True
        )


@tree.command(name="ticket_panel", description="Erstellt ein Ticket-Panel.")
@app_commands.checks.has_permissions(administrator=True)
async def ticket_panel(interaction: discord.Interaction):
    embed = discord.Embed(
        title="Support Tickets",
        description="Klicke auf den Button unten, um ein Ticket zu erstellen.",
    )
    await interaction.response.send_message("Ticket-Panel wurde erstellt.", ephemeral=True)
    await interaction.channel.send(embed=embed, view=TicketView())


@tree.command(name="close_ticket", description="Schließt das aktuelle Ticket.")
@app_commands.checks.has_permissions(manage_channels=True)
async def close_ticket(interaction: discord.Interaction):
    if interaction.channel is None or interaction.guild is None:
        await interaction.response.send_message("Das geht hier nicht.", ephemeral=True)
        return

    if not interaction.channel.name.startswith("ticket-"):
        await interaction.response.send_message("Das ist kein Ticket-Kanal.", ephemeral=True)
        return

    await interaction.response.send_message("Ticket wird geschlossen.", ephemeral=True)
    await interaction.channel.delete()
    @tree.command(name="kick", description="Kickt einen Benutzer.")
@app_commands.checks.has_permissions(kick_members=True)
async def kick_user(interaction: discord.Interaction, member: discord.Member, grund: str = "Kein Grund angegeben"):
    if interaction.guild is None:
        await interaction.response.send_message("Das geht nur in einem Server.", ephemeral=True)
        return

    await member.kick(reason=grund)
    await interaction.response.send_message(f"{member.mention} wurde gekickt. Grund: {grund}")


@tree.command(name="ban", description="Bannt einen Benutzer.")
@app_commands.checks.has_permissions(ban_members=True)
async def ban_user(interaction: discord.Interaction, member: discord.Member, grund: str = "Kein Grund angegeben"):
    if interaction.guild is None:
        await interaction.response.send_message("Das geht nur in einem Server.", ephemeral=True)
        return

    await member.ban(reason=grund)
    await interaction.response.send_message(f"{member.mention} wurde gebannt. Grund: {grund}")


@tree.command(name="clear", description="Löscht eine Anzahl von Nachrichten.")
@app_commands.checks.has_permissions(manage_messages=True)
async def clear_messages(interaction: discord.Interaction, anzahl: app_commands.Range[int, 1, 100]):
    if interaction.channel is None:
        await interaction.response.send_message("Kanal nicht gefunden.", ephemeral=True)
        return

    await interaction.response.send_message(f"Lösche {anzahl} Nachrichten...", ephemeral=True)
    await interaction.channel.purge(limit=anzahl)
bot.run(TOKEN)
