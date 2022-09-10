import discord
import json
import log
import sys
import time
import tzlocal
from billingmaster import billing_reply
from config import ADMIN, CHANNEL, TOKEN

ME = ADMIN
logger = log.new_logger('BillingBot')
client = discord.Client()
message_log = []

@client.event
async def on_message(message):
    # Only works for ME
    if message.author.id != ME or message.channel.id != CHANNEL:
        return None
    global message_log
    message_log.append(message)
    if message.content.strip() == '/clear' or message.content.strip() == 'CLEAR':
        await delete_message(message)
        return
    reply = billing_reply(message)
    try:
        if reply is None:
            return None
        elif isinstance(reply, str):
            result = await message.channel.send(reply)
            message_log.append(result)
        elif isinstance(reply, list):
            for r in reply:
                result = await message.channel.send(r)
                message_log.append(result)
    except:
        result = await message.channel.send('出错了1551')
        message_log.append(result.id)

async def delete_message(message):
    global message_log
    m = await message.channel.send('正在清理记录...')
    message_log.append(m)
    cnt = len(message_log)
    while len(message_log):
        m = message_log.pop(0)
        print(f'delete message {m.id}')
        await m.delete()
        time.sleep(0.5)
    m = await message.channel.send(f'清理记录完成 {cnt}')
    time.sleep(5)
    print(f'delete message {m.id}')
    await m.delete()


@client.event
async def on_ready():
    logger.info("Discord bot logged in as: %s" % client.user.name)

try:
    tzlocal.get_localzone()
except:
    print("无法获取系统时区，请将系统时区设置为北京/上海时区")
    sys.exit()

client.run(TOKEN)
