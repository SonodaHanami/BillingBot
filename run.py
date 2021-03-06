import discord
import json
import log
import sys
from billingmaster import billing_reply
from config import ADMIN, TOKEN

ME = ADMIN
logger = log.new_logger('BillingBot')
client = discord.Client()

@client.event
async def on_message(message):
    # Only works for ME
    if message.author.id != ME:
        return None
    reply = billing_reply(message)
    try:
        if reply is None:
            return None
        elif isinstance(reply, str):
            await message.channel.send(reply)
        elif isinstance(reply, list):
            for r in reply:
                await message.channel.send(r)
    except:
        await message.channel.send('出错了1551')

@client.event
async def on_ready():
    logger.info("Discord bot logged in as: %s" % client.user.name)

client.run(TOKEN)
