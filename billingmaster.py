import re
import time
from datetime import datetime, timedelta

import log
from config import BID_DICT, TYPE_DICT
from utils import totimestamp
from sqlitedao import BalanceDao, PaymentDao

logger = log.new_logger('BillingMaster')
paydao = PaymentDao()
baldao = BalanceDao()

def billing_reply(message):
    msg = message.content.strip()
    if msg.startswith('收入'):
        msg = msg[2:].strip()
        reply = func_in(msg)
    elif msg[0:2] in ['记账', '支出']:
        msg = msg[2:].strip()
        reply = func_out(msg)
    elif msg.startswith('转移'):
        msg = msg[2:].strip()
        reply = func_transfer(msg)
    elif msg.startswith('查'):
        msg = msg[1:].strip()
        reply = func_view(msg)
    elif msg.startswith('SELECT '):
        msg = msg[7:].strip()
        reply = func_sel(msg)
    elif msg.startswith('改'):
        msg = msg[1:].strip()
        reply = func_mod(msg)
    elif msg.startswith('删'):
        msg = msg[1:].strip()
        reply = func_del(msg)
    elif msg == '重新排序':
        t0 = time.time()
        paydao.order_by_time()
        t1 = time.time() - t0
        logger.info('order_by_time()')
        reply = 'order_by_time() executed\n{}s'.format(t1)
    elif msg == '余额':
        reply = check_balance()
    elif msg == '配置':
        reply = check_config()
    else:
        reply = None

    if reply:
        return reply


def check_balance():
    balance = baldao.find_all()
    replys = [
        '{0}|{2:>10,}|{1}'.format(
            b['bid'], b['name'], b['value']
        ) for b in balance
    ]
    reply = '```' + "\n".join(replys) + '```'
    logger.info('check_balance()')
    return reply


def check_config():
    replys = []

    reply = '```BID_DICT:\n'
    for k in BID_DICT.keys():
        reply += f'{k} {BID_DICT[k]}\n'
    reply = reply[:-1] + '```'
    replys.append(reply)

    reply = '```TYPE_DICT:\n'
    for k in TYPE_DICT.keys():
        reply += f'{k} {TYPE_DICT[k]}\n'
    reply = reply[:-1] + '```'
    replys.append(reply)

    logger.info('check_config()')
    return replys


def func_in(msg):
    usage = '使用方法：\n收入 数值 [bid=1] [备注]'
    now = int(datetime.now().timestamp())
    nums = re.findall('\d+', msg)
    if len(nums) == 0 or len(nums) > 2:
        return usage
    elif len(nums) == 1:
        value = int(nums[0])
        bid  = 1
    elif len(nums) == 2:
        value = int(nums[0])
        bid  = int(nums[1])
    if bid == 0 or bid not in BID_DICT:
        return 'bid should be in BID_DICT and not be 0.'
    comment = re.sub('\d+', '', msg).strip()
    if comment == '':
        comment = None
    paydao.add({
        'value'      : value * (-1),
        'bid'        : bid,
        'type'       : 0,
        'time'       : now,
        'comment'    : comment
    })
    baldao.modify_minus({
        'bid'        : 0,
        'value'      : value * (-1),
        'last_update': now
    })
    baldao.modify_minus({
        'bid'        : bid,
        'value'      : value * (-1),
        'last_update': now
    })
    reply = f'[{datetime.fromtimestamp(now)}] -{value} ' + \
            f'{BID_DICT.get(bid, bid)} {comment} added'
    logger.info(reply)
    return reply


