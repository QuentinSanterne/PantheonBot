import os
import discord
import asyncio
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timezone, timedelta, time
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('BOT_TOKEN')
intents = discord.Intents.default()

bot = commands.Bot(command_prefix='!', intents=intents)

# Variables

GUILD_ID = 954437554810257468
GRUMPY1 = time(15, 3, 0)
GRUMPY2 = time(15, 5, 0)

# Event

@bot.event
async def on_ready():
    bot.loop.create_task(background_grumpy())
    synced = await bot.tree.sync()
    print(f"Synced {len(synced)} command(s)")
    print(f'{bot.user.name} est connecté à discord!')

# Commandes

@bot.command(name="ping", help="Ping pong basique")
async def ping(ctx):
    await ctx.send("Pong!")

# Slash Commands

@bot.tree.command(name="ping", description="Renvoie Pong !")
async def ping(interaction):
    await interaction.response.send_message("Pong !")

## Message get-role

@bot.tree.command(name="autorole", description="Écris le message à réagir pour obtenir un role")
@app_commands.checks.has_role("LoM_admin")
async def autorole(interaction, role: discord.Role, message: str):
    channel = interaction.channel
    msg = f">>>Pour obtenir le rôle {role.mention}, réagissez avec ✅ \n\n"
    msg += message 
    await channel.send(msg)
    await channel.last_message.add_reaction("✅")
    await interaction.response.send_message("Done", ephemeral=True)

## Purge nb message

@bot.tree.command(name="purge", description="Supprimer les x derniers messages du salon")
@app_commands.checks.has_role("LoM_admin")
async def purge(interaction, number: int):
    await interaction.response.defer(ephemeral=True)
    channel = interaction.channel
    messages = []
    async for message in channel.history(limit=number):
        messages.append(message)
    await channel.delete_messages(messages)
    await interaction.followup.send(f"{number} messages supprimés", ephemeral=True)


## Purge les messages de la journée

@bot.tree.command(name="purgeold", description="Supprimer les messages envoyés dans les dernières 20h")
@app_commands.checks.has_role("LoM_admin")
async def purgeold(interaction):
    await interaction.response.defer(ephemeral=True)
    channel = interaction.channel
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=20)
    messages = []
    async for message in channel.history(after=cutoff):
        messages.append(message)
    await channel.delete_messages(messages)
    await interaction.followup.send(f"Messages de la journée supprimés", ephemeral=True)

## Alerte parking

@bot.tree.command(name="parking", description="Ping le rôle LoM_Parking dans le salon #Parking")
@app_commands.checks.has_role("LoM_Parking")
async def parking(interaction, num_parking: int, num_serveur: int, délai: int = 0, garnison: int = 0):
    role = bot.get_guild(GUILD_ID).get_role(954447331653193808) # Rôle "LoM_Parking"
    channel = bot.get_guild(GUILD_ID).get_channel(1248571403314266183) # Salon "#Parking"

    if role is None or channel is None:
        await interaction.response.send_message("Erreur : rôle ou salon introuvable")
        return

    message = f"Attaque Parking {num_parking} sur le serveur {num_serveur} "
    if délai > 0:
        message += f"dans {délai} min"
    if garnison > 0:
        message += f", {garnison} joueurs en garnison"
    await channel.send(f"{message} {role.mention}")
    await interaction.response.send_message("Done", ephemeral=True)

# Tâches

async def ping_grumpy():
    await bot.wait_until_ready()
    role = bot.get_guild(GUILD_ID).get_role(1264265938446848043)  # Rôle "LoM_Grumpy"
    channel = bot.get_guild(GUILD_ID).get_channel(1248571403314266183)  # Salon "#Grumpy"
    await channel.send(f"{role.mention} Grumpy dans 5min, pensez à vous inscrire")

async def background_grumpy():
    now = datetime.now(timezone.utc)
    if now.time() > GRUMPY2:  # Make sure loop doesn't start after {GRUMPY2} as then it will send immediately the first time as negative seconds will make the sleep yield instantly
        tomorrow = datetime.combine(datetime.now() + timedelta(days=1), time(0))
        seconds = (tomorrow - now).total_seconds()  # Seconds until tomorrow (midnight)
        await asyncio.sleep(seconds)  # Sleep until tomorrow and then the loop will start 
    
    while True:
        now = datetime.now(timezone.utc)
        target_time = datetime.combine(datetime.now(), GRUMPY1)  # Grumpy 12h05 - 5min
        seconds_until_target = (target_time - now.replace(tzinfo=None)).total_seconds()
        await asyncio.sleep(seconds_until_target)  # Sleep until we hit the target time
        await ping_grumpy()  # Envoie le message de ping
        
        now = datetime.now(timezone.utc)
        target_time = datetime.combine(datetime.now(), GRUMPY2)  # Grumpy 19h15 - 5min
        seconds_until_target = (target_time - now.replace(tzinfo=None)).total_seconds()
        await asyncio.sleep(seconds_until_target)  # Sleep until we hit the target time
        await ping_grumpy()  # Envoie le message de ping
        
        tomorrow = datetime.combine(datetime.now() + timedelta(days=1), time(0))
        seconds = (tomorrow - now.replace(tzinfo=None)).total_seconds()  # Seconds until tomorrow (midnight)
        await asyncio.sleep(seconds)  # Sleep until tomorrow and then the loop will start a new iteration


if __name__ == "__main__":

    bot.run(TOKEN)
		