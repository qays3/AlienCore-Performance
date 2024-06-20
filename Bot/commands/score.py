import discord
from discord.ext import commands
import aiomysql
import logging
from datetime import datetime, timedelta

FIRST_PLACE_EMOJI = ":first_place:"
SECOND_PLACE_EMOJI = ":second_place:"
THIRD_PLACE_EMOJI = ":third_place:"

async def setup(bot, create_connection, AUTHORIZED_USER_IDS):
    @bot.command()
    async def score(ctx, period: str):
        try:
            connection = await create_connection()

            if not connection:
                await ctx.send("Database connection failed.")
                return

            async with connection.cursor() as cursor:
                current_date = datetime.now()
                
                if period.lower() == 'w':  
                    start_of_week = current_date - timedelta(days=current_date.weekday())
                    end_of_week = start_of_week + timedelta(days=6)
                    query = "SELECT p.discord_id, SUM(e.score) AS total_score " \
                            "FROM Participants p " \
                            "LEFT JOIN Evaluations e ON p.id = e.participant_id " \
                            "WHERE e.evaluated_at BETWEEN %s AND %s " \
                            "GROUP BY p.id " \
                            "ORDER BY total_score DESC"
                    await cursor.execute(query, (start_of_week, end_of_week))
                    period_str = "Week"

                elif period.lower() == 'm':  
                    start_of_month = current_date.replace(day=1)
                    end_of_month = start_of_month.replace(month=start_of_month.month % 12 + 1, day=1) - timedelta(days=1)
                    query = "SELECT p.discord_id, SUM(e.score) AS total_score " \
                            "FROM Participants p " \
                            "LEFT JOIN Evaluations e ON p.id = e.participant_id " \
                            "WHERE e.evaluated_at BETWEEN %s AND %s " \
                            "GROUP BY p.id " \
                            "ORDER BY total_score DESC"
                    await cursor.execute(query, (start_of_month, end_of_month))
                    period_str = "Month"

                elif period.lower() == 'y':  
                    start_of_year = current_date.replace(month=1, day=1)
                    end_of_year = start_of_year.replace(year=start_of_year.year + 1, month=1, day=1) - timedelta(days=1)
                    query = "SELECT p.discord_id, SUM(e.score) AS total_score " \
                            "FROM Participants p " \
                            "LEFT JOIN Evaluations e ON p.id = e.participant_id " \
                            "WHERE e.evaluated_at BETWEEN %s AND %s " \
                            "GROUP BY p.id " \
                            "ORDER BY total_score DESC"
                    await cursor.execute(query, (start_of_year, end_of_year))
                    period_str = "Year"

                else:
                    embed = discord.Embed(description="Invalid period. Use `W`, `M`, or `Y` for weekly, monthly, or yearly scores respectively.", color=discord.Color.red())
                    await ctx.send(embed=embed)
                    return

                scores = await cursor.fetchall()

                if not scores:
                    embed = discord.Embed(description=f"No scores found for the {period_str.lower()}.", color=discord.Color.red())
                    await ctx.send(embed=embed)
                    return

                rank_embed = discord.Embed(title=f"Rankings for {period_str}", color=discord.Color.gold())
                rank = 1

                for score in scores:
                    discord_id = score['discord_id']
                    total_score = score['total_score']

                    try:
                        user = await bot.fetch_user(discord_id)
                        user_mention = user.mention
                        rank_str = f"{get_rank_emoji(rank)} **Rank {rank}:** {user_mention} - **Total Score:** {total_score}"
                        rank_embed.add_field(name="\u200b", value=rank_str, inline=False)

                        rank += 1

                        if rank > 10:  
                            break
                    except discord.errors.NotFound:
                        logging.warning(f"User not found for discord_id: {discord_id}")
                    except Exception as e:
                        logging.error(f"Error fetching user: {str(e)}")

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
        return ""
