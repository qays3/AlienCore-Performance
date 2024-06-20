import discord
from discord.ext import commands
import aiomysql
import logging
import os
from dotenv import load_dotenv
import json
import importlib

load_dotenv()


TOKEN = os.getenv('TOKEN')
DB_HOST = os.getenv('DB_HOST')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_DATABASE = os.getenv('DB_DATABASE')
AUTHORIZED_USER_IDS_str = os.getenv('AUTHORIZED_USER_IDS')


AUTHORIZED_USER_IDS = json.loads(AUTHORIZED_USER_IDS_str) if AUTHORIZED_USER_IDS_str else []


intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)
logging.basicConfig(level=logging.ERROR)


bot.remove_command("help")


async def create_connection():
    try:
        connection = await aiomysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            db=DB_DATABASE,
            charset='utf8mb4',
            cursorclass=aiomysql.DictCursor
        )
        return connection
    except Exception as e:
        logging.error(f"Error creating database connection: {str(e)}")
        return None


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    await bot.change_presence(activity=discord.Game(name="!help"))


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.errors.CommandNotFound):
        await ctx.send("Invalid command. Use `!help` to see available commands.")


async def setup_commands():
    command_modules = ['add_task', 'add_user', 'help', 'clear', 'upload', 'ping', 'tasks', 'ann', 'CleanUP', 'score', 'rank']

    for module_name in command_modules:
        try:
            module = importlib.import_module(f'commands.{module_name}')
            if hasattr(module, 'setup'):
                await module.setup(bot, create_connection, AUTHORIZED_USER_IDS)
                print(f"Loaded {module_name} command.")
        except Exception as e:
            logging.error(f"Error loading {module_name} command: {str(e)}")


@bot.event
async def on_connect():
    await setup_commands()


if __name__ == "__main__":
    bot.run(TOKEN)
