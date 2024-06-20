import discord
from discord.ext import commands
import aiomysql
import logging




async def setup(bot, create_connection, AUTHORIZED_USER_IDS):
    @bot.command()
    async def add_user(ctx, member: discord.Member):
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
                
                sql_check = "SELECT * FROM Participants WHERE discord_id = %s"
                await cursor.execute(sql_check, (member.id,))
                result = await cursor.fetchone()

                if result:
                    message = "This user is already exist."
                    embed = discord.Embed(description=message, color=0xFF0000)
                    await ctx.send(embed=embed)
                    return

                
                sql_insert = "INSERT INTO Participants (discord_id, score) VALUES (%s, 0)"
                await cursor.execute(sql_insert, (member.id,))
                await connection.commit()

            
            message = f"You were added to **AlienCore Performance Score**.\n\n" \
                      f"This is a rating system that assigns scores based on tasks assigned to you with deadlines and weights. " \
                      f"If you fail to upload the task on time, the weight will decrease.\n\n" \
                      f"If the task is accepted, the calculated score will be based on the weight and deadline.\n\n" \
                      f"For more information, type `!help`."

            embed = discord.Embed(description=message, color=0x000000)
            await member.send(embed=embed)

            
            message_panel = f"Successfully added {member.mention}"
            embed_panel = discord.Embed(description=message_panel, color=0x18bd06)
            await ctx.send(embed=embed_panel)

        except aiomysql.Error as e:
            logging.error(f"Database error: {str(e)}")
            await ctx.send(f"Database error: {str(e)}", delete_after=10)
        except Exception as e:
            logging.error(f"Unexpected error: {str(e)}")
            await ctx.send(f"Unexpected error: {str(e)}", delete_after=10)
        finally:
            try:
                if connection:
                    await connection.ensure_closed()
            except Exception as e:
                logging.error(f"Error closing the database connection: {str(e)}")
                await ctx.send(f"Error closing the database connection: {str(e)}", delete_after=10)
