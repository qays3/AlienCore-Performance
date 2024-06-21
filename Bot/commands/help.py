import discord
from discord.ext import commands

async def setup(bot, create_connection, AUTHORIZED_USER_IDS):
    @bot.command()
    async def help(ctx):
        help_embed = discord.Embed(title="AlienCore Performance Score Bot Help", description="Here are the available commands:", color=discord.Color.purple())

        authorized_commands = [
            ("ping", "Check bot latency", "`!ping`"),
            ("add_user", "Add new user to database", "`!add_user <@member>`"),
            ("AddTask", "Add a new task for a participant", "`!AddTask <@member> <task_name> <weight> <deadline Format: 2024-06-20>`"),
            ("upload", "Upload task submission", "`!upload <taskname>`"),
            ("tasks", "List tasks for a participant", "`!tasks <@member>`"),
            ("ann", "Add announcements to the server", "`!ann <message>`"),
            ("clear", "Clear messages in the channel", "`!clear <number>`"),
            ("CleanUP", "Clean Database tables", "Use one of the following:\n`!CleanUP list`\n`!CleanUP table <TableName>`\n`!CleanUP all`\n`!CleanUP score`\n`!CleanUP users list` and `!CleanUP users <@mention>` to delete a participant.\n`!CleanUP tasks` to list all tasks or delete a specific task with `!CleanUP tasks <taskname>`"),
            ("score", "Rank based on datetime", "Use one of the following:\n`!score w <Rankings for Week> `\n`!score m <Rankings for Month>`\n`!score y <Rankings for Year>`"),
            ("rank", "Display General Rank", "`!rank`"),
            ("help", "Display this help message", "`!help`")
        ]

        public_commands = [
            ("help", "Display this help message", "`!help`"),
            ("rank", "Display General Rank", "`!rank`"),
            ("score", "Rank based on datetime", "Use one of the following:\n`!score w <Rankings for Week> `\n`!score m <Rankings for Month>`\n`!score y <Rankings for Year>`"),
            ("tasks", "List tasks for a participant", "`!tasks <@member>`"),
            ("upload", "Upload task submission", "`!upload <taskname>`"),
            ("ping", "Check bot latency", "`!ping`")
        ]

        if ctx.author.id in AUTHORIZED_USER_IDS:
            for name, description, usage in authorized_commands:
                help_embed.add_field(name=f"Command: {name}", value=f"{description}\nUsage: {usage}", inline=False)
        else:
            for name, description, usage in public_commands:
                help_embed.add_field(name=f"Command: {name}", value=f"{description}\nUsage: {usage}", inline=False)

        if isinstance(ctx.channel, discord.DMChannel):
            await ctx.author.send(embed=help_embed)
        else:
            await ctx.send(embed=help_embed)
