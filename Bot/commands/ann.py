import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

load_dotenv()

ANNOUNCEMENTS_ID = int(os.getenv('ANNOUNCEMENTS_ID'))

async def setup(bot, create_connection, AUTHORIZED_USER_IDS):
    @bot.command()
    async def ann(ctx, *, announcement_text):
        try:
            if ctx.author.id not in AUTHORIZED_USER_IDS:
                message = "You don't have permission to use this command."
                embed = discord.Embed(description=message, color=discord.Color.red())
                await ctx.send(embed=embed)
                return

            announcement_channel = bot.get_channel(ANNOUNCEMENTS_ID)

            if not announcement_channel:
                await ctx.send("Announcements channel not found.")
                return

            
            embed = discord.Embed(
                description=f"**Author: {ctx.author.mention}**\n\n**{announcement_text}**", 
                color=discord.Color.purple()
            )

            
            await announcement_channel.send(content="@everyone", embed=embed)

            success_message = f"**Announcement posted in {announcement_channel.mention}**"
            embed_success = discord.Embed(description=success_message, color=discord.Color.green())
            await ctx.send(embed=embed_success)

        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")

