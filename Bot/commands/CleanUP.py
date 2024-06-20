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
    async def CleanUP(ctx, subcommand: str, *, table_name: str = None):
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

                elif subcommand.lower() == 'table' and table_name:
                    try:
                        await cursor.execute(f"TRUNCATE TABLE {table_name}")
                        await connection.commit()
                        embed = discord.Embed(description=f"**Table `{table_name}` has been emptied.**", color=discord.Color.green())
                        await ctx.send(embed=embed)
                    except aiomysql.Error:
                        embed = discord.Embed(description=f"**Table `{table_name}` has reference keys and cannot be emptied.**", color=discord.Color.red())
                        await ctx.send(embed=embed)

                else:
                    embed = discord.Embed(description="**Invalid command. Use one of the following:**\n`!CleanUP list`\n`!CleanUP table <TableName>`\n`!CleanUP all`\n`!CleanUP score`", color=discord.Color.red())
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
