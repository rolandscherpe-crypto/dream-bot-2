import os
import sqlite3
import random
import time
import discord
from discord import app_commands
from discord.ext import commands, tasks

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.messages = True
intents.message_content = True
intents.presences = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

DB_PATH = "bot.db"

# ---------------------------
# KANÄLE FÜR AKTIVITÄTS-BOOSTER
# ---------------------------
BOOSTER_CHANNELS = {
    "allgemein": {
        "activity_prompts": [
            "Was geht heute bei euch noch?",
            "Woran arbeitet ihr gerade?",
            "Was war heute euer Highlight?",
            "Was macht für euch einen guten Discord-Server aus?",
            "Wer ist gerade da und was macht ihr so?",
            "Wenn ihr euch heute noch etwas gönnen könntet, was wäre es?",
            "Was war euer produktivster Moment heute?",
            "Wer von euch ist gerade noch voll im Arbeitsmodus?",
            "Kurze Runde: Was habt ihr heute schon geschafft?",
            "Was würdet ihr heute Abend noch gern erledigen?"
        ],
        "reaction_games": [
            {"text": "Schnell! Wer zuerst mit 🔥 reagiert, bekommt Bonus-XP!", "emoji": "🔥", "xp_min": 10, "xp_max": 30},
            {"text": "Check-in! Reagiere mit 👋, wenn du gerade wirklich da bist.", "emoji": "👋", "xp_min": 10, "xp_max": 25},
            {"text": "Wer heute produktiv war, reagiert mit 💪", "emoji": "💪", "xp_min": 10, "xp_max": 20},
            {"text": "Team Kaffee oder Energie? Reagiere mit ☕", "emoji": "☕", "xp_min": 10, "xp_max": 20},
            {"text": "Schnelltest: Wer das hier zuerst sieht, reagiert mit ⚡", "emoji": "⚡", "xp_min": 15, "xp_max": 30},
            {"text": "Kurze Aktivitätsrunde: Reagiere mit ✅, wenn du online und wach bist.", "emoji": "✅", "xp_min": 10, "xp_max": 20},
            {"text": "Wer gerade an etwas arbeitet, reagiert mit 🛠️", "emoji": "🛠️", "xp_min": 10, "xp_max": 20},
            {"text": "Mini-Game: Der erste mit 🚀 bekommt Extra-XP!", "emoji": "🚀", "xp_min": 15, "xp_max": 30},
            {"text": "Wer heute gute Laune hat, reagiert mit 😄", "emoji": "😄", "xp_min": 10, "xp_max": 20},
            {"text": "Sofortreaktion: Wer hier ist, reagiert mit 👀", "emoji": "👀", "xp_min": 10, "xp_max": 20}
        ],
        "challenges": [
            {"text": "Mini-Challenge: Schreib in einem Satz, woran du gerade arbeitest. Beste Antwort bekommt Bonus-XP.", "xp_min": 30, "xp_max": 60},
            {"text": "Challenge: Schreib hier dein Ziel für heute rein. Eine gute Antwort bekommt Bonus-XP.", "xp_min": 30, "xp_max": 60},
            {"text": "Kurze Community-Challenge: Was war dein bester Moment diese Woche?", "xp_min": 30, "xp_max": 70},
            {"text": "Challenge: Nenne etwas, das du heute gelernt hast.", "xp_min": 30, "xp_max": 70},
            {"text": "Mitmach-Challenge: Was motiviert dich gerade am meisten?", "xp_min": 35, "xp_max": 70},
            {"text": "Kleine Aufgabe: Schreib eine Sache, die du diese Woche noch schaffen willst.", "xp_min": 30, "xp_max": 60},
            {"text": "Challenge: Zeig mit Worten oder Bild, was dich aktuell beschäftigt.", "xp_min": 40, "xp_max": 80},
            {"text": "Mitmach-Frage: Was würdest du an einem Discord-Server sofort besser machen?", "xp_min": 30, "xp_max": 70},
            {"text": "Community-Challenge: Schreib deine beste Idee für mehr Aktivität in einem Server.", "xp_min": 35, "xp_max": 75},
            {"text": "Kleine Kreativrunde: Schreib drei Wörter, die deinen Tag beschreiben.", "xp_min": 30, "xp_max": 60}
        ],
        "quizzes": [
            {"question": "Quiz: Was ist oft wichtiger für einen guten Server? A: Aktivität oder B: Perfektes Design", "answer": "a", "xp_min": 50, "xp_max": 100},
            {"question": "Quiz: Was bringt mehr Community-Gefühl? A: Austausch oder B: Stille", "answer": "a", "xp_min": 50, "xp_max": 100},
            {"question": "Quiz: Was hält Leute eher im Server? A: Bewegung oder B: Leere", "answer": "a", "xp_min": 50, "xp_max": 100},
            {"question": "Quiz: Was ist wichtiger? A: Vertrauen oder B: Zufall", "answer": "a", "xp_min": 50, "xp_max": 100},
            {"question": "Quiz: Was ist besser für Wachstum? A: Aktivität oder B: tote Kanäle", "answer": "a", "xp_min": 50, "xp_max": 100},
            {"question": "Quiz: Was hilft mehr? A: Mitmachen oder B: nur zuschauen", "answer": "a", "xp_min": 50, "xp_max": 100},
            {"question": "Quiz: Wodurch entsteht eher Gespräch? A: Frage oder B: Schweigen", "answer": "a", "xp_min": 50, "xp_max": 100},
            {"question": "Quiz: Was ist besser für Bindung? A: Interaktion oder B: Funkstille", "answer": "a", "xp_min": 50, "xp_max": 100},
            {"question": "Quiz: Was bringt eher neue Leute zum Bleiben? A: lebendige Kanäle oder B: leere Räume", "answer": "a", "xp_min": 50, "xp_max": 100},
            {"question": "Quiz: Was wirkt professioneller? A: aktive Community oder B: nichts los", "answer": "a", "xp_min": 50, "xp_max": 100}
        ]
    },
    "ideen": {
        "activity_prompts": [
            "Welche neue Idee würdet ihr gern mal umgesetzt sehen?",
            "Was würdet ihr gerade gern entwickeln oder entwerfen?",
            "Welche kreative Idee spukt euch gerade im Kopf herum?",
            "Was wäre ein richtig gutes personalisiertes Geschenk?",
            "Welche Farbe oder welches Material findet ihr aktuell am besten?",
            "Wenn ihr etwas Neues entwerfen könntet: Was wäre es?",
            "Welche Produktidee fehlt eurer Meinung nach noch?",
            "Was würdet ihr lieber gestalten: Holz, Acryl oder Metall?",
            "Welche Idee würdet ihr sofort testen?",
            "Was war eure beste kreative Idee in letzter Zeit?"
        ],
        "reaction_games": [
            {"text": "Ideen-Check: Team Holz 🪵 oder Team Acryl ✨? Reagiere jetzt!", "emoji": "🪵", "xp_min": 10, "xp_max": 25},
            {"text": "Wer hat gerade kreative Energie? Reagiere mit 🎨", "emoji": "🎨", "xp_min": 10, "xp_max": 25},
            {"text": "Schnellrunde: Reagiere mit 💡, wenn du gerade eine Idee hast.", "emoji": "💡", "xp_min": 10, "xp_max": 25},
            {"text": "Wer hätte Lust auf ein neues Produktkonzept? Reagiere mit 🚀", "emoji": "🚀", "xp_min": 10, "xp_max": 30},
            {"text": "Kreativ-Check: Reagiere mit ✍️, wenn du gern Ideen sammelst.", "emoji": "✍️", "xp_min": 10, "xp_max": 25},
            {"text": "Wer ist heute im Ideenmodus? Reagiere mit 🔥", "emoji": "🔥", "xp_min": 10, "xp_max": 25},
            {"text": "Sofortreaktion: Reagiere mit 📦, wenn du gern neue Produkte siehst.", "emoji": "📦", "xp_min": 10, "xp_max": 25},
            {"text": "Reagiere mit 🎁, wenn du Geschenkideen spannend findest.", "emoji": "🎁", "xp_min": 10, "xp_max": 25},
            {"text": "Kurzer Poll per Reaktion: Wer mag eher minimalistische Designs? Reagiere mit ✅", "emoji": "✅", "xp_min": 10, "xp_max": 20},
            {"text": "Wer hier ist und Ideen hat: Reagiere mit 👀", "emoji": "👀", "xp_min": 10, "xp_max": 20}
        ],
        "challenges": [
            {"text": "Challenge: Postet eine Produktidee, die ihr gern mal sehen würdet.", "xp_min": 35, "xp_max": 80},
            {"text": "Mitmach-Challenge: Was wäre euer perfektes personalisiertes Geschenk?", "xp_min": 35, "xp_max": 80},
            {"text": "Kreativ-Challenge: Beschreibt euer Wunschprodukt in einem Satz.", "xp_min": 30, "xp_max": 75},
            {"text": "Ideen-Challenge: Was würdet ihr lieber gravieren lassen?", "xp_min": 35, "xp_max": 75},
            {"text": "Challenge: Schickt eine spontane Motiv-Idee für ein neues Design.", "xp_min": 40, "xp_max": 80},
            {"text": "Mitmachrunde: Welches Material wirkt für euch am hochwertigsten?", "xp_min": 30, "xp_max": 70},
            {"text": "Challenge: Nennt ein Produkt, das man unbedingt personalisieren können sollte.", "xp_min": 35, "xp_max": 80},
            {"text": "Kleine Challenge: Welche Farbe wäre euer Favorit für ein neues Produkt?", "xp_min": 30, "xp_max": 70},
            {"text": "Ideen-Post: Wenn ihr ein Geschenk designen müsstet, wie sähe es aus?", "xp_min": 40, "xp_max": 80},
            {"text": "Mitmachen: Welche Produktidee wäre für euch sofort kaufbar?", "xp_min": 35, "xp_max": 80}
        ],
        "quizzes": [
            {"question": "Quiz: Was eignet sich oft gut für Personalisierung? A: Holz oder B: Luft", "answer": "a", "xp_min": 60, "xp_max": 120},
            {"question": "Quiz: Was ist greifbarer? A: Produktidee oder B: gar keine Idee", "answer": "a", "xp_min": 60, "xp_max": 120},
            {"question": "Quiz: Was inspiriert eher? A: Beispiele oder B: Leere", "answer": "a", "xp_min": 60, "xp_max": 120},
            {"question": "Quiz: Was bringt eher neue Produkte hervor? A: Ideen sammeln oder B: nichts notieren", "answer": "a", "xp_min": 60, "xp_max": 120},
            {"question": "Quiz: Was wirkt bei Geschenken oft stärker? A: personalisiert oder B: beliebig", "answer": "a", "xp_min": 60, "xp_max": 120},
            {"question": "Quiz: Was hilft kreativen Prozessen? A: Austausch oder B: Funkstille", "answer": "a", "xp_min": 60, "xp_max": 120},
            {"question": "Quiz: Was verkauft eher? A: gute Idee oder B: keine Richtung", "answer": "a", "xp_min": 60, "xp_max": 120},
            {"question": "Quiz: Was fällt eher auf? A: individuelles Design oder B: Standard ohne Charme", "answer": "a", "xp_min": 60, "xp_max": 120},
            {"question": "Quiz: Was bleibt eher im Kopf? A: besondere Idee oder B: langweilig", "answer": "a", "xp_min": 60, "xp_max": 120},
            {"question": "Quiz: Was hilft Produkten mehr? A: Feedback oder B: Ignoranz", "answer": "a", "xp_min": 60, "xp_max": 120}
        ]
    },
    "wupperlike": {
        "activity_prompts": [
            "Welches Wupelike-Produkt interessiert euch aktuell am meisten?",
            "Was würdet ihr gerne als Nächstes von Wupelike sehen?",
            "Welche Gravur-Idee fändet ihr richtig stark?",
            "Wenn ihr euch etwas personalisieren lassen würdet: Was wäre es?",
            "Welche Art von Produkt würdet ihr am ehesten verschenken?",
            "Welches Material wirkt für euch am hochwertigsten?",
            "Was würdet ihr eher kaufen: Deko, Geschenk oder Alltagsprodukt?",
            "Welche Produktidee passt am besten zu Wupelike?",
            "Was würdet ihr euch als neues Beispielprojekt wünschen?",
            "Was wäre euer Wunschprodukt im Wupelike-Stil?"
        ],
        "reaction_games": [
            {"text": "Wupelike-Check: Wer mag eher personalisierte Produkte? Reagiere mit 🎁", "emoji": "🎁", "xp_min": 10, "xp_max": 25},
            {"text": "Reagiere mit 🪵, wenn du Holzprodukte magst.", "emoji": "🪵", "xp_min": 10, "xp_max": 25},
            {"text": "Reagiere mit ✨, wenn du Acryl spannend findest.", "emoji": "✨", "xp_min": 10, "xp_max": 25},
            {"text": "Wer würde ein personalisiertes Geschenk kaufen? Reagiere mit ✅", "emoji": "✅", "xp_min": 10, "xp_max": 25},
            {"text": "Wer hat Lust auf neue Produktideen? Reagiere mit 💡", "emoji": "💡", "xp_min": 10, "xp_max": 25},
            {"text": "Schnell! Wer zuerst mit 🚀 reagiert, bekommt Bonus-XP.", "emoji": "🚀", "xp_min": 15, "xp_max": 30},
            {"text": "Wer würde eher etwas gravieren lassen? Reagiere mit 🔥", "emoji": "🔥", "xp_min": 10, "xp_max": 25},
            {"text": "Wer mag praktische Produkte mehr als Deko? Reagiere mit 🛠️", "emoji": "🛠️", "xp_min": 10, "xp_max": 25},
            {"text": "Wer würde Wupelike weiterempfehlen? Reagiere mit 👌", "emoji": "👌", "xp_min": 10, "xp_max": 20},
            {"text": "Wer ist für neue Beispiele und Projekte? Reagiere mit 👀", "emoji": "👀", "xp_min": 10, "xp_max": 20}
        ],
        "challenges": [
            {"text": "Challenge: Welche Produktidee würdet ihr gerne im Wupelike-Stil sehen?", "xp_min": 35, "xp_max": 80},
            {"text": "Mitmach-Challenge: Beschreibt euer perfektes personalisiertes Produkt.", "xp_min": 35, "xp_max": 80},
            {"text": "Challenge: Wenn ihr etwas für jemanden verschenken müsstet – was wäre es?", "xp_min": 35, "xp_max": 80},
            {"text": "Produkt-Challenge: Nennt eine coole Gravur-Idee.", "xp_min": 35, "xp_max": 80},
            {"text": "Mitmachen: Was wäre ein Produkt, das Wupelike unbedingt anbieten sollte?", "xp_min": 40, "xp_max": 80},
            {"text": "Challenge: Welches Material würdet ihr für ein Geschenk wählen und warum?", "xp_min": 35, "xp_max": 75},
            {"text": "Ideenrunde: Was wäre ein starkes Produkt für einen Geburtstag?", "xp_min": 35, "xp_max": 80},
            {"text": "Mitmachfrage: Welches Wupelike-Projekt würde euch direkt interessieren?", "xp_min": 35, "xp_max": 80},
            {"text": "Challenge: Nennt ein Produkt, das man unbedingt personalisiert anbieten sollte.", "xp_min": 40, "xp_max": 80},
            {"text": "Mitmachen: Was würdet ihr eher kaufen – Geschenk, Deko oder Nutzenprodukt?", "xp_min": 35, "xp_max": 75}
        ],
        "quizzes": [
            {"question": "Quiz: Was ist oft stärker? A: personalisiert oder B: beliebig", "answer": "a", "xp_min": 60, "xp_max": 120},
            {"question": "Quiz: Was bleibt eher in Erinnerung? A: individuelles Produkt oder B: Standardware", "answer": "a", "xp_min": 60, "xp_max": 120},
            {"question": "Quiz: Was wirkt hochwertiger? A: durchdachte Personalisierung oder B: lieblos", "answer": "a", "xp_min": 60, "xp_max": 120},
            {"question": "Quiz: Was macht Produkte spannender? A: eigene Idee oder B: Austauschbarkeit", "answer": "a", "xp_min": 60, "xp_max": 120},
            {"question": "Quiz: Was verkauft eher? A: Nutzen plus Persönlichkeit oder B: Zufall", "answer": "a", "xp_min": 60, "xp_max": 120},
            {"question": "Quiz: Was überzeugt eher? A: Beispiele oder B: nichts zeigen", "answer": "a", "xp_min": 60, "xp_max": 120},
            {"question": "Quiz: Was ist oft besser als Geschenk? A: personalisiert oder B: beliebig", "answer": "a", "xp_min": 60, "xp_max": 120},
            {"question": "Quiz: Was erzeugt eher Interesse? A: echte Projekte oder B: leere Kanäle", "answer": "a", "xp_min": 60, "xp_max": 120},
            {"question": "Quiz: Was hilft Kunden eher? A: Inspiration oder B: Funkstille", "answer": "a", "xp_min": 60, "xp_max": 120},
            {"question": "Quiz: Was ist für eine Marke besser? A: Aktivität oder B: tote Wirkung", "answer": "a", "xp_min": 60, "xp_max": 120}
        ]
    }
}

