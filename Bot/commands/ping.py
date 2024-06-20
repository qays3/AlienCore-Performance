import discord
from discord.ext import commands

async def setup(bot, create_connection, AUTHORIZED_USER_IDS):
    @bot.command()
    async def ping(ctx):
        latency = bot.latency * 1000  
        
        
        embed = discord.Embed(
            title="Pong!",
            description=f"Latency: {latency:.2f}ms",
            color=discord.Color.purple()
        )
        
        await ctx.send(embed=embed)
