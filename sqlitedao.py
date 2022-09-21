import sqlite3
import os
import datetime
import log

DB_PATH = './Billing.db'
logger = log.new_logger('sqlitedao')


class DatabaseError(Exception):
    def __init__(self, msg, *msgs):
        self._msgs = [msg, *msgs]

    def __str__(self):
        return '\n'.join(self._msgs)

    @property
    def message(self):
        return str(self)

    def append(self, msg:str):
        self._msgs.append(msg)


class SqliteDao(object):
    def __init__(self, table, columns, fields):
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        self._dbpath = DB_PATH
        self._table = table
        self._columns = columns
        self._fields = fields
        self._create_table()


    def _create_table(self):
        sql = "CREATE TABLE IF NOT EXISTS {0} ({1})".format(self._table, self._fields)
        with self._connect() as conn:
            conn.execute(sql)


    def _connect(self):
        # detect_types 中的两个参数用于处理datetime
        return sqlite3.connect(self._dbpath, detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)



class PaymentDao(SqliteDao):
    def __init__(self):
        super().__init__(
            table='payment',
            columns='pid, value, bid, type, time, comment',
            fields='''
            pid INTEGER PRIMARY KEY AUTOINCREMENT,
            value INT NOT NULL,
            bid INT NOT NULL,
            type INT NOT NULL,
            time INT NOT NULL,
            comment VARCHAR (30)
            ''')
        logger.info('PaymentDao Initialized')


    @staticmethod
    def row2item(r):
        return {
            'pid':     r[0],
            'value':   r[1],
            'bid':     r[2],
            'type':    r[3],
            'time':    r[4],
            'comment': r[5],
        } if r else None


    def add(self, pm):
        with self._connect() as conn:
            try:
                ret = conn.execute(
                    '''
                    INSERT INTO {0} ({1}) VALUES (?, ?, ?, ?, ?, ?)
                    '''.format(self._table, self._columns),
                    (None, pm['value'], pm['bid'], pm['type'], pm['time'], pm['comment'])
                )
                return ret.lastrowid
            except (sqlite3.DatabaseError) as e:
                logger.error(f'[PaymentDao.add] {e}')
                raise DatabaseError('添加记录失败')


    def find_one(self, pid):
        with self._connect() as conn:
            try:
                ret = conn.execute('''
                    SELECT {1} FROM {0} WHERE pid=?
                    '''.format(self._table, self._columns),
                    (pid,) ).fetchone()
                return self.row2item(ret)
            except (sqlite3.DatabaseError) as e:
                logger.error(f'[PaymentDao.find_one] {e}')
                raise DatabaseError('查找记录失败')


    def find_all(self):
        with self._connect() as conn:
            try:
                ret = conn.execute('''
                    SELECT {1} FROM {0}
                    '''.format(self._table, self._columns),
                    ).fetchall()
                return [self.row2item(r) for r in ret]
            except (sqlite3.DatabaseError) as e:
                logger.error(f'[PaymentDao.find_all] {e}')
                raise DatabaseError('查找记录失败')


    def find_from_time_to_time(self, t1, t2):
        with self._connect() as conn:
            try:
                ret = conn.execute('''
                    SELECT {1} FROM {0} WHERE time BETWEEN ? AND ?
                    '''.format(self._table, self._columns),
                    (t1, t2)
                    ).fetchall()
                return [self.row2item(r) for r in ret]
            except (sqlite3.DatabaseError) as e:
                logger.error(f'[PaymentDao.find_from_time_to_time] {e}')
                raise DatabaseError('查找记录失败')


    def select(self, condition):
        with self._connect() as conn:
            try:
                ret = conn.execute('''SELECT {1} FROM {0} WHERE
                    '''.format(self._table, self._columns) + condition
                ).fetchall()
                return [self.row2item(r) for r in ret]
            except (sqlite3.DatabaseError) as e:
                logger.error(f'[PaymentDao.select] {e}')
                raise DatabaseError('查找记录失败')


    def modify(self, pid, col, val):
        with self._connect() as conn:
            try:
                conn.execute('''
                    UPDATE {0} SET {1}=? WHERE pid=?
                    '''.format(self._table, col), (val, pid)
                )
            except (sqlite3.DatabaseError) as e:
                logger.error(f'[PaymentDao.modify] {e}')
                raise DatabaseError('修改记录失败')


    def order_by_time(self):
        with self._connect() as conn:
            try:
