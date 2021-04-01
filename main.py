import asyncio
from time import sleep
from typing import List
from discord.activity import Activity
from discord.embeds import Embed
from discord.enums import ActivityType
from discord.ext import commands
from discord.guild import Guild
from discord.message import Message
from env import env
import discord
import sys
from db import client
db = client['discordbot_data']
# Discord bot token
TOKEN = env['DEV_TOKEN'] if sys.argv[1] == 'dev' else env['PROD_TOKEN']
# Get prefixes collection
prefixes = db['prefixes']
# All the parts of the embed
description = '''
Musical is a music bot that can play music in voice channels.
Musical is very similar to another discord bot called Rhythm.
Both bots have the same purpose of playing music, and have queues and playlists.
'''
important_commands = '''
The default command prefix is !, but you can change it with !prefix <new prefix>.
Some important commands are !queue (to show queue), !add <search term or youtube url> (add song to queue),
!remove <index of song> (remove song from queue), and !mv <begin> <end> (move songs around in queue).
For all the commands, run the command !help
'''
embed = Embed(title='Musical Discord Bot', description=description)
embed.add_field(name='Import Commands', value=important_commands, inline=False)
# Print out which type of bot is being run
if sys.argv[1] == 'dev':
    print('Development discord bot started')
else:
    print('Production discord bot running')

# Get the prefix for each message


def get_prefix(bot: commands.Bot, message: Message):
    try:
        return prefixes.find_one({'id': str(message.guild.id)})['prefix']
    except:
        pass


myBot = commands.Bot(command_prefix=get_prefix)
# Extensions for discord bot
startup_extensions: List[str] = [
    'discord_methods_playlists',
    'discord_methods_general',
    'discord_methods_music'
]
# Load extensions
for extension in startup_extensions:
    myBot.load_extension(extension)


@myBot.event
async def on_guild_join(guild: Guild):
    prefixes.insert_one({
        'id': str(guild.id),
        'prefix': '!'
    })
    server_count = len(myBot.guilds)
    if server_count == 1:
        await myBot.change_presence(activity=Activity(type=ActivityType.watching, name=f'{server_count} server'))
    else:
        await myBot.change_presence(activity=Activity(type=ActivityType.watching, name=f'{server_count} servers'))
    for channel in guild.text_channels:
        if channel.permissions_for(guild.me):
            await channel.send(embed=embed)
            break

# Remove prefix when removed


@myBot.event
async def on_guild_remove(guild: Guild):
    prefixes.delete_one({
        'id': str(guild.id)
    })
    server_count = len(myBot.guilds)
    if server_count == 1:
        await myBot.change_presence(activity=Activity(type=ActivityType.watching, name=f'{server_count} server'))
    else:
        await myBot.change_presence(activity=Activity(type=ActivityType.watching, name=f'{server_count} servers'))

# Prefix command to change prefix


@myBot.event
async def on_ready():
    while True:
        server_count = len(myBot.guilds)
        if server_count == 1:
            await myBot.change_presence(activity=Activity(type=ActivityType.watching, name=f'{server_count} server'))
        else:
            await myBot.change_presence(activity=Activity(type=ActivityType.watching, name=f'{server_count} servers'))
        await asyncio.sleep(300)


@myBot.command(brief='Change prefix', description='Change prefix. Default prefix is !')
async def prefix(ctx, *new_prefix):
    new_prefix = ' '.join(new_prefix)
    if not new_prefix:
        return
    prefixes.update_one({
        'id': str(ctx.guild.id)
    },
        {
        '$set': {
            'prefix': new_prefix
        }
    })
    await ctx.send(f'Prefix has been changed to {new_prefix}')


@myBot.event
async def on_message(msg: Message):
    await myBot.process_commands(msg)
    if msg.author == myBot.user:
        return
    if myBot.user.mentioned_in(msg) and not msg.mention_everyone:
        prefix = prefixes.find_one({'id': str(msg.guild.id)})
        await msg.reply('The current prefix is {prefix}. You can change it with {prefix}prefix <new prefix>'.format(prefix=prefix['prefix']))

# Run discord bot with token
myBot.run(TOKEN)
