import discord
from discord.ext import commands
import aiomysql
import logging
import os
from dotenv import load_dotenv

load_dotenv()

DB_DATABASE = os.getenv('DB_DATABASE')

async def setup(bot, create_connection, AUTHORIZED_USER_IDS):
    @bot.command()
    async def CleanUP(ctx, subcommand: str, *, participant_mention: str = None):
        try:
            if ctx.author.id not in AUTHORIZED_USER_IDS:
                embed = discord.Embed(description="You don't have permission to use this command.", color=discord.Color.red())
                await ctx.send(embed=embed)
                return

            connection = await create_connection()

            if not connection:
                await ctx.send("Database connection failed.")
                return

            async with connection.cursor() as cursor:
                if subcommand.lower() == 'list':
                    await cursor.execute("SHOW TABLES")
                    tables = await cursor.fetchall()
                    table_list = "\n".join([table['Tables_in_' + DB_DATABASE] for table in tables])
                    embed = discord.Embed(description=f"**Tables in Database:**\n{table_list}", color=discord.Color.purple())
                    await ctx.send(embed=embed)

                elif subcommand.lower() == 'all':
                    await cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
                    await cursor.execute("SHOW TABLES")
                    tables = await cursor.fetchall()
                    for table in tables:
                        await cursor.execute(f"TRUNCATE TABLE {table['Tables_in_' + DB_DATABASE]}")
                    await cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
                    await connection.commit()
                    embed = discord.Embed(description="**All tables have been emptied.**", color=discord.Color.green())
                    await ctx.send(embed=embed)

                elif subcommand.lower() == 'score':
                    await cursor.execute("UPDATE Participants SET score = 0")
                    await connection.commit()
                    embed = discord.Embed(description="**All participant scores have been reset to 0.**", color=discord.Color.green())
                    await ctx.send(embed=embed)

                elif subcommand.lower() == 'table' and participant_mention:
                    try:
                        if participant_mention.startswith('<@') and participant_mention.endswith('>'):
                            participant_mention = participant_mention.strip('<@!>')

                        table_name = participant_mention

                        await cursor.execute(f"TRUNCATE TABLE {table_name}")
                        await connection.commit()
                        embed = discord.Embed(description=f"**Table `{table_name}` has been emptied.**", color=discord.Color.green())
                        await ctx.send(embed=embed)
                    except aiomysql.Error:
                        embed = discord.Embed(description=f"**Table `{table_name}` has reference keys and cannot be emptied.**", color=discord.Color.red())
                        await ctx.send(embed=embed)

                elif subcommand.lower() == 'users':
                    if participant_mention and participant_mention.lower() == 'list':
                        await cursor.execute("SELECT discord_id FROM Participants")
                        participants = await cursor.fetchall()

                        if participants:
                            mention_list = "\n".join([f"<@{participant['discord_id']}>" for participant in participants])
                            embed = discord.Embed(description=f"**Participants in Database:**\n{mention_list}", color=discord.Color.blue())
                            await ctx.send(embed=embed)
                        else:
                            embed = discord.Embed(description="**No participants found in the database.**", color=discord.Color.blue())
                            await ctx.send(embed=embed)
                    elif participant_mention:
                        try:
                            if participant_mention.startswith('<@') and participant_mention.endswith('>'):
                                participant_mention = participant_mention.strip('<@!>')

                            discord_id = int(participant_mention)

                            discord_user = await bot.fetch_user(discord_id)

                            await cursor.execute("SELECT id FROM Participants WHERE discord_id = %s", (discord_id,))
                            participant = await cursor.fetchone()

                            if participant:
                                participant_id = participant['id']

                                await cursor.execute("DELETE FROM Tasks WHERE participant_id = %s", (participant_id,))
                                await cursor.execute("DELETE FROM Evaluations WHERE participant_id = %s", (participant_id,))
                                await cursor.execute("DELETE FROM Submissions WHERE participant_id = %s", (participant_id,))

                                await cursor.execute("DELETE FROM Participants WHERE id = %s", (participant_id,))
                                await connection.commit()

                                embed = discord.Embed(description=f"**Participant {discord_user.mention} and all references have been deleted.**", color=discord.Color.green())
                                await ctx.send(embed=embed)
                            else:
                                embed = discord.Embed(description=f"**No participants found in the database.**", color=discord.Color.red())
                                await ctx.send(embed=embed)
                        except ValueError:
                            embed = discord.Embed(description="**Invalid mention format. Use `@username` to specify the user.**", color=discord.Color.red())
                            await ctx.send(embed=embed)
                        except aiomysql.Error as e:
                            embed = discord.Embed(description=f"**Error deleting participant with ID `{discord_id}`: {str(e)}**", color=discord.Color.red())
                            await ctx.send(embed=embed)
                        except discord.HTTPException as e:
                            embed = discord.Embed(description=f"**Error fetching user information for `{participant_mention}`: {str(e)}**", color=discord.Color.red())
                            await ctx.send(embed=embed)
                    else:
                        embed = discord.Embed(description="**Invalid command. Use `!CleanUP users list` to list all participants or `!CleanUP users <@mention>` to delete a participant.**", color=discord.Color.red())
                        await ctx.send(embed=embed)

                elif subcommand.lower() == 'tasks':
                    if not participant_mention:
                        await cursor.execute("SELECT task_name FROM Tasks")
                        tasks = await cursor.fetchall()
                        if tasks:
                            task_list = "\n".join([task['task_name'] for task in tasks])
                            embed = discord.Embed(description=f"**Tasks in Database:**\n{task_list}", color=discord.Color.blue())
                            await ctx.send(embed=embed)
                        else:
                            embed = discord.Embed(description="**No tasks found in the database.**", color=discord.Color.blue())
                            await ctx.send(embed=embed)
                    else:
                        try:
                            await cursor.execute("SELECT id FROM Tasks WHERE task_name = %s", (participant_mention,))
                            task = await cursor.fetchone()

                            if task:
                                task_id = task['id']

                                await cursor.execute("DELETE FROM Tasks WHERE id = %s", (task_id,))
                                await cursor.execute("DELETE FROM Evaluations WHERE task_id = %s", (task_id,))
                                await cursor.execute("DELETE FROM Submissions WHERE task_id = %s", (task_id,))
                                await connection.commit()

                                embed = discord.Embed(description=f"**Task `{participant_mention}` and all references have been deleted.**", color=discord.Color.green())
                                await ctx.send(embed=embed)
                            else:
                                embed = discord.Embed(description=f"**Task `{participant_mention}` not found in database.**", color=discord.Color.red())
                                await ctx.send(embed=embed)
                        except aiomysql.Error as e:
                            embed = discord.Embed(description=f"**Error deleting task `{participant_mention}`: {str(e)}**", color=discord.Color.red())
                            await ctx.send(embed=embed)

                else:
                    embed = discord.Embed(description="**Invalid command. Use one of the following:**\n`!CleanUP list`\n`!CleanUP table <TableName>`\n`!CleanUP all`\n`!CleanUP score`\n`!CleanUP users list` to list all participants or `!CleanUP users <@mention>` to delete a participant.\n`!CleanUP tasks` to list all tasks or delete a specific task with `!CleanUP tasks <taskname>`.", color=discord.Color.red())
                    await ctx.send(embed=embed)

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
