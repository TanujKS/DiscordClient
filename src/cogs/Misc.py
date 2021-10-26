import discord
from discord.ext import commands
from discord.utils import get

import src.utils as utils
from src.utils import Color

from PyDictionary import PyDictionary
PyDictionary = PyDictionary()

from googletrans import Translator
from googletrans.constants import LANGUAGES
Translator = Translator()

import datetime
from datetime import datetime as dtime

import ast

import subprocess


class Misc(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.stopWatches = {}
        self.bot.help_command.cog = self


    @commands.command(help="Spams a message")
    async def spam(self, ctx, *, message):
        embed = discord.Embed(title=f"To stop spamming, use {self.bot.command_prefix(self.bot, ctx)}stopspam")
        await ctx.reply(embed=embed)

        self.spamming = True
        while self.spamming:
            await ctx.send(message)
            await asyncio.sleep(1)


    @commands.command(help="Stops spamming a message")
    async def stopspam(self, ctx):
    	self.spamming = False


    @commands.command(description="member_or_role can be the name, id, or mention of a role or member", help="Returns the permissions for a role of member in the current server")
    @commands.guild_only()
    async def perms(self, ctx, member_or_role=None):
        def convertPermtoEmoji(member, perm, permissions):
            if getattr(permissions, perm) == True:
                return "✅"
            elif getattr(permissions, perm) == False:
                return "❌"

        if member_or_role == None:
            member_or_role = ctx.author
        else:
            try:
                member_or_role = await commands.RoleConverter().convert(ctx, member_or_role)
            except commands.RoleNotFound:
                member_or_role = await commands.MemberConverter().convert(ctx, member_or_role)


        embed = discord.Embed(title=f"Perms for {str(member_or_role)} in {ctx.guild.name}", color=Color.red())

        if type(member_or_role) == discord.Member:
            permissions = member_or_role.guild_permissions

        elif type(member_or_role) == discord.Role:
            permissions = member_or_role.permissions

        for perm in permissions:
            embed.add_field(name=perm[0].replace('_', ' ').title(), value=convertPermtoEmoji(member_or_role, perm[0], permissions))

        await ctx.reply(embed=embed)


    @commands.command(description="<user> can be the name, id, or mention of a Discord user", help="Returns the profile picture of a Discord user", aliases=['pfp', 'profile'])
    async def avatar(self, ctx, *user : discord.User):
        user = ctx.author if not user else user[0]
        await ctx.reply(user.avatar_url)


    @commands.command(aliases=['purge'], help="Clears a number of messages")
    async def clear(self, ctx, num, *member: discord.User):
    	def is_member(m):
    		return m.author == member

    	def no_check(m):
    		return True

    	if num.lower() == "all":
    		num = None
    	else:
    		num = int(num)

    	if member:
    		member = member[0]
    		check = is_member
    	else:
    		check = no_check

    	if not ctx.guild:
    		messages = await ctx.channel.history(limit=num).flatten()
    		for m in messages:
    			if check(m):
    				try:
    					await m.delete()
    				except:
    					pass
    	else:
    		await ctx.channel.purge(limit=num, check=check)


    @commands.command(help="Starts a stopwatch if there is no active one")
    async def starttimer(self, ctx):
        if self.stopWatches.get(ctx.author.id):
            raise commands.BadArgument("Stop watch already in use")
        await ctx.reply("Starting stopwatch")
        self.stopWatches[ctx.author.id] = datetime.utcnow()


    @commands.command(help="Stops a stopwatch if there is an active one")
    async def stoptimer(self, ctx):
        startTime = self.stopWatches.get(ctx.author.id)
        if not startTime:
            raise commands.BadArgument("No active stopwatches")
        seconds = (datetime.utcnow() - startTime).total_seconds()
        await ctx.reply(f"Ended timer. Timer ran for: {datetime.timedelta(seconds=seconds)}")
        del self.stopWatches[ctx.author.id]


    @commands.command(description="For accurate ping readings, this is ratelimited to 1 use every 5 seconds per guild", help="Checks GamerBot's Ping")
    @commands.cooldown(1, 60, commands.BucketType.guild)
    async def ping(self, ctx):
        t = await ctx.reply("Pong!")
        await t.edit(content=f'Pong! `{(t.created_at-ctx.message.created_at).total_seconds() * 1000}ms`')


    @commands.command(help="Returns the definition of a word")
    async def define(self, ctx, word):
        embed = discord.Embed(title=f"Definition of '{word}'", color=Color.green())
        meanings = PyDictionary.meaning(word)
        for item in meanings:
            embed.add_field(name=item, value="\n".join(meanings[item]), inline=False)
        await ctx.reply(embed=embed)


    @commands.command(help="Unpins all messages in a channel")
    async def unpinall(self, ctx):
        await ctx.send(f"Are you sure you want me too unpin {len(await ctx.channel.pins())} messages? (y/n)")
        def check(m):
            responses = ['y', 'n']
            return ctx.author == m.author and ctx.channel == m.channel and msg.content in responses
        msg = await self.bot.wait_for('message', timeout=60.0, check=check)
        if msg.content == "y":
            for message in await ctx.channel.pins():
                await message.unpin()
            await ctx.send(f"Unpinned all messages")
        elif msg.content == "n":
            await ctx.send("Cancelled")


    @commands.command(help="Uses Google Translate to translate a message into English")
    async def translate(self, ctx, *, message):
        translation = Translator.translate(message, dest='en')
        embed = discord.Embed(color=Color.green())
        embed.add_field(name=LANGUAGES[translation.src.lower()].capitalize(), value=message, inline=False)
        embed.add_field(name=LANGUAGES[translation.dest].capitalize(), value=translation.text, inline=False)
        await ctx.send(embed=embed)


    @commands.command(help="Changes the Self-Bot's prefix")
    async def changeprefix(self, ctx, prefix):
        self.bot.config.prefix = prefix
        embed = discord.Embed(title=f"Your Self-Bot will now use the prefix {prefix}", description="You can still use .help incase you forget your prefix", color=Color.red())
        await ctx.send(embed=embed)


    @commands.command(help="Evalutes code in Bash")
    async def bash(self, ctx, *, cmd):
        result = subprocess.run(cmd, shell=True, text=True, capture_output=True)
        await ctx.reply(f"```{result.stdout if result.stdout else result.stderr}```")


    @commands.command(help="Evalutes code in Python", aliases=['eval', 'exec', 'run'])
    async def eval_fn(self, ctx, *, cmd):

        def insert_returns(body):
            if isinstance(body[-1], ast.Expr):
                body[-1] = ast.Return(body[-1].value)
                ast.fix_missing_locations(body[-1])

            if isinstance(body[-1], ast.If):
                insert_returns(body[-1].body)
                insert_returns(body[-1].orelse)

            if isinstance(body[-1], ast.With):
                insert_returns(body[-1].body)

        try:
            fn_name = "_eval_expr"

            cmd = cmd.strip("` ")

            cmd = "\n".join(f"    {i}" for i in cmd.splitlines())

            body = f"async def {fn_name}():\n{cmd}"

            parsed = ast.parse(body)
            body = parsed.body[0].body

            insert_returns(body)

            env = {
                'bot': ctx.bot,
                'discord': discord,
                'commands': commands,
                'ctx': ctx,
                '__import__': __import__,
                'get': get,
            }

            exec(compile(parsed, filename="<ast>", mode="exec"), env)

            result = (await eval(f"{fn_name}()", env))

            await ctx.reply(f"```{str(result)}```")

        except Exception as err:
            raise commands.BadArgument(f"```{err}```")


def setup(bot):
    bot.add_cog(Misc(bot))
