import os
import discord
import asyncio
import re
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timezone, timedelta, time
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('BOT_TOKEN')
intents = discord.Intents.default()
intents.members = True
intents.messages = True
intents.presences = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Variables

GUILD_TEST = os.getenv('GUILD_TEST')
ROLE_TEST = os.getenv('ROLE_TEST')
GRUMPY_TEST = os.getenv('GRUMPY_TEST')
SALON_TEST = os.getenv('SALON_TEST')
GRUMPY1 = time(10, 0, 0)
GRUMPY2 = time(17, 15, 0)

# Event

@bot.event
async def on_ready():
    bot.loop.create_task(background_grumpy())
    synced = await bot.tree.sync()
    print(f"Synced {len(synced)} command(s)")
    print(f'{bot.user.name} est connecté à discord!')

@bot.event
async def on_raw_reaction_add(payload):
    # Vérifier si la réaction est une réaction que le bot doit traiter
    guild_id = payload.guild_id
    guild = discord.utils.get(bot.guilds, id=guild_id)
    user = discord.utils.get(guild.members, id=payload.user_id)
    if str(payload.emoji) == "✅" and bot.user != user:
        # Récupérer le message et l'utilisateur qui a ajouté la réaction
        channel = bot.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        # Traitement de la réaction
        await on_reaction_add(message, user)

@bot.event
async def on_raw_reaction_remove(payload):
    # Vérifier si la réaction est une réaction que le bot doit traiter
    guild_id = payload.guild_id
    guild = discord.utils.get(bot.guilds, id=guild_id)
    user = discord.utils.get(guild.members, id=payload.user_id)
    if str(payload.emoji) == "✅" and bot.user != user:
        # Récupérer le message et l'utilisateur qui a enlevé la réaction
        channel = bot.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        # Traitement de la réaction
        await on_reaction_remove(message, user)

async def on_reaction_add(message, user):
        # Récupère le rôle mentionné dans le message
        role_id = None
        for line in message.content.splitlines():
            if line.startswith(">>> Pour obtenir le rôle "):
                # Extraire l'ID du rôle à partir de la mention du rôle
                match = re.search(r'<@&(\d+)>', line)
                if match:
                    role_id = int(match.group(1))
                    break
        # Si un rôle est trouvé, assigne-le à l'utilisateur
        if role_id:
            role = discord.utils.get(message.guild.roles, id=role_id)
            if role:
                await user.add_roles(role)
                await message.channel.send(f"{user.mention} a obtenu le rôle {role.mention}", delete_after=3)

async def on_reaction_remove(message, user):
        # Récupère le rôle mentionné dans le message
        role_id = None
        for line in message.content.splitlines():
            if line.startswith(">>> Pour obtenir le rôle "):
                # Extraire l'ID du rôle à partir de la mention du rôle
                match = re.search(r'<@&(\d+)>', line)
                if match:
                    role_id = int(match.group(1))
                    break
        # Si un rôle est trouvé, assigne-le à l'utilisateur
        if role_id:
            role = discord.utils.get(message.guild.roles, id=role_id)
            if role:
                await user.remove_roles(role)
                await message.channel.send(f"{user.mention} n'a plus le rôle {role.mention}", delete_after=3)

# Commands

# Slash Commands

@bot.tree.command(name="ping", description="Renvoie Pong !")
async def ping(interaction):
    await interaction.response.send_message("Pong !")

## Message get-role

@bot.tree.command(name="autorole", description="Écris le message à réagir pour obtenir un role")
#@app_commands.checks.has_role("LoM_admin")
async def autorole(interaction, role: discord.Role, message: str):
    channel = interaction.channel
    msg = f">>> Pour obtenir le rôle {role.mention}, réagissez avec ✅ \n\n"
    msg += message 
    msg_sent= await channel.send(msg)
    await msg_sent.add_reaction("✅")
    await interaction.response.send_message("Done", ephemeral=True, delete_after=10)

## Purge nb message

@bot.tree.command(name="purge", description="Supprimer les x derniers messages du salon")
#@app_commands.checks.has_role("LoM_admin")
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
#@app_commands.checks.has_role("LoM_admin")
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
@app_commands.checks.has_role("Ouais")
async def parking(interaction, num_parking: int, num_serveur: int, délai: int = 0, garnison: int = 0):
    role = bot.get_guild(GUILD_TEST).get_role(ROLE_TEST) # Rôle "LoM_Parking"
    channel = bot.get_guild(GUILD_TEST).get_channel(SALON_TEST) # Salon "#Parking"

    if role is None or channel is None:
        await interaction.response.send_message("Erreur : rôle ou salon introuvable")
        return

    message = f"Attaque Parking {num_parking} sur le serveur {num_serveur} "
    if délai > 0:
        message += f"dans {délai} min"
    if garnison > 0:
        message += f", {garnison} joueurs en garnison"
    await channel.send(f"{message} {role.mention}")
    await interaction.response.send_message("Done", ephemeral=True, delete_after=2)

# Tâches

async def ping_grumpy():
    await bot.wait_until_ready()
    role = bot.get_guild(GUILD_TEST).get_role(GRUMPY_TEST)  # Rôle "LoM_Grumpy"
    channel = bot.get_guild(GUILD_TEST).get_channel(SALON_TEST)  # Salon "#Grumpy"
    await channel.send(f"{role.mention} Grumpy dans 5min, pensez à vous inscrire")

async def background_grumpy():
    now = datetime.now(timezone.utc)
    if now.time() > GRUMPY2:  # Make sure loop doesn't start after {GRUMPY2} as then it will send immediately the first time as negative seconds will make the sleep yield instantly
        tomorrow = datetime.combine(datetime.now() + timedelta(days=1), time(0))
        seconds = (tomorrow - now.replace(tzinfo=None)).total_seconds()  # Seconds until tomorrow (midnight)
        await asyncio.sleep(seconds)  # Sleep until tomorrow and then the loop will start 
    
    while True:
        now = datetime.now(timezone.utc)
        target_time = datetime.combine(datetime.now(), GRUMPY1)  # Grumpy 12h05 - 5min
        seconds_until_target = (target_time - now.replace(tzinfo=None)).total_seconds()
        if seconds_until_target > 0:
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
		