LEVEL_ROLE_REWARDS = {
    5: "Stammgast",
    10: "VIP",
    20: "Legende"
}

last_activity = {}
next_prompt_time = {}
active_event_claims = {}   # message_id -> winner user_id
active_quizzes = {}        # channel_id -> quiz data
user_xp_cooldown = {}      # (guild_id, user_id) -> timestamp


# ---------------------------
# DATENBANK
# ---------------------------
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

    cur.execute("""
    CREATE TABLE IF NOT EXISTS user_levels (
        guild_id INTEGER,
        user_id INTEGER,
        xp INTEGER DEFAULT 0,
        level INTEGER DEFAULT 1,
        PRIMARY KEY (guild_id, user_id)
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


def get_user_level_data(guild_id: int, user_id: int):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        SELECT xp, level
        FROM user_levels
        WHERE guild_id = ? AND user_id = ?
    """, (guild_id, user_id))
    row = cur.fetchone()

    if row is None:
        cur.execute("""
            INSERT INTO user_levels (guild_id, user_id, xp, level)
            VALUES (?, ?, 0, 1)
        """, (guild_id, user_id))
        conn.commit()
        conn.close()
        return 0, 1

    conn.close()
    return row


def add_xp(guild_id: int, user_id: int, amount: int):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        SELECT xp, level
        FROM user_levels
        WHERE guild_id = ? AND user_id = ?
    """, (guild_id, user_id))
    row = cur.fetchone()

    if row is None:
        xp = 0
        level = 1
        cur.execute("""
            INSERT INTO user_levels (guild_id, user_id, xp, level)
            VALUES (?, ?, 0, 1)
        """, (guild_id, user_id))
    else:
        xp, level = row

    xp += amount
    new_level = (xp // 100) + 1

    cur.execute("""
        UPDATE user_levels
        SET xp = ?, level = ?
        WHERE guild_id = ? AND user_id = ?
    """, (xp, new_level, guild_id, user_id))

    conn.commit()
    conn.close()

    leveled_up = new_level > level
    return xp, new_level, leveled_up


def get_leaderboard(guild_id: int, limit: int = 10):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        SELECT user_id, xp, level
        FROM user_levels
        WHERE guild_id = ?
        ORDER BY xp DESC
        LIMIT ?
    """, (guild_id, limit))
    rows = cur.fetchall()
    conn.close()
    return rows


