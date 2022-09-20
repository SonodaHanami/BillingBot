import discord
import json
import log
import sys
import time
import tzlocal

import billingmaster as bm
from config import ADMIN, CHANNEL, TOKEN

logger = log.new_logger('BillingBot')
bot = discord.Bot()
message_log = []


async def send_reply(message, reply):
    global message_log
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

# SLASH COMMAND

@bot.slash_command()
async def balance(message):
    await message.respond(bm.check_balance())
    # await send_reply(message, bm.check_balance())

@bot.slash_command()
async def show(message, target=''):
    # Only works for ME
    # if message.author.id != ME or message.channel.id != CHANNEL:
    #     return None
    await message.respond(f'查 {target}')
    await send_reply(message, bm.func_view(target))

@bot.slash_command()
async def pay(message, target=''):
    await message.respond(f'记账 {target}')
    await send_reply(message, bm.func_out(target))

@bot.slash_command()
async def get(message, target=''):
    await message.respond(f'收入 {target}')
    await send_reply(message, bm.func_in(target))

@bot.slash_command()
async def transfer(message, target=''):
    await message.respond(f'转移 {target}')
    await send_reply(message, bm.func_transfer(target))

@bot.slash_command()
async def modify(message, target=''):
    await message.respond(f'改 {target}')
    await send_reply(message, bm.func_mod(target))

@bot.slash_command()
async def delete(message, target=''):
    await message.respond(f'删 {target}')
    await send_reply(message, bm.func_del(target))

@bot.slash_command()
async def select(message, conditions=''):
    await message.respond(f'SELECT FROM PAYMENT WHERE {target};')
    await send_reply(message, bm.func_sel(conditions))


# USER COMMAND

@bot.user_command(name='查询余额')
async def balance_app(message, user):
    await message.respond(bm.check_balance())

@bot.user_command(name='查询配置')
async def setting_app(message, user):
    await message.respond(f'正在查询配置')
    await send_reply(message, bm.check_config())

@bot.user_command(name='查询时间')
async def date(message, user):
    await message.respond(bm.datetime_now())

@bot.user_command(name='重新排序')
async def re_order(message, user):
    await message.respond('正在重新排序...')
    await send_reply(message, bm.order_by_time())

@bot.user_command(name='清理记录')
async def clear_message_log(message, user):
    await message.respond('正在清理记录...')
    channel = message.channel
    cnt = len(message_log)
    while len(message_log):
        m = message_log.pop(0)
        try:
            await m.delete()
        except Exception as e:
            logger.error(e)
        time.sleep(0.1)
    logger.info(f'delete_message {cnt}')
    m = await channel.send('你要多少bot正在为你记账')


@bot.event
async def on_ready():
    logger.info("Discord bot logged in as: %s" % bot.user.name)

@bot.event
async def on_message(message):
    global message_log
    message_log.append(message)

try:
    tzlocal.get_localzone()
except:
    logger.error("无法获取系统时区，请将系统时区设置为北京/上海时区")
    sys.exit()

bot.run(TOKEN)
