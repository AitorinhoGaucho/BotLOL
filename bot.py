import discord
from discord.ext import commands
import os
from flask import Flask
from threading import Thread
import requests
import datetime

TOKEN = os.getenv("DISCORD_TOKEN")
PANDASCORE_TOKEN = os.getenv("PANDASCORE_TOKEN")
# Configura el servidor web para mantener el bot despierto
app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# Configura el bot de Discord
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Diccionario de los tiers de las ligas
LEAGUE_TIERS = {
    "s": 1,
    "a": 2,
    "b": 3,
    "c": 4,
    "d": 5,
    "e": 6,
    "f": 7
}

def get_lol_matches_today(api_token):
    today = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d')
    url = f"https://api.pandascore.co/lol/matches?filter[begin_at]={today}&per_page=100"
    headers = {"Authorization": f"Bearer {api_token}"}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        matches = response.json()
        leagues = {}

        if matches:
            for match in matches:
                league_name = match['league']['name']
                league_tier = match['tournament'].get('tier', 'f').lower()  # Obtener el tier de la liga
                team1 = match['opponents'][0]['opponent']['name'] if match['opponents'] else "Unknown"
                team2 = match['opponents'][1]['opponent']['name'] if len(match['opponents']) > 1 else "Unknown"

                max_position = max(game['position'] for game in match['games']) if match['games'] else 1
                bo_format = f"BO{max_position}"

                if league_name not in leagues:
                    leagues[league_name] = {"tier": LEAGUE_TIERS.get(league_tier, 7), "games": []}
                leagues[league_name]["games"].append(f"{team1} vs {team2} ({bo_format})")

            # Ordenar las ligas por su tier (de mayor a menor)
            sorted_leagues = sorted(leagues.items(), key=lambda x: x[1]['tier'])

            result_message = ""
            for league, data in sorted_leagues:
                result_message += f"{league} ({[tier for tier, num in LEAGUE_TIERS.items() if num == data['tier']][0]} tier):\n"
                for game in data['games']:
                    result_message += f"{game}\n"
                result_message += "\n"

            return result_message if result_message else "No hay partidos programados para hoy."
        else:
            return "No hay partidos programados para hoy."
    else:
        return f"Error en la solicitud: {response.status_code} - {response.text}"

# Evento cuando el bot está listo
@bot.event
async def on_ready():
    print(f'Bot {bot.user.name} está listo!')

# Comando simple
@bot.command()
async def hola(ctx):
    await ctx.send('Hola!')

# Comando para sumar dos números
@bot.command()
async def sumar(ctx, num1: int, num2: int):
    resultado = num1 + num2
    await ctx.send(f'El resultado es: {resultado}')

# Comando para obtener los partidos de LoL
@bot.command()
async def partidos(ctx):
    partidos_hoy = get_lol_matches_today(PANDASCORE_TOKEN)
    await ctx.send(partidos_hoy)

# Inicia el servidor web y el bot
keep_alive()
bot.run(TOKEN)