# ---------------------------
# XP / RÄNGE
# ---------------------------
def apply_premium_bonus(guild_id: int, xp_amount: int) -> int:
    if is_premium(guild_id):
        return xp_amount * 2
    return xp_amount


async def assign_level_roles(member: discord.Member, level: int):
    reward_role_names = set(LEVEL_ROLE_REWARDS.values())
    roles_to_add = []

    for required_level, role_name in LEVEL_ROLE_REWARDS.items():
        role = discord.utils.get(member.guild.roles, name=role_name)
        if role is None:
            continue
        if level >= required_level and role not in member.roles:
            roles_to_add.append(role)

    removable_roles = [
        role for role in member.roles
        if role.name in reward_role_names and role.name not in [r.name for r in roles_to_add]
    ]

    if removable_roles:
        await member.remove_roles(*removable_roles, reason="Level-Rollen aktualisiert")

    if roles_to_add:
        await member.add_roles(*roles_to_add, reason="Level-Rolle erreicht")


def get_reward_text_for_level(level: int):
    rewards = {
        5: "🎖️ Du hast die Rolle **Stammgast** freigeschaltet!",
        10: "💎 Du hast die Rolle **VIP** freigeschaltet!",
        20: "👑 Du hast die Rolle **Legende** freigeschaltet!"
    }
    return rewards.get(level)


