import discord
from discord.ext import commands
import aiomysql
import logging
from datetime import datetime

FIRST_PLACE_EMOJI = ":first_place:"
SECOND_PLACE_EMOJI = ":second_place:"
THIRD_PLACE_EMOJI = ":third_place:"

async def setup(bot, create_connection, AUTHORIZED_USER_IDS):
    @bot.command()
    async def rank(ctx):
        try:
            connection = await create_connection()

            if not connection:
                await ctx.send("Database connection failed.")
                return

            async with connection.cursor() as cursor:
                query = "SELECT p.discord_id, p.score " \
                        "FROM Participants p " \
                        "ORDER BY p.score DESC " \
                        "LIMIT 10"
                await cursor.execute(query)
                results = await cursor.fetchall()

                if not results:
                    embed = discord.Embed(description="No participants found.", color=discord.Color.red())
                    await ctx.send(embed=embed)
                    return

                rank_embed = discord.Embed(title="Top 10 Participants", color=discord.Color.gold())
                rank = 1

                for result in results:
                    discord_id = result['discord_id']
                    total_score = result['score']

                    try:
                        user = await bot.fetch_user(discord_id)
                        user_mention = user.mention
                        rank_str = f"{get_rank_emoji(rank)} **Rank {rank}:** {user_mention} - **Total Score:** {total_score}"
                        rank_embed.add_field(name="\u200b", value=rank_str, inline=False)
                        rank += 1
                    except discord.errors.NotFound:
                        logging.warning(f"User not found for discord_id: {discord_id}")
                    except Exception as e:
                        logging.error(f"Error fetching user: {str(e)}")

                    if rank > 10:  
                        break

                await ctx.send(embed=rank_embed)

        except aiomysql.Error as e:
            logging.error(f"Database error: {str(e)}")
            await ctx.send(f"Database error: {str(e)}")
        except Exception as e:
            logging.error(f"Unexpected error: {str(e)}")
            await ctx.send(f"Unexpected error: {str(e)}")
        finally:
            try:
                if connection:
                    await connection.ensure_closed()
            except Exception as e:
                logging.error(f"Error closing the database connection: {str(e)}")
                await ctx.send(f"Error closing the database connection: {str(e)}")

def get_rank_emoji(rank):
    if rank == 1:
        return FIRST_PLACE_EMOJI
    elif rank == 2:
        return SECOND_PLACE_EMOJI
    elif rank == 3:
        return THIRD_PLACE_EMOJI
    else:
        return ":medal:"   
