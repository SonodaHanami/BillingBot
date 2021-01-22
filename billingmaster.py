import re
from datetime import datetime, timedelta

import log
from config import BID_DICT, TYPE_DICT
from utils import totimestamp
from sqlitedao import BalanceDao, PaymentDao

logger = log.new_logger('BillingMaster')
paydao = PaymentDao()
baldao = BalanceDao()

def billing_reply(message):
    if message.content.startswith('收入'):
        msg = message.content[2:].strip()
        reply = func_in(msg)
    elif message.content[0:2] in ['记账', '支出']:
        msg = message.content[2:].strip()
        reply = func_out(msg)
    elif message.content.startswith('转移'):
        msg = message.content[2:].strip()
        reply = func_transfer(msg)
    elif message.content.startswith('查'):
        msg = message.content[1:].strip()
        reply = func_view(msg)
    elif message.content.startswith('SELECT '):
        msg = message.content[7:].strip()
        reply = func_sel(msg)
    elif message.content.startswith('改'):
        msg = message.content[1:].strip()
        reply = func_mod(msg)
    elif message.content.startswith('删'):
        msg = message.content[1:].strip()
        reply = func_del(msg)
    elif message.content == '重新排序':
        paydao.order_by_time()
        logger.info('order_by_time()')
        reply = 'order_by_time() executed'
    elif message.content in ['余额', '查询余额']:
        reply = check_balance()
    else:
        reply = None

    if reply:
        return reply


def check_balance():
    balance = baldao.find_all()
    replys = [
        '{0}|{2:>10,}|{1}'.format(
            b['bid'], BID_DICT[b['bid']], b['value'], b['name']
        ) for b in balance
    ]
    reply = '```' + "\n".join(replys) + '```'
    logger.info('check_balance()')
    return reply


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
    if bid == 0:
        return 'bid should be between 1 and 5'
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
    reply = f'[{datetime.fromtimestamp(now)}] -{value} {BID_DICT[bid]} {comment} added'
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
    if bid == 0:
        return 'bid should be between 1 and 5'
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
    reply = f'[{datetime.fromtimestamp(now)}] {value} {BID_DICT[bid]} {TYPE_DICT[type]} {comment} added'
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
    comment  = re.sub('\d+', '', msg).strip()
    if bid_from == 0 or bid_to == 0:
        return 'bid should be between 1 and 5'
    if bid_from == bid_to:
        return 'same bid'
    paydao.add({
        'value'      : value,
        'bid'        : bid_from,
        'type'       : 0,
        'time'       : now,
        'comment'    : comment,
    })
    paydao.add({
        'value'      : value * (-1),
        'bid'        : bid_to,
        'type'       : 0,
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
    reply = f'[{datetime.fromtimestamp(now)}] transfer {value} from {BID_DICT[bid_from]} to {BID_DICT[bid_to]}'
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
            'type   : {0}\n'.format((BID_DICT[p['bid']] + ' ' + TYPE_DICT[p['type']]).strip()) + \
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
    reply = []
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
        reply.append(r)
        i = i + 50
    return reply


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
        if new_bid == 0:
            return 'bid should be between 1 and 5'
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