async def award_xp(member: discord.Member, channel: discord.abc.Messageable, xp_amount: int, reason: str = ""):
    xp_amount = apply_premium_bonus(member.guild.id, xp_amount)
    xp, level, leveled_up = add_xp(member.guild.id, member.id, xp_amount)

    if reason:
        await channel.send(f"✨ {member.mention} bekommt **{xp_amount} XP** für: {reason}")

    if leveled_up:
        await channel.send(f"🎉 {member.mention} ist jetzt Level {level}!")
        await assign_level_roles(member, level)
        reward_text = get_reward_text_for_level(level)
        if reward_text:
            await channel.send(f"{member.mention} {reward_text}")


# ---------------------------
# AKTIVITÄTS-BOOSTER
# ---------------------------
def schedule_next_prompt(channel_id: int, min_minutes: int = 45, max_minutes: int = 180):
    now = discord.utils.utcnow()
    delay = random.randint(min_minutes, max_minutes)
    next_prompt_time[channel_id] = now.timestamp() + (delay * 60)


def update_channel_activity(channel_id: int):
    now = discord.utils.utcnow()
    last_activity[channel_id] = now.timestamp()
    schedule_next_prompt(channel_id, 60, 180)


def estimated_online_members(guild: discord.Guild) -> int:
    count = 0
    for member in guild.members:
        if member.bot:
            continue
        if member.status != discord.Status.offline:
            count += 1
    return count


