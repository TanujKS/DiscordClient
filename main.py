from src.tokenFinder import TokenFinder
from src.bot import Bot
import src.utils as utils
from src.help import EmbedHelpCommand

import discord

import json

import asyncio
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import argparse
parser = argparse.ArgumentParser("Configure your Self-Bot. These are advanced settings intended for people with a knowledge of programming")
parser.add_argument('TOKEN', nargs="?", default=None)
parser.add_argument("-d", "--debug", help="Boots the bot into Debug mode, where only the bot Owner can use commands and tracebacks are printed etc", action="store_true")
args = parser.parse_args()


def new_login():
    TOKENS = [args.TOKEN] if args.TOKEN is not None else TokenFinder().to_list()
    if not TOKENS:
        utils.raiseDialogue("Could not detect your Discord token! Your token is required to run a Self-Bot. Try manually passing the argument")
        exit()

    for token in TOKENS:
        print("Found token:", token)
        asyncio.set_event_loop(asyncio.new_event_loop())
        bot = Bot(command_prefix=Bot.determine_prefix, case_insensitive=True, self_bot=True, help_command=EmbedHelpCommand(), allowed_mentions=discord.AllowedMentions.none(), debug=args.debug)
        success = bot.run(token, bot=False)
        if success != False:
            exit()
    else:
        utils.raiseDialogue("Invalid token")

try:
    bot = Bot(command_prefix=Bot.determine_prefix, case_insensitive=True, self_bot=True, help_command=EmbedHelpCommand(), allowed_mentions=discord.AllowedMentions.none(), intents=discord.Intents.all(), debug=args.debug)
    print(bot.config.TOKEN)
    res = bot.run(bot.config.TOKEN, bot=False)
    if not res:
        new_login()
except (FileNotFoundError, TypeError):
    new_login()
