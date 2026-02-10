import discord
from discord.ext import commands
import os
import sys
import random
import asyncio
from dotenv import load_dotenv

# Add scripts/comfy to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'comfy'))
from comfy_client import ComfyClient

# === SETUP ===
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, "config", ".env"))

TOKEN = os.getenv("DISCORD_TOKEN")
COMFY_URL = os.getenv("COMFY_URL", "127.0.0.1:8188") # Add to .env if remote

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
comfy = ComfyClient(server_address=COMFY_URL)

# === STATE ===
WORKFLOW_PATH = os.path.join(BASE_DIR, "workflows", "masterpiece.json")
STYLES = {
    "anime": "masterpiece, best quality, anime style, cel shaded",
    "photo": "masterpiece, best quality, realistic, photorealistic, 8k",
    "oil": "masterpiece, best quality, oil painting, impasto, textured",
    "manga": "masterpiece, best quality, monochrome, manga style, ink lines"
}

# === EVENTS ===
@bot.event
async def on_ready():
    print(f'✨ Lady Nuggets Orchestrator Online as {bot.user}')
    print(f'🔌 Connecting to ComfyUI at {COMFY_URL}...')
    if comfy.connect():
        print("✅ ComfyUI Connected")
    else:
        print("⚠️ ComfyUI NOT Connected (Make sure it's running)")

@bot.event
async def on_member_join(member):
    """Community: Welcome Message"""
    channel = discord.utils.get(member.guild.text_channels, name="general")
    if channel:
        await channel.send(f"Welcome to the Harem, {member.mention}! 💖\nType `!help` to start generating.")
    
    # Auto-Role (Novice)
    role = discord.utils.get(member.guild.roles, name="Novice")
    if role:
        await member.add_roles(role)

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    
    # Moderation: Bad Words
    bad_words = ["shota", "loli", "rape"] # Basic safety filter
    if any(word in message.content.lower() for word in bad_words):
        await message.delete()
        await message.channel.send(f"⚠️ {message.author.mention}, that language is not allowed here.", delete_after=5)
        return

    # XP System (Mockup)
    # in real DB we would increment user XP here
    
    await bot.process_commands(message)

# === COMMANDS ===

@bot.command()
async def gen(ctx, *, prompt: str):
    """Generate an image using ComfyUI"""
    status_msg = await ctx.send(f"🎨 **Generating:** `{prompt}`\nWait a moment...")
    
    # Prepare Prompt
    # Inject style if specified (simple logic for now)
    final_prompt = prompt
    
    # Run Generation (Blocking for now, should be async in prod)
    # We run in executor to not block bot loop
    def run_comfy():
        return comfy.generate(
            WORKFLOW_PATH, 
            final_prompt, 
            negative_prompt="(worst quality, low quality:1.4)",
            output_dir=os.path.join(BASE_DIR, "content", "comfy_out")
        )
    
    try:
        loop = asyncio.get_event_loop()
        files = await loop.run_in_executor(None, run_comfy)
        
        if files:
            discord_files = [discord.File(f) for f in files]
            await ctx.send(f"{ctx.author.mention} Here is your creation! ✨", files=discord_files)
            await status_msg.delete()
        else:
            await status_msg.edit(content="❌ Generation failed. Is ComfyUI running?")
            
    except Exception as e:
        await status_msg.edit(content=f"❌ Error: {e}")

@bot.command()
async def styles(ctx):
    """List available styles"""
    msg = "**🎭 Available Styles:**\n"
    for s in STYLES:
        msg += f"`{s}`\n"
    await ctx.send(msg)

@bot.command()
async def story(ctx, *, theme: str):
    """(Stub) Create a story and generate images"""
    await ctx.send(f"📝 Writing a story about `{theme}` using DeepSeek R1... (Coming Soon)")

if __name__ == "__main__":
    if not TOKEN:
        print("❌ Error: DISCORD_TOKEN not found in .env")
    else:
        bot.run(TOKEN)