async def post_activity_prompt(channel: discord.TextChannel):
    prompt = random.choice(BOOSTER_CHANNELS[channel.name]["activity_prompts"])
    await channel.send(f"💬 {prompt}")


async def post_reaction_game(channel: discord.TextChannel):
    game = random.choice(BOOSTER_CHANNELS[channel.name]["reaction_games"])
    msg = await channel.send(f"🎮 {game['text']}")
    await msg.add_reaction(game["emoji"])

    xp_amount = random.randint(game["xp_min"], game["xp_max"])
    active_event_claims[msg.id] = {
        "type": "reaction",
        "emoji": game["emoji"],
        "xp": xp_amount,
        "winner": None,
        "channel_id": channel.id
    }


async def post_challenge(channel: discord.TextChannel):
    challenge = random.choice(BOOSTER_CHANNELS[channel.name]["challenges"])
    xp_amount = random.randint(challenge["xp_min"], challenge["xp_max"])
    await channel.send(
        f"🏆 **Challenge**\n{challenge['text']}\n\n"
        f"Die beste oder erste gute Antwort kann **{xp_amount} XP** bekommen."
    )


async def post_quiz(channel: discord.TextChannel):
    quiz = random.choice(BOOSTER_CHANNELS[channel.name]["quizzes"])
    xp_amount = random.randint(quiz["xp_min"], quiz["xp_max"])
    await channel.send(
        f"🧠 **Quiz**\n{quiz['question']}\n\n"
        f"Antworte einfach mit `A` oder `B`.\n"
        f"Richtige Antwort bekommt **{xp_amount} XP**."
    )

    active_quizzes[channel.id] = {
        "answer": quiz["answer"],
        "xp": xp_amount,
        "created_at": time.time(),
        "solved": False
    }