def func_out(msg):
    usage = '使用方法：\n记账 数值 [bid] [类型] [备注]\n' + \
            '记账 指定时间 数值 [bid] [类型] yyyymmddhhmmss [备注]'
    now = int(datetime.now().timestamp())
    nums = re.findall('\d+', msg)
    if msg.startswith('指定时间'):
        if len(nums) == 2:
            value = int(nums[0])
            bid   = 1
            type  = 0
        elif len(nums) == 3:
            value = int(nums[0])
            bid   = int(nums[1])
            type  = 0
        elif len(nums) == 4:
            value = int(nums[0])
            bid   = int(nums[1])
            type  = int(nums[2])
        else:
            return usage
        now = totimestamp(nums[len(nums) - 1])
        if not now:
            return usage
        msg = msg[4:].strip()
    else:
        if len(nums) == 1:
            value = int(nums[0])
            bid   = 1
            type  = 0
        elif len(nums) == 2:
            value = int(nums[0])
            bid   = int(nums[1])
            type  = 0
        elif len(nums) == 3:
            value = int(nums[0])
            bid   = int(nums[1])
            type  = int(nums[2])
        else:
            return usage
    if bid == 0 or bid not in BID_DICT:
        return 'bid should be in BID_DICT and not be 0.'
    if type not in TYPE_DICT:
        return 'type should be in TYPE_DICT.'
    comment = re.sub('\d+', '', msg).strip()
    if comment == '':
        comment = None
    paydao.add({
        'value'      : value,
        'bid'        : bid,
        'type'       : type,
        'time'       : now,
        'comment'    : comment
    })
    baldao.modify_minus({
        'bid'        : 0,
        'value'      : value,
        'last_update': now
    })
    baldao.modify_minus({
        'bid'        : bid,
        'value'      : value,
        'last_update': now
    })
    reply = f'[{datetime.fromtimestamp(now)}] {value} ' + \
            f'{BID_DICT.get(bid, bid)} {TYPE_DICT.get(type, type)} ' + \
            f'{comment} added'
    logger.info(reply)
    return reply


def func_transfer(msg):
    usage = '使用方法：\n转移 数值 from to [备注]'
    now = int(datetime.now().timestamp())
    nums = re.findall('\d+', msg)
    if len(nums) != 3:
        return usage
    value    = int(nums[0])
    bid_from = int(nums[1])
    bid_to   = int(nums[2])
    comment  = re.sub('\d+', '', msg).strip() or f'转移 {bid_from} -> {bid_to}'
    if (bid_from == 0 or bid_from not in BID_DICT) or (bid_to == 0 or bid_to not in BID_DICT):
        return 'bid should be in BID_DICT and not be 0.'
    if bid_from == bid_to:
        return 'same bid'
    paydao.add({
        'value'      : value,
        'bid'        : bid_from,
        'type'       : 9,
        'time'       : now,
        'comment'    : comment,
    })
    paydao.add({
        'value'      : value * (-1),
        'bid'        : bid_to,
        'type'       : 9,
        'time'       : now,
        'comment'    : comment,
    })
    baldao.modify_minus({
        'bid'        : bid_from,
        'value'      : value,
        'last_update': now
    })
    baldao.modify_minus({
        'bid'        : bid_to,
        'value'      : value * (-1),
        'last_update': now
    })
    reply = f'[{datetime.fromtimestamp(now)}] transfer {value} ' + \
            f'from {BID_DICT.get(bid_from, bid_from)} ' + \
            f'to {BID_DICT.get(bid_to, bid_to)}'
    logger.info(reply)
    return reply


def func_view(msg):
    logger.info(f'func_view({msg})')
    now = int(datetime.now().timestamp())
    if not len(msg) or msg == '今天' or msg == '今日':
        yyyy = datetime.today().year
        mm = datetime.today().month
        dd = datetime.today().day
        t1 = datetime(yyyy, mm, dd)
        t2 = t1 + timedelta(days=1)
        pays = paydao.find_from_time_to_time(
            t1.timestamp(),
            t2.timestamp()
        )
    elif msg == '昨天' or msg == '昨日':
        yyyy = datetime.today().year
        mm = datetime.today().month
        dd = datetime.today().day
        t1 = datetime(yyyy, mm, dd) + timedelta(days=-1)
        t2 = datetime(yyyy, mm, dd)
        pays = paydao.find_from_time_to_time(
            t1.timestamp(),
            t2.timestamp()
        )
    elif msg == '本月':
        yyyy = datetime.today().year
        mm = datetime.today().month
        dd = datetime.today().day
        t1 = datetime(yyyy, mm, 1)
        if mm == 12:
            yyyy += 1
            mm = 0
        mm += 1
        t2 = datetime(yyyy, mm, 1)
        pays = paydao.find_from_time_to_time(
            t1.timestamp(),
            t2.timestamp()
        )
    elif re.match('\d{8}', msg):
        if re.match('\d{8}', msg)[0] != msg:
            return 'invalid parameter'
        yyyy = int(msg[0:4])
        mm = int(msg[4:6])
        dd = int(msg[6:8])
        t1 = datetime(yyyy, mm, dd)
        t2 = t1 + timedelta(days=1)
        pays = paydao.find_from_time_to_time(
            t1.timestamp(),
            t2.timestamp()
        )
    elif re.match('\d{6}', msg):
        if re.match('\d{6}', msg)[0] != msg:
            return 'invalid parameter'
        yyyy = int(msg[0:4])
        mm = int(msg[4:6])
        t1 = datetime(yyyy, mm, 1)
        if mm == 12:
            yyyy += 1
            mm = 0
        mm += 1
        t2 = datetime(yyyy, mm, 1)
        pays = paydao.find_from_time_to_time(
            t1.timestamp(),
            t2.timestamp()
        )
    elif re.match('\d+', msg):
        nums = re.findall('\d+', msg)
        usage = '使用方法：\n查 记录编号'
        if len(nums) != 1:
            return usage
        p = paydao.find_one(nums[0])
        if not p:
            return f'no record {nums[0]}'
        reply = '```' + \
            'pid    : {0}\n'.format(p['pid']) + \
            'value  : {0:,}\n'.format(p['value']) + \
            'bid    : {0}\n'.format(BID_DICT.get(p['bid'], p['bid'])) + \
            'type   : {0}\n'.format(TYPE_DICT.get(p['type'], p['type'])) + \
            'time   : {0}\n'.format(datetime.fromtimestamp(p['time'])) + \
            'comment: {0}\n'.format(p['comment'] or '') + \
            '```'

        return reply

    elif msg in ['全部', 'all']:
        pays = paydao.find_all()
    else:
        return 'invalid parameter'

    reply = func_output_pays(pays)
    return reply


