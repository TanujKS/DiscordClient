import discord
from discord.ext import commands

import src.utils as utils
from src.utils import Color, Config

from src.cogs.Setup import Setup
from src.cogs.Misc import Misc
from src.cogs.Logger import Logger
from src.cogs.ErrorHandler import ErrorHandler
from src.cogs import cogs_dict as cogs


class Bot(commands.Bot):
    def __init__(bot, **kwargs):
        super().__init__(**kwargs)
        bot.debug = kwargs.get("debug", False)

        try:
            bot.config = Config.from_file()
        except FileNotFoundError:
            bot.config = Config()

        if not bot.config.cogs:
            bot.add_cog(cogs["Setup"](bot))
        else:
            for cog in bot.config.cogs:
                bot.add_cog(cogs[cog](bot))

        bot.add_command(bot.setup)
        bot.add_command(bot.shutdown)

    def run(self, *args, **kwargs):
        try:
            super().run(*args, **kwargs)
        except:
            return False


    @staticmethod
    def determine_prefix(bot, message):
        if isinstance(message, discord.Message):
            if message.content == ".help":
                return [".", bot.config.prefix]
        return bot.config.prefix


    @staticmethod
    async def get_message(message: discord.Message, *, limit=25):
        return await Bot.get_message_from_id(message.id, message.channel, limit=limit)


    @staticmethod
    async def get_message_reference(message: discord.MessageReference, channel, *, limit=25):
        return await Bot.get_message_from_id(message.message_id, channel, limit=limit)


    @staticmethod
    async def get_message_from_id(id: int, channel: discord.TextChannel, *, limit=25):
        async for m in channel.history(limit=limit):
            if m.id == id:
                return m
        else:
            return None


    def remove_all_cogs(bot):
        cogs = [cog for cog in bot.cogs]
        for cog in cogs:
            bot.remove_cog(cog)


    async def on_ready(bot):
        print("Logged into", bot.user)
        for cog in bot.cogs:
            print("Loaded", cog)
        bot.config.TOKEN = bot.http.token
        await bot.change_precense(afk=True)


    @commands.command(help="Shuts down your Self-Bot")
    async def shutdown(ctx):
        embed = discord.Embed(title="Shutting Down. Goodbye!", color=Color.red())
        await ctx.reply(embed=embed)
        await ctx.bot.close()


    @commands.command(help="Sets up and initalizes your bot")
    async def setup(ctx):
        bot = ctx.bot

        cogs = {
         "📝" : "Logger",
         "⚙️" : "Misc",
        }

        embed = discord.Embed(title="Setup Menu", description="Select what features you would like to enable", color=Color.red())
        embed.add_field(name="React 📝 to enable Logger", value="\u200b", inline=False)
        embed.add_field(name="React ⚙️ to enable commands", value="\u200b", inline=False)
        embed.add_field(name="React ✅ to confirm", value="\u200b", inline=False)
        message = await ctx.reply(embed=embed)
        for key, value in cogs.items():
            await message.add_reaction(key)

        def check(reaction, user):
            return user == ctx.author and reaction.message == message and str(reaction) == "✅"

        reaction, user = await bot.wait_for('reaction_add', timeout=120.0, check=check)

        selected_cogs = [str(reaction) for reaction in reaction.message.reactions if str(reaction) != "✅"]
        selected_cogs = [cogs[cog] for cog in selected_cogs]
        selected_cogs.append("ErrorHandler")

        bot.config.cogs = selected_cogs

        loaded_cogs = [cog for cog in bot.cogs]
        for cog in loaded_cogs:
            bot.remove_cog(cog)

        for cog in selected_cogs:
            bot.add_cog(globals()[cog](bot))


        await message.clear_reactions()
        embed = discord.Embed(title="Your Self-Bot is setup! You can always use the setup command to edit which features you would like enabled", color=Color.red())

        bot.config.cogs = selected_cogs

        bot.remove_all_cogs()

        for cog in selected_cogs:
            bot.add_cog(globals()[cog](bot))

        await message.clear_reactions()
        embed = discord.Embed(title="Your Self-Bot is setup! You can always use the setup command to edit which features you would like enabled", description="Remember, if you have not set a logging channel yet, please use the .setlogchannel command to enable Logger", color=Color.red())

        await message.edit(embed=embed)
