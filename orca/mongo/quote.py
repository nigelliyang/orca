"""
.. moduleauthor: Li, Wang <wangziqi@foreseefund.com>
"""

import numpy as np
import pandas as pd

from orca.mongo import KDayFetcher

from orca import (
        DB,
        DATES)


class QuoteFetcher(KDayFetcher):

    def __init__(self, **kwargs):
        self.collection = DB.quote
        KDayFetcher.__init__(self, **kwargs)

    @classmethod
    def fetch(self, dname, *args, **kwargs):
        """When ``dname`` is 'returnsN', ``args`` should be a tuple ``(N, startdate[, enddate[, backdays]])``

        :param int N: Number of days to calculate returns
        """

        if dname != 'returnsN':
            return super(QuoteFetcher, self).fetch(dname, *args, **kwargs)

        N, args = args[0], args[1:]
        if 'backdays' in kwargs:
            kwargs['backdays'] += N-1
        else:
            if len(args) == 3:
                kwargs['backdays'] = args[2] + N-1
                args = args[:2]
            else:
                kwargs['backdays'] = N-1
        ret = super(QuoteFetcher, self).fetch('returns', *args, **kwargs)
        retN = pd.rolling_apply(ret.fillna(0), N, lambda x: (1+x).cumprod()[-1] - 1.)
        retN[ret.isnull()] = np.nan
        return retN.iloc[N-1:]

    @classmethod
    def fetch_window(self, dname, *args, **kwargs):
        """When ``dname`` is 'returnsN', ``args`` should be a tuple ``(N, window)``.

        :param int N: Number of days to calculate returns
        """

        if dname != 'returnsN':
            return super(QuoteFetcher, self).fetch_window(dname, *args, **kwargs)

        print args
        N, window = args
        ext_window = DATES[DATES.index(window[0])-N+1: DATES.index(window[-1])+1]
        ret = super(QuoteFetcher, self).fetch_window('returns', ext_window, **kwargs)
        retN = pd.rolling_apply(ret.fillna(0), N, lambda x: (1+x).cumprod()[-1] - 1.)
        retN[ret.isnull()] = np.nan
        return retN.iloc[N-1:]

    @classmethod
    def fetch_history(self, dname, *args, **kwargs):
        """When ``dname`` is 'returnsN', ``args`` should be a tuple ``(N, date, backdays)``.

        :param int N: Number of days to calculate returns
        """

        if dname != 'returnsN':
            return super(QuoteFetcher, self).fetch_history(dname, *args, **kwargs)

        N, date, backdays = args
        ret = super(QuoteFetcher, self).fetch_history('returns', date, backdays+N-1, **kwargs)
        retN = pd.rolling_apply(ret.fillna(0), N, lambda x: (1+x).cumprod()[-1] - 1.)
        retN[ret.isnull()] = np.nan
        return retN.iloc[N-1:]

    @classmethod
    def fetch_daily(self, dname, *args, **kwargs):
        """When ``dname`` is 'returnsN', ``args`` should be a tuple ``(N, date[, offset])``

        :param int N: Number of days to calculate returns
        """

        if dname != 'returnsN':
            return super(QuoteFetcher, self).fetch_daily(dname, *args, **kwargs)

        N, date = args[:2]
        if 'offset' in kwargs:
            offset = kwargs.pop('offset')
        else:
            offset =  args[-1] if len(args) == 3 else 0
        kwargs['delay'] = offset
        ret = super(QuoteFetcher, self).fetch_history('returns', date, N, **kwargs)
        retN = (1+ret.fillna(0)).cumprod().iloc[-1] - 1.
        retN[ret.iloc[-1].isnull()] = np.nan
        return retN


QuoteFetcher.collection = DB.quote