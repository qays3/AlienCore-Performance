import discord
from discord.ext import commands
import aiomysql
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv
 

async def setup(bot, create_connection, AUTHORIZED_USER_IDS):
    @bot.command()
    async def tasks(ctx, member: discord.Member):
        try:
            connection = await create_connection()

            if not connection:
                await ctx.send("Database connection failed.")
                return

            async with connection.cursor() as cursor:
                
                sql_select_tasks = """
                    SELECT task_name, weight, deadline
                    FROM Tasks
                    WHERE participant_id = (SELECT id FROM Participants WHERE discord_id = %s)
                    AND id NOT IN (SELECT task_id FROM Submissions WHERE status = 'accepted')
                """
                await cursor.execute(sql_select_tasks, (member.id,))
                tasks = await cursor.fetchall()

                if not tasks:
                    message = f"No tasks found for {member.display_name}."
                    embed = discord.Embed(description=message, color=discord.Color.red())
                    await ctx.send(embed=embed)
                    return

                embed = discord.Embed(title=f"Tasks for {member.display_name}", color=discord.Color.purple())

                tasks_details = ""

                for task in tasks:
                    task_name = task['task_name']
                    weight = task['weight']
                    deadline = task['deadline']

                    
                    task_details = f"**{task_name}** - **Weight: `{weight:.2f}`** - **Deadline: `{deadline.strftime('%Y-%m-%d')}`**\n\n"
                    tasks_details += task_details

                embed.description = tasks_details
                await ctx.send(embed=embed)  

        except aiomysql.Error as e:
            logging.error(f"Database error: {str(e)}")
            await ctx.send("An error occurred while retrieving tasks.")
        except Exception as e:
            logging.error(f"Unexpected error in tasks command: {str(e)}")
            await ctx.send("An unexpected error occurred.")
        finally:
            try:
                if connection:
                    await connection.ensure_closed()
            except Exception as e:
                logging.error(f"Error closing the database connection: {str(e)}")
