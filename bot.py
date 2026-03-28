import os
import discord
from discord.ext import commands
import random

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'Bot conectado como {bot.user}')

@bot.command()
async def hola(ctx):
    await ctx.send("Hola po 😎 soy tu bot")

ejercicios = {
    "basico": [
        "Haz un programa que muestre los números del 1 al 10",
        "Pide un número y muestra si es positivo o negativo",
        "Pide 3 números y muestra el mayor"
    ],
    "ciclos": [
        "Usa un ciclo para mostrar del 1 al 10",
        "Cuenta regresiva del 10 al 1",
        "Suma números hasta que el usuario diga 0"
    ]
}

@bot.command()
async def ejercicio(ctx, tema="basico"):
    if tema not in ejercicios:
        await ctx.send("Ese tema no existe 😐")
        return
    
    ejercicio_random = random.choice(ejercicios[tema])
    await ctx.send(f"🧠 Ejercicio ({tema}):\n👉 {ejercicio_random}")

bot.run(os.getenv("DISCORD_TOKEN"))