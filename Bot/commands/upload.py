import discord
from discord.ext import commands
import aiomysql
import logging
from datetime import datetime
from discord.ui import Button, View
import pytz
import os
from dotenv import load_dotenv

load_dotenv()

EVALUATIONS_ID = int(os.getenv('EVALUATIONS_ID'))


async def setup(bot, create_connection, AUTHORIZED_USER_IDS):
    @bot.command()
    async def upload(ctx, task_name: str):
        connection = None
        try:
            connection = await create_connection()

            if not connection:
                await ctx.send("**Database connection failed.**", delete_after=10)
                return

            async with connection.cursor() as cursor:
                sql_find_user = "SELECT id, discord_id FROM Participants WHERE discord_id = %s"
                await cursor.execute(sql_find_user, (ctx.author.id,))
                result = await cursor.fetchone()

                if not result:
                    message = "**You are not one of the Participants.**"
                    embed = discord.Embed(description=message, color=0xFF0000)
                    await ctx.send(embed=embed)
                    return

                participant_id = result['id']
                participant_discord_id = result['discord_id']

                sql_find_task = "SELECT id, participant_id, deadline, created_at FROM Tasks WHERE task_name = %s"
                await cursor.execute(sql_find_task, (task_name,))
                task_result = await cursor.fetchone()

                if not task_result:
                    message = f"**This task `{task_name}` does not exist.**"
                    embed = discord.Embed(description=message, color=0xFF0000)
                    await ctx.send(embed=embed)
                    return

                task_id = task_result['id']  
                task_owner_id = task_result['participant_id']
                deadline = task_result['deadline']
                created_at = task_result['created_at']

                
                print(f"Task ID: {task_id}")

                if created_at.tzinfo is None or created_at.tzinfo.utcoffset(created_at) is None:
                    created_at = pytz.utc.localize(created_at)
                if deadline.tzinfo is None or deadline.tzinfo.utcoffset(deadline) is None:
                    deadline = pytz.utc.localize(deadline)

                if participant_id != task_owner_id:
                    message = f"**This task `{task_name}` is not assigned to you.**"
                    embed = discord.Embed(description=message, color=0xFF0000)
                    await ctx.send(embed=embed)
                    return

                sql_check_submission = "SELECT id FROM Submissions WHERE participant_id = %s AND task_id = %s"
                await cursor.execute(sql_check_submission, (participant_id, task_id))
                existing_submission = await cursor.fetchone()

                if existing_submission:
                    message = f"**This task `{task_name}` has already been submitted.**"
                    embed = discord.Embed(description=message, color=0xFF0000)
                    await ctx.send(embed=embed)
                    return

                sql_insert_submission = "INSERT INTO Submissions (participant_id, task_id, status, submitted_at) VALUES (%s, %s, %s, NOW())"
                await cursor.execute(sql_insert_submission, (participant_id, task_id, 'pending'))
                submission_id = cursor.lastrowid
                await connection.commit()

                submission_message = f"**{ctx.author} has submitted the task `{task_name}` and status is pending.**"
                embed = discord.Embed(description=submission_message, color=0x800080)
                await ctx.send(embed=embed)

                 
                channel = bot.get_channel(EVALUATIONS_ID)

                submission_embed = discord.Embed(description=submission_message, color=0x800080)
                view = await create_button_view(submission_id, connection)
                await channel.send(embed=submission_embed, view=view)

                participant = bot.get_user(participant_discord_id)
                if participant:
                    dm_message = f"**Your task submission for `{task_name}` has been submitted and is pending review.**"
                    embed = discord.Embed(description=dm_message, color=0x800080)
                    await participant.send(embed=embed)

        except aiomysql.Error as e:
            logging.error(f"Database error: {str(e)}")
            await ctx.send(f"**Database error: {str(e)}**", delete_after=10)
        except Exception as e:
            logging.error(f"Unexpected error: {str(e)}")
            await ctx.send(f"**Unexpected error: {str(e)}**", delete_after=10)
        finally:
            try:
                if connection:
                    await connection.ensure_closed()
            except Exception as e:
                logging.error(f"Error closing the database connection: {str(e)}")
                await ctx.send(f"**Error closing the database connection: {str(e)}**", delete_after=10)


    async def create_button_view(submission_id, connection):
        try:
            async with connection.cursor() as cursor:
                sql_get_submission_status = "SELECT status FROM Submissions WHERE id = %s"
                await cursor.execute(sql_get_submission_status, (submission_id,))
                submission_status = await cursor.fetchone()

                if submission_status:
                    status = submission_status['status']
                    if status == 'pending':
                        view = View()
                        view.add_item(Button(style=discord.ButtonStyle.red, label="Rejected", custom_id=f"rejected_{submission_id}"))
                        view.add_item(Button(style=discord.ButtonStyle.green, label="Accepted", custom_id=f"accepted_{submission_id}"))
                        return view
                    else:
                        return None
                else:
                    return None

        except aiomysql.Error as e:
            logging.error(f"Database error: {str(e)}")
            return None
        except Exception as e:
            logging.error(f"Unexpected error: {str(e)}")
            return None
        
    @bot.event
    async def on_interaction(interaction: discord.Interaction):
        connection = None
        try:
            if interaction.user.id not in AUTHORIZED_USER_IDS:
                await interaction.response.send_message("**You are not authorized to perform this action.**", ephemeral=True)
                return

            if interaction.response.is_done():
                return

            if interaction.data['custom_id'].startswith("rejected_") or interaction.data['custom_id'].startswith("accepted_"):
                action, submission_id = interaction.data['custom_id'].split('_')
                connection = await create_connection()

                if not connection:
                    await interaction.response.send_message("**Database connection failed.**", ephemeral=True)
                    return

                await interaction.response.defer(ephemeral=True)

                async with connection.cursor() as cursor:
                    sql_get_submission_status = "SELECT status, participant_id, task_id FROM Submissions WHERE id = %s"
                    await cursor.execute(sql_get_submission_status, (submission_id,))
                    submission_info = await cursor.fetchone()

                    if submission_info:
                        status = submission_info['status']
                        participant_id = submission_info['participant_id']
                        task_id = submission_info['task_id']

                        if status == 'pending':
                            if action == "rejected":
                                sql_update_submission = "UPDATE Submissions SET status = 'rejected' WHERE id = %s"
                                await cursor.execute(sql_update_submission, (submission_id,))
                                await connection.commit()
                                embed = discord.Embed(description="**Task has been rejected.**", color=0xFF0000)
                                await interaction.followup.send(embed=embed)

                            elif action == "accepted":
                                sql_update_submission = "UPDATE Submissions SET status = 'accepted' WHERE id = %s"
                                await cursor.execute(sql_update_submission, (submission_id,))
                                await connection.commit()

                                sql_select_task = """
                                SELECT t.weight, t.deadline, t.created_at, p.discord_id, p.id as participant_id, t.task_name
                                FROM Tasks t 
                                JOIN Participants p ON t.participant_id = p.id
                                WHERE t.id = %s
                                """
                                await cursor.execute(sql_select_task, (task_id,))
                                task_info = await cursor.fetchone()

                                if task_info:
                                    weight = task_info['weight']
                                    deadline = task_info['deadline']
                                    created_at = task_info['created_at']
                                    participant_discord_id = task_info['discord_id']
                                    task_name = task_info['task_name']

                                    
                                    if created_at.tzinfo is None or created_at.tzinfo.utcoffset(created_at) is None:
                                        created_at = pytz.utc.localize(created_at)
                                    if deadline.tzinfo is None or deadline.tzinfo.utcoffset(deadline) is None:
                                        deadline = pytz.utc.localize(deadline)

                                    
                                    days_left = (deadline - datetime.now(pytz.utc)).days
                                    
                                    if days_left < 0:  
                                        days_passed = abs(days_left)
                                        decrease_score_per_day = weight / (deadline - created_at).days
                                        decrease_point = decrease_score_per_day * days_passed
                                        final_score = max(weight - decrease_point, 0)  
                                    else:
                                        final_score = weight  

                                    sql_insert_evaluation = "INSERT INTO Evaluations (participant_id, task_id, score, evaluated_at) VALUES (%s, %s, %s, NOW())"
                                    await cursor.execute(sql_insert_evaluation, (participant_id, task_id, final_score))
                                    await connection.commit()

                                    sql_update_participant_score = """
                                    UPDATE Participants 
                                    SET score = (SELECT SUM(score) FROM Evaluations WHERE participant_id = %s) 
                                    WHERE id = %s
                                    """
                                    await cursor.execute(sql_update_participant_score, (participant_id, participant_id))
                                    await connection.commit()

                                    participant = bot.get_user(participant_discord_id)
                                    if participant:
                                        dm_color = discord.Color.green() if action == 'accepted' else discord.Color.red()
                                        dm_message = f"**Your task submission for `{task_name}` has been {'accepted' if action == 'accepted' else 'rejected'}. Your score is {final_score}.**"
                                        embed = discord.Embed(description=dm_message, color=dm_color)
                                        await participant.send(embed=embed)

                                    embed = discord.Embed(description="**Task has been accepted.**", color=0x00FF00)
                                    await interaction.followup.send(embed=embed)

                                message = await interaction.channel.fetch_message(interaction.message.id)
                                view = await create_button_view(submission_id, connection)
                                await message.edit(view=view)

                            else:
                                embed = discord.Embed(description=f"**This task has already been {status}.**", color=0xFF0000)
                                await interaction.followup.send(embed=embed)
                    else:
                        embed = discord.Embed(description=f"**Submission with id {submission_id} not found.**", color=0xFF0000)
                        await interaction.followup.send(embed=embed)

        except aiomysql.Error as e:
            logging.error(f"Database error: {str(e)}")
            embed = discord.Embed(description=f"**Database error: {str(e)}**", color=0xFF0000)
            await interaction.followup.send(embed=embed)
        except Exception as e:
            logging.error(f"Unexpected error: {str(e)}")
            embed = discord.Embed(description=f"**Unexpected error: {str(e)}**", color=0xFF0000)
            await interaction.followup.send(embed=embed)
        finally:
            try:
                if connection:
                    await connection.ensure_closed()
            except Exception as e:
                logging.error(f"Error closing the database connection: {str(e)}")
                embed = discord.Embed(description=f"**Error closing the database connection: {str(e)}**", color=0xFF0000)
                await interaction.followup.send(embed=embed)
