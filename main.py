# Code by https://github.com/wdlord

import discord
from discord.ext import commands
import asyncio
import os
import creds


class Bot(commands.Bot):
    """
    Inherits from commands.Bot.
    https://discordpy.readthedocs.io/en/stable/ext/commands/api.html?highlight=commands%20bot#discord.ext.commands.Bot
    """
    def __init__(self):
        # Intents define advanced permissions for a Discord bot.
        # https://discordpy.readthedocs.io/en/stable/intents.html
        intents = discord.Intents.default()

        # This is used to improve the workflow for slash command syncing during development.
        self.testing = True

        super().__init__(command_prefix=['$'], intents=intents)

    async def on_ready(self):
        """
        This is an override of the on_ready event listener.
        Triggered when the bot goes online.
        https://discordpy.readthedocs.io/en/stable/api.html?highlight=on_ready#discord.on_ready
        """

        print(f'Logged in as {self.user} (ID: {self.user.id})')

        # When testing, slash commands are synced instantly within the guild being used for testing.
        if self.testing:
            synced = await self.tree.sync(guild=discord.Object(id=864728010132947015))

        # Alternatively, global command syncing can take up to an hour.
        else:
            synced = await self.tree.sync()

        print(len(synced))

    async def on_command_error(self, ctx: commands.Context, exception: Exception):
        """
        This is an override of the on_command_error event listener.
        Triggered when the Discord API raises an Exception.
        https://discordpy.readthedocs.io/en/stable/ext/commands/api.html?highlight=on_command_error#discord.discord.ext.commands.on_command_error
        """

        if isinstance(exception, commands.NoPrivateMessage):
            await ctx.send("This command cannot be used via DM.")

        elif isinstance(exception, commands.MissingRole):
            pass

        else:
            print(f'\n!ERROR!\n{exception}\n')


async def main():
    bot = Bot()

    # Load all the files in the /cogs folder as Cog extensions.
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py') and '__' not in filename:
            await bot.load_extension(f'cogs.{filename[:-3]}')

    print('------')
    await bot.start(creds.TOKEN)


# Start the bot loop.
discord.utils.setup_logging()
asyncio.run(main())
