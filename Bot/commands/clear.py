import discord
from discord.ext import commands

async def setup(bot, create_connection, AUTHORIZED_USER_IDS):
    @bot.command()
    async def clear(ctx, num_messages: int):
        try:
            if ctx.author.id not in AUTHORIZED_USER_IDS:
                message = "**You don't have permission to use this command.**"
                embed = discord.Embed(description=message, color=0xFF0000)
                await ctx.send(embed=embed)
                return

            if not ctx.channel.permissions_for(ctx.me).manage_messages:
                message = "**I don't have permission to delete messages in this channel.**"
                embed = discord.Embed(description=message, color=0xFF0000)
                await ctx.send(embed=embed)
                return

            if num_messages <= 0:
                message = "**Please specify a number greater than 0.**"
                embed = discord.Embed(description=message, color=0xFF0000)
                await ctx.send(embed=embed)
                return

            deleted = await ctx.channel.purge(limit=num_messages + 1)   
            message = f"**Deleted {len(deleted) - 1} messages.**"   
            embed = discord.Embed(description=message, color=0x18bd06)
            await ctx.send(embed=embed, delete_after=5)

        except discord.Forbidden:
            message = "**I don't have permission to delete messages.**"
            embed = discord.Embed(description=message, color=0xFF0000)
            await ctx.send(embed=embed)
        except discord.HTTPException as e:
            message = f"**Failed to delete messages: {str(e)}**"
            embed = discord.Embed(description=message, color=0xFF0000)
            await ctx.send(embed=embed)
