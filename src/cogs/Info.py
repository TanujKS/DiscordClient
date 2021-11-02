import src.utils as utils
from src.utils import Color

import discord
from discord.ext import commands


class Info(commands.Cog, description="Commands for getting information on users, members, etc"):
    def __init__(self, bot):
        self.bot = bot


    @staticmethod
    async def getUserInfo(ctx, user : discord.User):
        embed = discord.Embed(title=f"{str(user)}'s Profile", description=user.mention, color=Color.red())
        embed.set_thumbnail(url=user.avatar_url)
        embed.add_field(name="Display Name:", value=user.display_name)
        embed.add_field(name="ID:", value=user.id)
        embed.add_field(name="Account creation date:", value=utils.UTCtoPST(user.created_at))
        return embed


    @commands.command(description="<user> can be the name, id, or mention of a user", help="Gets information of a user")
    async def userinfo(self, ctx, *user : discord.User):
        user = ctx.author if not user else user[0]
        embed = await self.getUserInfo(ctx, user)
        await ctx.reply(embed=embed)


    @commands.command(description="<member> can be the name, id, or mention of a member", help="Gets information of a member")
    @commands.guild_only()
    async def memberinfo(self, ctx, *member : discord.Member):
        member = ctx.author if not member else member[0]
        embed = await self.getUserInfo(ctx, member)
        embed.add_field(name=f"Joined {ctx.guild.name} at:", value=utils.UTCtoPST(member.joined_at))
        await ctx.send(embed=embed)


    @commands.command(help="Gets information of the current server", aliases=["serverinfo"])
    @commands.guild_only()
    async def guildinfo(self, ctx, *guild):
        guild = await commands.GuildConverter().convert(ctx, " ".join(guild)) if commands.is_owner() and guild else ctx.guild

        embed = discord.Embed(title=f"{guild.name}'s Information", description=f"Description: {guild.description}", color=Color.red())
        embed.set_thumbnail(url=guild.icon_url)
        embed.add_field(name="Name:", value=guild.name)
        embed.add_field(name="ID:", value=guild.id)
        embed.add_field(name="Created at:", value=utils.UTCtoPST(guild.created_at))
        embed.add_field(name="Members:", value=utils.insert_commas(len([member for member in guild.members if not member.bot])))
        embed.add_field(name="Bots:", value=utils.insert_commas(len([bot for bot in guild.members if bot.bot])))
        embed.add_field(name="Total Members:", value=utils.insert_commas(guild.member_count))
        embed.add_field(name="Region:", value=str(guild.region), inline=False)
        embed.add_field(name="\u200b", value="\u200b")
        embed.add_field(name="Owner:", value=getattr(guild.owner, "mention", str(guild.owner)), inline=False)
        embed.add_field(name="Emoji Limit:", value=f"{utils.insert_commas(round(guild.emoji_limit))} Emojis")
        embed.add_field(name="Filesize Limit:", value=f"{utils.insert_commas(round(guild.filesize_limit))} Bytes")
        embed.add_field(name="Bitrate Limit:", value=f"{utils.insert_commas(round(guild.bitrate_limit))} Bits")
        embed.add_field(name="Multi-Factor Authentication", value="Required" if guild.mfa_level == 1 else "Not Required")
        await ctx.reply(embed=embed)




def setup(bot):
    bot.add_cog(Info(bot))