def func_sel(msg):
    pays = paydao.select(msg)
    reply = func_output_pays(pays)
    return reply

def func_output_pays(pays):
    logger.info(f'func_output_pays(), len(pays): {len(pays)}')
    if not len(pays):
        return 'no record'

    i = 0
    replys = []
    size = max(len(str(pays[-1]['pid'])), 3) # len('pid') == 3
    while i < len(pays):
        j = i
        r = '```' + 'pid'.center(size) + \
            '|' + 'value'.center(14-size) + \
            '|' + 'time'.center(16) + \
            '\n' + '-' * size + '|' + '-' * (14 - size) + '|' + '-' * 16
        while j < i + 50 and j < len(pays):
            r += '\n{1:{0}}|{3:{2},}|{4}'.format(
                size,
                pays[j]['pid'],
                14 - size,
                pays[j]['value'],
                str(datetime.fromtimestamp(pays[j]['time']))[:-3]
            )
            j = j + 1
        r += '```'
        replys.append(r)
        i = i + 50
    return replys


def func_mod(msg):
    logger.info(f'func_mod({msg})')
    usage = '改 pid column value'
    now = int(datetime.now().timestamp())
    prms = re.match('(\d+) (value|type|bid|time|comment) (.+)', msg)
    if not prms:
        return usage
    pid = prms[1]
    col = prms[2]
    val = prms[3]
    if col != 'comment':
        try:
            _ = int(val)
        except ValueError:
            return usage
    p = paydao.find_one(pid)
    if not p:
        return 'no record'
    if str(p[col]) == val:
        return 'same value'
    if col == 'value':
        delta = int(val) - int(p['value'])
        baldao.modify_minus({
            'bid'        : 0,   # total
            'value'      : delta,
            'last_update': now
        })
        baldao.modify_minus({
            'bid'        : p['bid'], # targer bid
            'value'      : delta,
            'last_update': now
        })
    elif col == 'bid':
        old_bid = p['bid']
        new_bid = int(val)
        if new_bid == 0 or new_bid not in BID_DICT:
            return 'bid should be in BID_DICT and not be 0.'
        baldao.modify_minus({
            'bid'        : old_bid,
            'value'      : p['value'] * (-1),
            'last_update': now
        })
        baldao.modify_minus({
            'bid'        : new_bid,
            'value'      : p['value'],
            'last_update': now
        })
    elif col == 'type':
        if int(val) not in TYPE_DICT:
            return 'type should be in TYPE_DICT.'
        paydao.modify(pid, col, int(val))
    elif col == 'time':
        if re.match('^\d\d:?\d\d:?\d\d$', val):
            val = str(datetime.fromtimestamp(p['time']))[0:11] + val
        val = totimestamp(val)
    elif col == 'comment' and val == 'None':
        val = None
    paydao.modify(pid, col, val)
    return '修改成功\n' + func_view(pid)

def func_del(msg):
    return '...'

