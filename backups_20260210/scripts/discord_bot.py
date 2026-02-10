import discord
from discord.ext import commands
import os
import sqlite3
import random
import time
from pathlib import Path
from dotenv import load_dotenv

# LOAD ENV
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, "config", ".env"))

# CONFIG
TOKEN = os.getenv("DISCORD_TOKEN")
DB_PATH = os.path.join(BASE_DIR, "database", "users.db")
CONTENT_DIR = os.path.join(BASE_DIR, "content")

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
gacha_cooldown = {}

# SETUP DB
def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute('''CREATE TABLE IF NOT EXISTS inventory
                 (user_id INTEGER, waifu_id TEXT, rarity TEXT, obtained_at TIMESTAMP)''')
    conn.close()

init_db()

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

# === GACHA SYSTEM ===
@bot.command()
async def roll(ctx):
    user_id = ctx.author.id
    
    # Cooldown (6h = 21600s)
    if user_id in gacha_cooldown:
        last = gacha_cooldown[user_id]
        if time.time() - last < 21600:
            wait = 21600 - (time.time() - last)
            hours, minutes = int(wait // 3600), int((wait % 3600) // 60)
            await ctx.send(f"⏳ Please wait {hours}h {minutes}m for your next roll.")
            return

    # Rarity Logic
    roll = random.randint(1, 100)
    if roll <= 5:
        rarity = "legendary"
        color = 0xFFD700
    elif roll <= 30:
        rarity = "rare"
        color = 0x9B59B6
    else:
        rarity = "common"
        color = 0x95A5A6
        
    # Pick Image
    # Note: Expects folders content/gacha/legendary, etc.
    # Fallback to curated if gacha folders empty
    folder = os.path.join(CONTENT_DIR, "gacha", rarity)
    if not os.path.exists(folder):
        # Fallback mapping
        fallback_map = {"legendary": "premium", "rare": "standard", "common": "standard"}
        folder = os.path.join(CONTENT_DIR, "curated", fallback_map[rarity])
    
    files = [f for f in os.listdir(folder) if f.endswith(".png")] if os.path.exists(folder) else []
    
    if not files:
        await ctx.send("Gacha machine is empty! Contact Admin.")
        return
        
    waifu = random.choice(files)
    waifu_path = os.path.join(folder, waifu)
    
    # Save to Inventory
    conn = sqlite3.connect(DB_PATH)
    conn.execute("INSERT INTO inventory (user_id, waifu_id, rarity, obtained_at) VALUES (?, ?, ?, ?)",
                 (user_id, waifu, rarity, datetime.now()))
    conn.commit()
    conn.close()
    
    # Send Embed
    file = discord.File(waifu_path, filename=waifu)
    embed = discord.Embed(title=f"✨ You pulled a {rarity.upper()} Waifu!", color=color)
    embed.set_image(url=f"attachment://{waifu}")
    embed.set_footer(text=f"Waifu: {waifu}")
    
    await ctx.send(embed=embed, file=file)
    gacha_cooldown[user_id] = time.time()

# === INVENTORY ===
@bot.command()
async def inventory(ctx):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    rows = cursor.execute("SELECT rarity, COUNT(*) FROM inventory WHERE user_id=? GROUP BY rarity", (ctx.author.id,)).fetchall()
    conn.close()
    
    if not rows:
        await ctx.send("Your inventory is empty. Try `!roll`!")
        return
        
    msg = "**🎒 Your Collection:**\n"
    for rarity, count in rows:
        emoji = "🟡" if rarity == "legendary" else "🟣" if rarity == "rare" else "⚪"
        msg += f"{emoji} **{rarity.title()}**: {count}\n"
        
    await ctx.send(msg)

if __name__ == "__main__":
    if not TOKEN:
        print("Error: DISCORD_TOKEN not found.")
    else:
        bot.run(TOKEN)