@tasks.loop(minutes=10)
async def activity_booster_loop():
    now = discord.utils.utcnow().timestamp()

    for guild in bot.guilds:
        online_count = estimated_online_members(guild)

        for channel_name in BOOSTER_CHANNELS.keys():
            channel = discord.utils.get(guild.text_channels, name=channel_name)
            if channel is None:
                continue

            channel_id = channel.id

            if channel_id not in last_activity:
                last_activity[channel_id] = now

            if channel_id not in next_prompt_time:
                schedule_next_prompt(channel_id)

            if now < next_prompt_time[channel_id]:
                continue

            inactive_for = now - last_activity[channel_id]

            # Wenn gar niemand online ist -> länger warten
            if online_count == 0:
                schedule_next_prompt(channel_id, 120, 300)
                continue

            # Phase 1: leichte Ruhe
            if inactive_for >= 60 * 60 and inactive_for < 90 * 60:
                await post_activity_prompt(channel)
                last_activity[channel_id] = discord.utils.utcnow().timestamp()
                schedule_next_prompt(channel_id, 60, 150)
                continue

            # Phase 2: längere Ruhe
            if inactive_for >= 90 * 60 and inactive_for < 180 * 60:
                await post_reaction_game(channel)
                last_activity[channel_id] = discord.utils.utcnow().timestamp()
                schedule_next_prompt(channel_id, 90, 180)
                continue

            # Phase 3: starke Ruhe
            if inactive_for >= 180 * 60:
                action_type = random.choice(["challenge", "quiz"])
                if action_type == "challenge":
                    await post_challenge(channel)
                else:
                    await post_quiz(channel)

                last_activity[channel_id] = discord.utils.utcnow().timestamp()
                schedule_next_prompt(channel_id, 180, 420)
                continue


@activity_booster_loop.before_loop
async def before_activity_booster_loop():
    await bot.wait_until_ready()


# ---------------------------
# TICKET-SYSTEM
# ---------------------------
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

        safe_name = user.name.lower().replace(" ", "-")
        ticket_name = f"ticket-{safe_name}"

        existing_channel = discord.utils.get(guild.text_channels, name=ticket_name)
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
            name=ticket_name,
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