#                result = conn.execute('SELECT time FROM payment').fetchall()
#                array = [ r[0] for r in result ]
#                n = len(array)
#                maxx, minn = -1, 9999999999
#                l, r = 0, 0
#                for i in range(n):
#                    if array[i] < maxx:
#                        r = i
#                    else:
#                        maxx = array[i]
#
#                    if array[n - 1 - i] > minn:
#                        l = n - 1 - i
#                    else:
#                        minn = array[i]
#
#                if r == 0:
#                    return
#
#                l += 1
#                r += 1
#
                conn.execute('UPDATE payment set pid = pid + 65536')
                # conn.execute('''
                #     UPDATE payment
                #     SET pid =
                #     (SELECT rank FROM
                #       (SELECT
                #         row_number() OVER (ORDER BY time) AS rank,
                #         pid FROM payment)
                #      WHERE pid = payment.pid)'''
                # )
                rank_pid = conn.execute('SELECT row_number() OVER (ORDER BY time) AS rank, pid FROM payment').fetchall()
                for rp in rank_pid:
                    conn.execute('UPDATE payment set pid = {} WHERE pid = {}'.format(rp[0], rp[1]))


            except (sqlite3.DatabaseError) as e:
                logger.error(f'[ClanDao.order_by_time] {e}')
                raise DatabaseError('修改记录顺序失败')

    def delete(self, pid):
        with self._connect() as conn:
            try:
                conn.execute('''
                    DELETE FROM {0} WHERE pid=?
                    '''.format(self._table),
                    (gid,) )
            except (sqlite3.DatabaseError) as e:
                logger.error(f'[PaymentDao.delete] {e}')
                raise DatabaseError('删除记录失败')


class BalanceDao(SqliteDao):
    def __init__(self):
        super().__init__(
            table='balance',
            columns='bid, name, value, last_update',
            fields='''
            bid  INT PRIMARY KEY,
            name varchar(30) NOT NULL,
            value        INT NOT NULL,
            last_update  INT NOT NULL
            ''')
        from config import BALANCE_DICT
        for bid in BALANCE_DICT.keys():
            bal = self.find_one(bid)
            if bal:
                bal['name'] = BALANCE_DICT[bid]
                self.modify(bal)
            else:
                self.add({
                    'bid': bid,
                    'name': BALANCE_DICT[bid],
                    'value': 0,
                    'last_update': 0,
                })
        logger.info('BalanceDao Initialized')


    @staticmethod
    def row2item(r):
        return {
            'bid':          r[0],
            'name':         r[1],
            'value':        r[2],
            'last_update':  r[3]
        } if r else None


    def add(self, bal):
        with self._connect() as conn:
            try:
                conn.execute(
                    '''
                    INSERT INTO {0} ({1}) VALUES (?, ?, ?, ?)
                    '''.format(self._table, self._columns),
                    (bal['bid'], bal['name'], bal['value'], bal['last_update'])
                )
            except (sqlite3.DatabaseError) as e:
                logger.error(f'[BalanceDao.add] {e}')
                raise DatabaseError('添加记录失败')

    def find_one(self, bid):
        with self._connect() as conn:
            try:
                ret = conn.execute('''
                    SELECT {1} FROM {0} WHERE bid=?
                    '''.format(self._table, self._columns),
                    (bid,) ).fetchone()
                return self.row2item(ret)
            except (sqlite3.DatabaseError) as e:
                logger.error(f'[BalanceDao.find_one] {e}')
                raise DatabaseError('查找记录失败')


    def find_all(self):
        with self._connect() as conn:
            try:
                ret = conn.execute('''
                    SELECT {1} FROM {0}
                    '''.format(self._table, self._columns),
                    ).fetchall()
                return [self.row2item(r) for r in ret]
            except (sqlite3.DatabaseError) as e:
                logger.error(f'[BalanceDao.find_all] {e}')
                raise DatabaseError('查找记录失败')

    def modify(self, bal):
        with self._connect() as conn:
            try:
                conn.execute('''
                    UPDATE {0} SET value=?, last_update=? WHERE bid=?
                    '''.format(self._table),
                    (bal['value'], bal['last_update'], bal['bid'])
                )
            except (sqlite3.DatabaseError) as e:
                logger.error(f'[BalanceDao.modify] {e}')
                raise DatabaseError('修改记录失败')

    def modify_minus(self, bal):
        with self._connect() as conn:
            try:
                conn.execute('''
                    UPDATE {0} SET value=value-?, last_update=? WHERE bid=?
                    '''.format(self._table),
                    (bal['value'], bal['last_update'], bal['bid'])
                )
            except (sqlite3.DatabaseError) as e:
                logger.error(f'[BalanceDao.modify] {e}')
                raise DatabaseError('修改记录失败')

    def delete(self, bid):
        with self._connect() as conn:
            try:
                conn.execute('''
                    DELETE FROM {0} WHERE bid=?
                    '''.format(self._table),
                    (bid,) )
            except (sqlite3.DatabaseError) as e:
                logger.error(f'[BalanceDao.delete] {e}')
                raise DatabaseError('删除记录失败')
