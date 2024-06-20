import discord
from discord.ext import commands
import aiomysql
from datetime import datetime
import logging
import os
from dotenv import load_dotenv

load_dotenv()

TASK_CHANNEL_ID = int(os.getenv('TASK_CHANNEL_ID'))


async def setup(bot, create_connection, AUTHORIZED_USER_IDS):
    @bot.command()
    async def AddTask(ctx, member: discord.Member, task_name: str, weight: float, deadline: str):
        try:
            if ctx.author.id not in AUTHORIZED_USER_IDS:
                message = "You don't have permission to use this command."
                embed = discord.Embed(description=message, color=0xFF0000)
                await ctx.send(embed=embed)
                return

            connection = await create_connection()

            if not connection:
                await ctx.send("Database connection failed.")
                return

            async with connection.cursor() as cursor:
                
                sql_check_task = "SELECT id FROM Tasks WHERE task_name = %s AND participant_id = (SELECT id FROM Participants WHERE discord_id = %s)"
                await cursor.execute(sql_check_task, (task_name, member.id))
                existing_task = await cursor.fetchone()

                if existing_task:
                    message = f"A task with name '{task_name}' already exists for {member.mention}. Please use a different name."
                    embed = discord.Embed(description=message, color=0xFF0000)
                    await ctx.send(embed=embed)
                    return

                
                sql_insert_task = "INSERT INTO Tasks (task_name, weight, participant_id, deadline, created_at) VALUES (%s, %s, (SELECT id FROM Participants WHERE discord_id = %s), %s, NOW())"
                await cursor.execute(sql_insert_task, (task_name, weight, member.id, deadline))
                await connection.commit()

                deadline_date = datetime.strptime(deadline, "%Y-%m-%d").date()
                current_date = datetime.now().date()
                days_until_deadline = (deadline_date - current_date).days

                if days_until_deadline > 0:
                    decrease_per_day = weight / days_until_deadline
                    score_message = f"Everyday will decrease the weight by {decrease_per_day:.2f} per day"

                    task_details_message = f"New task added to AlienCore:\n" \
                                           f"Task Name: {task_name}\n" \
                                           f"Weight: {weight:.2f}\n" \
                                           f"Deadline: {deadline}\n" \
                                           f"{score_message}\n" \
                                           f"Assigned to: {member.mention}"
                    task_channel = bot.get_channel(TASK_CHANNEL_ID)

                    embed_task_details = discord.Embed(description=task_details_message, color=0x000000)

                    
                    button = discord.ui.Button(label="Delete Task", style=discord.ButtonStyle.secondary, custom_id=f"delete_{task_name}_{deadline}")
                    view = discord.ui.View()
                    view.add_item(button)
                    task_message = await task_channel.send(embed=embed_task_details, view=view)

                    dm_message = f"There is a new task assigned to you in AlienCore. Please check the task channel and Miro."
                    dm_embed = discord.Embed(description=dm_message, color=0x000000)
                    await member.send(embed=dm_embed)

                    message_success = f"Task added successfully for {member.mention}"
                    embed_success = discord.Embed(description=message_success, color=0x18bd06)
                    await ctx.send(embed=embed_success)
                else:
                    await ctx.send("Deadline should be a future date.")

        except aiomysql.Error as e:
            logging.error(f"Database error: {str(e)}")
        except Exception as e:
            logging.error(f"Unexpected error: {str(e)}")
        finally:
            try:
                if connection:
                    await connection.ensure_closed()
            except Exception as e:
                logging.error(f"Error closing the database connection: {str(e)}")


    @bot.event
    async def on_interaction(interaction: discord.Interaction):
        if interaction.data['custom_id'].startswith("delete_"):
            _, task_name, deadline = interaction.data['custom_id'].split('_')
            
            task_channel = bot.get_channel(TASK_CHANNEL_ID)

            if interaction.channel == task_channel:
                connection = await create_connection()

                if not connection:
                    await task_channel.send("Database connection failed.")
                    return

                try:
                    async with connection.cursor() as cursor:
                        sql_find_task = "SELECT id FROM Tasks WHERE task_name = %s AND deadline = %s"
                        await cursor.execute(sql_find_task, (task_name, deadline))
                        result = await cursor.fetchone()

                        if result:
                            task_id = result['id']
                            if interaction.user.id in AUTHORIZED_USER_IDS:
                                sql_delete_task = "DELETE FROM Tasks WHERE id = %s"
                                await cursor.execute(sql_delete_task, (task_id,))
                                await connection.commit()

                                await interaction.message.delete()

                                removal_message = f"Task '{task_name}' has been removed."
                                embed_removal = discord.Embed(description=removal_message, color=0xFF0000)
                                await task_channel.send(embed=embed_removal)
                            else:
                                permission_message = "You don't have permission to delete tasks."
                                embed_permission = discord.Embed(description=permission_message, color=0xFF0000)
                                await interaction.user.send(embed=embed_permission)

                except aiomysql.Error as e:
                    logging.error(f"Database error: {str(e)}")
                finally:
                    try:
                        if connection:
                            await connection.ensure_closed()
                    except Exception as e:
                        logging.error(f"Error closing the database connection: {str(e)}")