# ---------------------------
# EVENTS
# ---------------------------
@bot.event
async def on_ready():
    init_db()
    bot.add_view(TicketView())

    if not activity_booster_loop.is_running():
        activity_booster_loop.start()

    await tree.sync()
    print(f"Eingeloggt als {bot.user}")


@bot.event
async def on_member_join(member: discord.Member):
    settings = get_guild_settings(member.guild.id)
    if settings:
        welcome_channel_id, welcome_message, _premium = settings
        if welcome_channel_id and welcome_message:
            channel = member.guild.get_channel(welcome_channel_id)
            if channel:
                msg = welcome_message.replace("{user}", member.mention).replace("{server}", member.guild.name)
                await channel.send(msg)

    role_name = "Mitglied"
    role = discord.utils.get(member.guild.roles, name=role_name)
    if role:
        await member.add_roles(role)
        print(f"{member} hat die Rolle {role_name} bekommen")
    else:
        print("Rolle nicht gefunden!")


@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    if message.guild is None:
        return

    # Aktivität tracken
    if message.channel.name in BOOSTER_CHANNELS:
        update_channel_activity(message.channel.id)

    # Quiz prüfen
    if message.channel.id in active_quizzes:
        quiz = active_quizzes[message.channel.id]
        if not quiz["solved"]:
            if time.time() - quiz["created_at"] <= 1800:  # 30 Minuten gültig
                content = message.content.strip().lower()
                if content in ["a", "b"]:
                    if content == quiz["answer"]:
                        quiz["solved"] = True
                        await award_xp(message.author, message.channel, quiz["xp"], "Quiz richtig gelöst")
                        await message.channel.send(f"✅ {message.author.mention} hat das Quiz richtig gelöst!")
                    else:
                        await message.channel.send(f"❌ {message.author.mention} leider falsch.")
            else:
                del active_quizzes[message.channel.id]

    # XP-Cooldown für normale Nachrichten
    cooldown_key = (message.guild.id, message.author.id)
    now = time.time()
    allow_normal_xp = False

    if cooldown_key not in user_xp_cooldown:
        allow_normal_xp = True
    elif now - user_xp_cooldown[cooldown_key] >= 30:
        allow_normal_xp = True

    if allow_normal_xp:
        user_xp_cooldown[cooldown_key] = now
        xp_gain = apply_premium_bonus(message.guild.id, 10)
        xp, level, leveled_up = add_xp(message.guild.id, message.author.id, xp_gain)

        if leveled_up:
            await message.channel.send(f"🎉 {message.author.mention} ist jetzt Level {level}!")
            await assign_level_roles(message.author, level)
            reward_text = get_reward_text_for_level(level)
            if reward_text:
                await message.channel.send(f"{message.author.mention} {reward_text}")

    await bot.process_commands(message)


@bot.event
async def on_reaction_add(reaction: discord.Reaction, user: discord.User):
    if user.bot:
        return

    message = reaction.message
    if message.id not in active_event_claims:
        return

    event = active_event_claims[message.id]
    if event["type"] != "reaction":
        return

    if str(reaction.emoji) != event["emoji"]:
        return

    if event["winner"] is not None:
        return

    if not isinstance(user, discord.Member):
        if message.guild:
            member = message.guild.get_member(user.id)
        else:
            member = None
    else:
        member = user

    if member is None:
        return

    event["winner"] = member.id
    await award_xp(member, message.channel, event["xp"], "Reaktionsspiel gewonnen")
    await message.channel.send(f"🏁 {member.mention} war am schnellsten und gewinnt!")
    del active_event_claims[message.id]


# ---------------------------
# COMMANDS
# ---------------------------
@tree.command(name="setup_welcome", description="Setzt den Willkommenskanal und die Nachricht.")
@app_commands.checks.has_permissions(administrator=True)
async def setup_welcome(interaction: discord.Interaction, channel: discord.TextChannel, message: str):
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
        await interaction.response.send_message("Diese Funktion ist Premium.", ephemeral=True)
        return

    if interaction.channel is None:
        await interaction.response.send_message("Kanal nicht gefunden.", ephemeral=True)
        return

    await interaction.channel.send(f"📢 {text}")
    await interaction.response.send_message("Ankündigung gesendet.", ephemeral=True)


