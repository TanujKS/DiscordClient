import src.utils as utils
from src.utils import Color

import discord
from discord.ext import commands

import asyncio

import socket

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(("8.8.8.8", 80))
local_ip = s.getsockname()[0]
s.close()


class LoggedMessage(discord.Embed):
    def __init__(self, message: discord.Message, *, type, color: discord.Color):
        guild = message.guild.name + ": " if message.guild else ""
        super().__init__(title=f"{type} in {guild}{message.channel}", description=f"Message by {str(message.author)}", color=color)

        self.add_field(name="Message:", value="None" if not message.content else message.content[0:1000], inline=False)

        if message.attachments:
            attachments = ""
            for attachment in message.attachments:
                asyncio.create_task(attachment.save("./Images/"+ str(attachment.id) + "_" + attachment.filename))
                attachments += f"http://{local_ip}:8000/Images/{str(attachment.id)}{'_'}{attachment.filename}"
                attachments += "\n"
            self.add_field(name="Attachments", value=attachments, inline=False)

        self.set_thumbnail(url=message.author.avatar_url)
        self.set_footer(text=f"Message sent at {utils.UTCtoPST(message.created_at)} PST", icon_url=self.get_icon_url(message))


    @staticmethod
    def get_icon_url(message: discord.Message):
        if isinstance(message.channel, discord.DMChannel):
            return message.channel.recipient.avatar_url
        elif isinstance(message.channel, discord.GroupChannel):
            return message.channel.icon_url
        elif message.guild:
            return message.guild.icon_url


    @classmethod
    def deleted_message(cls, message):
        return cls(message, type="Message deleted", color=Color.red())


    @classmethod
    def edited_message(cls, before, after):
        cls = cls(before, type="Message edited", color=Color.orange())
        cls.add_field(name="New Message:", value="None" if not after.content else after.content[0:1000], inline=False)

        try:
            cls.add_field(name="Edited at:", value=utils.UTCtoPST(after.edited_at), inline=False)
        except:
            pass

        return cls


class Logger(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.messageLog = {}
        self.log_channel = None


    def checkIfLog(self, message):
        if (not message.author.bot and not message.author.id in self.bot.config.ignored_users) and (not message.guild or message.guild.id in self.bot.config.logged_guilds):
            return True
        else:
            return False


    async def cog_check(self, ctx):
        if self.log_channel or ctx.command.name == "setlogchannel":
            return True
        else:
            raise commands.BadArgument(f"No logging channel is setup yet, use {self.bot.command_prefix(self.bot, ctx)}setlogchannel")


    @commands.Cog.listener()
    async def on_ready(self):
        self.log_channel = self.bot.get_channel(self.bot.config.log_channel)


    @commands.Cog.listener()
    async def on_message(self, message):
        if self.checkIfLog(message):
            message = await self.bot.get_message(message)
            if message:
                self.messageLog[message.id] = message


    @commands.Cog.listener()
    async def on_message_delete(self, message):
        message = self.messageLog.get(message.id)
        if message and self.log_channel:
            embed = LoggedMessage.deleted_message(message)
            await self.log_channel.send(embed=embed)


    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        before = self.messageLog.get(before.id)
        if before:
            after = await self.bot.get_message(after)
            self.messageLog[after.id] = after
            embed = LoggedMessage.edited_message(before, after)
            await self.log_channel.send(embed=embed)


    @commands.command(help="Logs deleted and edited messages in a server")
    @commands.guild_only()
    async def logserver(self, ctx, *, guild : discord.Guild=None):
        if not guild:
            guild = ctx.guild

        if guild.id in self.bot.config.logged_guilds:
            raise commands.BadArgument(f"Already logging {guild.name}")

        self.bot.config.logged_guilds.append(guild.id)
        self.bot.config.logged_guilds = self.bot.config.logged_guilds

        embed = discord.Embed(title=f"You are now logging {guild.name}", description="All deleted and edited messages will be sent to your logging channel", color=Color.red())
        await ctx.reply(embed=embed)


    @commands.command(help="Stops logging deleted and edited messages in a server")
    @commands.guild_only()
    async def unlogserver(self, ctx, *, guild : discord.Guild=None):
        if not guild:
            guild = ctx.guild

        if not guild.id in self.bot.config.logged_guilds:
            raise commands.BadArgument(f"You are not logging {guild.name}")

        self.bot.config.logged_guilds.remove(guild.id)
        self.bot.config.logged_guilds = self.bot.config.logged_guilds

        embed = discord.Embed(title=f"You are no longer logging {guild.name}", description="Deleted and edited messages will no longer be sent to your logging channel", color=Color.red())
        await ctx.reply(embed=embed)


    @commands.command(help="Displays a list of all servers being logged")
    async def loggedservers(self, ctx):
        guilds = [self.bot.get_guild(id).name for id in self.bot.config.logged_guilds if self.bot.get_guild(id)]
        message = "\n" + "\n".join(guilds)
        await ctx.reply(f"```Servers currently being logged: {message}```")


    @commands.command(help="Stops logging a users deleted and edited messages")
    async def ignore(self, ctx, user : discord.User):
        if user.id in self.bot.config.ignored_users:
            raise commands.BadArgument(f"Already ignoring {str(user)}")
        self.bot.config.ignored_users.append(user.id)
        self.bot.config.ignored_users = self.bot.config.ignored_users
        embed = discord.Embed(title=f"You are now ignoring {str(user)}", description="Deleted and edited messages by this user will no longer be sent to your logging channel", color=Color.red())
        await ctx.reply(embed=embed)


    @commands.command(help="Starts logging a users deleted and edited messages")
    async def unignore(self, ctx, user : discord.User):
        if not user.id in self.bot.config.ignored_users:
            raise commands.BadArgument(f"Already logging {str(user)}")
        self.bot.config.ignored_users.remove(user.id)
        self.bot.config.ignored_users = self.bot.config.ignored_users
        embed = discord.Embed(title=f"You are no longer ignoring {str(user)}", description="All deleted and edited messages by this user will now be sent to your logging channel", color=Color.red())
        await ctx.reply(embed=embed)


    @commands.command(help="Displays a list of all users being ignored")
    async def ignoredusers(self, ctx):
        _UserConverter = commands.UserConverter()
        users = [str(await _UserConverter.convert(ctx, str(id))) for id in self.bot.config.ignored_users]
        message = "\n" + "\n".join(users)
        await ctx.send(f"```Users currently being ignored: {message}```")


    @commands.command(help="Sets the channel to which all deleted and edited messages will be sent too")
    async def setlogchannel(self, ctx):
        self.bot.config.log_channel = ctx.channel.id
        self.log_channel = ctx.channel
        embed = discord.Embed(title="Your logger is setup! All deleted and edited messages will now be sent here", description="Remember, Direct Messages are automatically logged but to log servers you must use the .logserver command", color=Color.red())
        await ctx.reply(embed=embed)


    @commands.command(help="Checks which channel deleted and edited messages are being sent too")
    async def logchannel(self, ctx):
        channel = self.log_channel
        if channel:
            channel = channel.mention

        embed = discord.Embed(title="Deleted and edited messages are being sent too:", description=channel, color=Color.red())
        await ctx.reply(embed=embed)


def setup(bot):
    bot.add_cog(Logger(bot))
