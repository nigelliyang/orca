"""
.. moduleauthor:: Li, Wang <wangziqi@foreseefund.com>
"""

import pandas as pd

from base import UpdaterBase
import cax_sql


class CaxUpdater(UpdaterBase):
    """The updater class for collections 'cax', 'shares'"""

    def __init__(self, timeout=10):
        UpdaterBase.__init__(self, timeout)

    def pre_update(self):
        self.connect_jydb()

    def pro_update(self):
        return

        self.logger.debug('Ensuring index date_1_dname_1 on collection cax')
        self.db.cax.ensure_index([('date', 1), ('dname', 1)],
                unique=True, dropDups=True, background=True)
        self.logger.debug('Ensuring index dname_1_date_1 on collection cax')
        self.db.cax.ensure_index([('dname', 1), ('date', 1)],
                unique=True, dropDups=True, background=True)
        self.logger.debug('Ensuring index date_1_dname_1 on collection shares')
        self.db.shares.ensure_index([('date', 1), ('dname', 1)],
                unique=True, dropDups=True, background=True)
        self.logger.debug('Ensuring index dname_1_date_1 on collection shares')
        self.db.shares.ensure_index([('dname', 1), ('date', 1)],
                unique=True, dropDups=True, background=True)
        self.logger.debug('Ensuring index date_1 on collection dates')
        self.db.dates.ensure_index([('date', 1)],
                unique=True, dropDups=True, background=True)

    def update(self, date):
        """Update adjusting factors and shares structures for the **same** day before market open."""
        CMD = cax_sql.CMD0.format(date=date)
        self.logger.debug('Executing command:\n%s', CMD)
        self.cursor.execute(CMD)
        if date != list(self.cursor)[0][0]:
            self.logger.warning('%s is not a trading day?', date)
            return
        self.db.dates.update({'date': date}, {'date': date}, upsert=True)
        self._update(date, cax_sql.CMD1, cax_sql.dnames1, self.db.cax, float)
        self._update(date, cax_sql.CMD2, cax_sql.dnames2, self.db.shares, int)

    def _update(self, date, CMD, dnames, col, dtype):
        CMD = CMD.format(date=date)
        self.logger.debug('Executing command:\n%s', CMD)
        self.cursor.execute(CMD)
        df = pd.DataFrame(list(self.cursor))
        if len(df) == 0:
            self.logger.warning('No records found for %s on %s', col.name, date)
            return

        df.columns = ['sid'] + dnames
        df.index = df.sid

        for dname in dnames:
            key = {'dname': dname, 'date': date}
            col.update(key, {'$set': {'dvalue': df[dname].dropna().astype(dtype).to_dict()}}, upsert=True)
        self.logger.info('UPSERT documents for %d sids into (c: [%s]) of (d: [%s]) on %s',
                len(df), col.name, self.db.name, date)

if __name__ == '__main__':
    cax = CaxUpdater()
    cax.run()