@tree.command(name="ticket_panel", description="Erstellt ein Ticket-Panel.")
@app_commands.checks.has_permissions(administrator=True)
async def ticket_panel(interaction: discord.Interaction):
    if interaction.guild is None:
        await interaction.response.send_message("Das geht nur in einem Server.", ephemeral=True)
        return

    if not is_premium(interaction.guild.id):
        await interaction.response.send_message(
            "Das Ticket-System ist nur für Premium-Server verfügbar.",
            ephemeral=True
        )
        return

    if interaction.channel is None:
        await interaction.response.send_message("Kanal nicht gefunden.", ephemeral=True)
        return

    embed = discord.Embed(
        title="Support Tickets",
        description="Klicke auf den Button unten, um ein Ticket zu erstellen."
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
    if interaction.guild is None:
        await interaction.response.send_message("Das geht nur in einem Server.", ephemeral=True)
        return

    if not is_premium(interaction.guild.id):
        await interaction.response.send_message(
            "Diese Funktion ist nur für Premium-Server verfügbar.",
            ephemeral=True
        )
        return

    if interaction.channel is None:
        await interaction.response.send_message("Kanal nicht gefunden.", ephemeral=True)
        return

    await interaction.response.send_message(f"Lösche {anzahl} Nachrichten...", ephemeral=True)
    await interaction.channel.purge(limit=anzahl)


@tree.command(name="premium_on", description="Aktiviert Premium für diesen Server.")
@app_commands.checks.has_permissions(administrator=True)
async def premium_on(interaction: discord.Interaction):
    if interaction.guild is None:
        await interaction.response.send_message("Das geht nur in einem Server.", ephemeral=True)
        return

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO guild_settings (guild_id, premium_enabled)
        VALUES (?, 1)
        ON CONFLICT(guild_id) DO UPDATE SET premium_enabled=1
    """, (interaction.guild.id,))
    conn.commit()
    conn.close()

    await interaction.response.send_message("Premium wurde aktiviert.", ephemeral=True)


@tree.command(name="premium_off", description="Deaktiviert Premium für diesen Server.")
@app_commands.checks.has_permissions(administrator=True)
async def premium_off(interaction: discord.Interaction):
    if interaction.guild is None:
        await interaction.response.send_message("Das geht nur in einem Server.", ephemeral=True)
        return

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO guild_settings (guild_id, premium_enabled)
        VALUES (?, 0)
        ON CONFLICT(guild_id) DO UPDATE SET premium_enabled=0
    """, (interaction.guild.id,))
    conn.commit()
    conn.close()

    await interaction.response.send_message("Premium wurde deaktiviert.", ephemeral=True)


@tree.command(name="level", description="Zeigt dein aktuelles Level und deine Punkte.")
async def level(interaction: discord.Interaction):
    if interaction.guild is None:
        await interaction.response.send_message(
            "Dieser Befehl funktioniert nur in einem Server.",
            ephemeral=True
        )
        return

    xp, lvl = get_user_level_data(interaction.guild.id, interaction.user.id)
    await interaction.response.send_message(
        f"Du bist Level {lvl} und hast {xp} Punkte.",
        ephemeral=True
    )


@tree.command(name="leaderboard", description="Zeigt die Top 10 des Servers.")
async def leaderboard(interaction: discord.Interaction):
    if interaction.guild is None:
        await interaction.response.send_message(
            "Dieser Befehl funktioniert nur in einem Server.",
            ephemeral=True
        )
        return

    rows = get_leaderboard(interaction.guild.id, 10)

    if not rows:
        await interaction.response.send_message("Es gibt noch keine Leveldaten.", ephemeral=True)
        return

    text = ""
    for index, (user_id, xp, lvl) in enumerate(rows, start=1):
        member = interaction.guild.get_member(user_id)
        name = member.display_name if member else f"User {user_id}"
        text += f"{index}. {name} — Level {lvl} ({xp} Punkte)\n"

    embed = discord.Embed(title="🏆 Leaderboard", description=text)
    await interaction.response.send_message(embed=embed)


@tree.command(name="rank_rewards", description="Zeigt die Level-Belohnungen.")
async def rank_rewards(interaction: discord.Interaction):
    text = (
        "🎁 **Level-Belohnungen**\n\n"
        "Level 5 → Stammgast\n"
        "Level 10 → VIP\n"
        "Level 20 → Legende\n\n"
        "💎 Premium-Server erhalten doppelte XP."
    )
    await interaction.response.send_message(text, ephemeral=True)


# ---------------------------
# FEHLERBEHANDLUNG
# ---------------------------
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
