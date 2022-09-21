import discord
import json
import log
import sys
import time
import tzlocal

import billingmaster as bm
from config import ADMIN, CHANNEL, TOKEN, HELLO

logger = log.new_logger('BillingBot')
bot = discord.Bot()

async def send_reply(message, reply):
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

# SLASH COMMAND

@bot.slash_command()
async def show(message, target=''):
    await message.respond(f'查 {target}')
    await send_reply(message, bm.func_view(target))

@bot.slash_command(description='/add 数值 bid 类型 备注 [[yyyymmdd]hhmmss]')
async def add(
    message,
    value:      discord.Option(int, description='数值'),
    balance_id: discord.Option(int, description='balance_id'),
    type_id:    discord.Option(int, description='类型'),
    comment:    discord.Option(str, description='备注说明'),
    time_:      discord.Option(int, description='[[YYYYmmdd]HHMMSS]') = 0,
):
    res = '{} {} {} {} "{}"{}'.format(
        '支出' if value > 0 else '收入',
        value,
        balance_id,
        type_id,
        comment,
        f' {time_}' if time_ else '',
    )
    await message.respond(res)
    await send_reply(
        message,
        bm.func_out(value, balance_id, type_id, comment, time_)
    )

@bot.slash_command(description='/transfer 数值 from to 备注 [[yyyymmdd]hhmmss]')
async def transfer(
    message,
    value:      discord.Option(int, description='数值'),
    bid_from:   discord.Option(int, description='balance_id 转移来源'),
    bid_to:     discord.Option(int, description='balance_id 转移目标'),
    comment:    discord.Option(str, description='备注说明'),
    time_:      discord.Option(int, description='[[YYYYmmdd]HHMMSS]') = 0,
):
    res = '转移 {} from {} to {} "{}"{}'.format(
        value,
        bid_from,
        bid_to,
        comment,
        f' {time_}' if time_ else '',
    )
    await message.respond(res)
    await send_reply(
        message,
        bm.func_transfer(value, bid_from, bid_to, comment, time_)
    )

@bot.slash_command()
async def modify(message, target):
    await message.respond(f'改 {target}')
    await send_reply(message, bm.func_modify(target))

@bot.slash_command()
async def select(message, conditions):
    await message.respond(f'SELECT FROM PAYMENT WHERE {conditions};')
    await send_reply(message, bm.func_SELECT(conditions))


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
    messages = await channel.history(limit=200).flatten()
    cnt = len(messages)
    while len(messages):
        m = messages.pop(-1)
        try:
            await m.delete()
        except Exception as e:
            logger.error(e)
        time.sleep(0.1)
    logger.info(f'delete_message {cnt}')
    if HELLO:
        await channel.send(HELLO)


@bot.event
async def on_ready():
    logger.info("Discord bot logged in as: %s" % bot.user.name)
    channel = bot.get_channel(CHANNEL)
    if HELLO:
        await channel.send(HELLO)


try:
    tzlocal.get_localzone()
except:
    logger.error("无法获取系统时区，请将系统时区设置为北京/上海时区")
    sys.exit()

bot.run(TOKEN)
