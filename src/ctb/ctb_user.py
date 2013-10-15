"""
    This file is part of ALTcointip.

    ALTcointip is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    ALTcointip is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with ALTcointip.  If not, see <http://www.gnu.org/licenses/>.
"""

import ctb_misc

import logging, time, praw, re

from requests.exceptions import HTTPError
from praw.errors import ExceptionList, APIException, InvalidCaptcha, InvalidUser, RateLimitExceeded
from socket import timeout

lg = logging.getLogger('cointipbot')

class CtbUser(object):
    """
    User class for cointip bot
    """

    # Basic properties
    _NAME=None
    _GIFTAMNT=None
    _JOINDATE=None
    _ADDR={}
    _TRANS={}
    _IS_BANNED=False

    # Objects
    _REDDITOBJ=None
    _CTB=None
    _CC=None

    def __init__(self, name=None, redditobj=None, ctb=None):
        """
        Initialize CtbUser object with given parameters
        """
        lg.debug("> CtbUser::__init__(%s)", name)

        if not bool(name):
            raise Exception("CtbUser::__init__(): name must be set")
        self._NAME = name

        if not bool(ctb):
            raise Exception("CtbUser::__init__(): ctb must be set")
        self._CTB = ctb
        self._CC = self._CTB._config['cc']

        if bool(redditobj):
            self._REDDITOBJ = redditobj

        # Determine if user is banned
        if ctb._config['reddit'].has_key('banned_users'):
            if ctb._config['reddit']['banned_users']['method'] == 'subreddit':
                for u in cb._redditcon.get_banned(ctb._config['reddit']['subreddit']):
                    if self._NAME.lower() == u.name.lower():
                        self._IS_BANNED = True
            elif ctb._config['reddit']['banned_users']['method'] == 'list':
                for u in ctb._config['reddit']['banned_users']['list']:
                    if self._NAME.lower() == u.lower():
                        self._IS_BANNED = True
            else:
                lg.warning("CtbUser::__init__(): invalid method '%s' in banned_users config" % ctb._config['reddit']['banned_users']['method'])

        lg.debug("< CtbUser::__init__(%s) DONE", name)

    def __str__(self):
        """
        Return string representation of self
        """
        me = "<CtbUser: name=%s, giftamnt=%s, joindate=%s, addr=%s, trans=%s, redditobj=%s, ctb=%s, banned=%s>"
        me = me % (self._NAME, self._GIFTAMNT, self._JOINDATE, self._ADDR, self._TRANS, self._REDDITOBJ, self._CTB, self._IS_BANNED)
        return me

    def get_balance(self, coin=None, kind=None):
        """
        If coin is specified, return float with coin balance for user
        Else, return a dict with balance of each coin for user
        """
        lg.debug("> CtbUser::balance(%s)", self._NAME)

        if not bool(coin) or not bool(kind):
            raise Exception("CtbUser::balance(%s): coin or kind not set" % self._NAME)

        # Ask coin daemon for account balance
        lg.info("CtbUser::balance(%s): getting %s %s balance", self._NAME, coin, kind)
        balance = self._CTB._coins[coin].getbalance(_user=self._NAME, _minconf=self._CC[coin]['minconf'][kind])

        lg.debug("< CtbUser::balance(%s) DONE", self._NAME)
        return float(balance)

    def get_addr(self, coin=None):
        """
        Return coin address of user
        """
        lg.debug("> CtbUser::get_addr(%s, %s)", self._NAME, coin)

        if hasattr(self._ADDR, coin):
            return self._ADDR[coin]

        sql = "SELECT address from t_addrs WHERE username = %s AND coin = %s"
        mysqlrow = self._CTB._mysqlcon.execute(sql, (self._NAME.lower(), coin.lower())).fetchone()
        if mysqlrow == None:
            lg.debug("< CtbUser::get_addr(%s, %s) DONE (no)", self._NAME, coin)
            return None
        else:
            self._ADDR[coin] = mysqlrow['address']
            lg.debug("< CtbUser::get_addr(%s, %s) DONE (%s)", self._NAME, coin, self._ADDR[coin])
            return self._ADDR[coin]

        lg.debug("< CtbUser::get_addr(%s, %s) DONE (should never happen)", self._NAME, coin)
        return None

    def get_tx_history(self, coin=None):
        """
        Return a dict with user transactions
        """
        return None

    def is_on_reddit(self):
        """
        Return true if user is on Reddit
        Also set _REDDITOBJ pointer while at it
        """
        lg.debug("> CtbUser::is_on_reddit(%s)", self._NAME)

        # Return true if _REDDITOBJ is already set
        if bool(self._REDDITOBJ):
            lg.debug("< CtbUser::is_on_reddit(%s) DONE (yes)", self._NAME)
            return True

        while True:
            # This loop retries if Reddit is down
            try:
                self._REDDITOBJ = self._CTB._redditcon.get_redditor(self._NAME)
                lg.debug("< CtbUser::is_on_reddit(%s) DONE (yes)", self._NAME)
                return True
            except (HTTPError, RateLimitExceeded) as e:
                lg.warning("CtbUser::is_on_reddit(%s): Reddit is down (%s), sleeping...", self._NAME, str(e))
                time.sleep(self._CTB._DEFAULT_SLEEP_TIME)
                pass
            except timeout:
                lg.warning("CtbUser::is_on_reddit(%s): Reddit is down (timeout), sleeping...", self._NAME)
                time.sleep(self._CTB._DEFAULT_SLEEP_TIME)
                pass
            except Exception as e:
                lg.debug("< CtbUser::is_on_reddit(%s) DONE (no)", self._NAME)
                return False

        lg.warning("< CtbUser::is_on_reddit(%s): returning None (shouldn't happen)", self._NAME)
        return None

    def is_registered(self):
        """
        Return true if user is registered with CointipBot
        """
        lg.debug("> CtbUser::is_registered(%s)", self._NAME)

        try:
            # First, check t_users table
            sql = "SELECT * FROM t_users WHERE username = %s"
            mysqlrow = self._CTB._mysqlcon.execute(sql, (self._NAME.lower())).fetchone()
            if mysqlrow == None:
                lg.debug("< CtbUser::is_registered(%s) DONE (no)", self._NAME)
                return False
            else:
                # Next, check t_addrs table
                sql_coins = "SELECT COUNT(*) AS count FROM t_addrs WHERE username = %s"
                mysqlrow_coins = self._CTB._mysqlcon.execute(sql_coins, (self._NAME.lower())).fetchone()
                if int(mysqlrow_coins['count']) != len(self._CTB._coins):
                    raise Exception("CtbUser::is_registered(%s): database returns %s coins but %s active" % (self._NAME, mysqlrow_coins['count'], len(self._CTB._coins)))
                # Set some properties
                self._GIFTAMNT = mysqlrow['giftamount']
                # Done
                lg.debug("< CtbUser::is_registered(%s) DONE (yes)", self._NAME)
                return True
        except Exception, e:
            lg.error("CtbUser::is_registered(%s): error while executing <%s>: %s", self._NAME, sql % self._NAME.lower(), str(e))
            raise

        lg.warning("< CtbUser::is_registered(%s): returning None (shouldn't happen)", self._NAME)
        return None

    def tell(self, subj=None, msg=None, msgobj=None):
        """
        Send a Reddit message to user
        """
        lg.debug("> CtbUser::tell(%s)", self._NAME)

        if not bool(subj) or not bool(msg):
            raise Exception("CtbUser::tell(%s): subj or msg not set", self._NAME)

        if not self.is_on_reddit():
            raise Exception("CtbUser::tell(%s): not a Reddit user", self._NAME)

        if bool(msgobj):
            lg.debug("CtbUser::tell(%s): replying to message", msgobj.id)
            ctb_misc._praw_call(msgobj.reply, msg)
        else:
            lg.debug("CtbUser::tell(%s): sending message", self._NAME)
            ctb_misc._praw_call(self._REDDITOBJ.send_message, subj, msg)

        lg.debug("< CtbUser::tell(%s) DONE", self._NAME)
        return True

    def register(self):
        """
        Add user to database and generate coin addresses
        """
        lg.debug("> CtbUser::register(%s)", self._NAME)

        _cc = self._CTB._config['cc']

        # Add user to database
        try:
            sql_adduser = "INSERT INTO t_users (username) VALUES (%s)"
            mysqlexec = self._CTB._mysqlcon.execute(sql_adduser, (self._NAME.lower()))
            if mysqlexec.rowcount <= 0:
                raise Exception("CtbUser::register(%s): rowcount <= 0 while executing <%s>" % ( self._NAME, sql_adduser % (self._NAME.lower())))
        except Exception, e:
            lg.error("CtbUser::register(%s): exception while executing <%s>: %s", self._NAME, sql_adduser % (self._NAME.lower()), str(e))
            raise

        # Get new coin addresses
        new_addrs = {}
        for c in self._CTB._coins:
            new_addrs[c] = self._CTB._coins[c].getnewaddress(_user=self._NAME)
            lg.info("CtbUser::register(%s): got %s address %s", self._NAME, c, new_addrs[c])

        # Add coin addresses to database
        for c in new_addrs:
            try:
                sql_addr = "REPLACE INTO t_addrs (username, coin, address) VALUES (%s, %s, %s)"
                mysqlexec = self._CTB._mysqlcon.execute(sql_addr, (self._NAME.lower(), c, new_addrs[c]))
                if mysqlexec.rowcount <= 0:
                    # Undo change to database
                    _delete_user(self._NAME, self._CTB._mysqlcon)
                    raise Exception("CtbUser::register(%s): rowcount <= 0 while executing <%s>" % (self._NAME, sql_addr % (self._NAME.lower(), c, new_addrs[c])))
            except Exception, e:
                # Undo change to database
                _delete_user(self._NAME, self._CTB._mysqlcon)
                raise

        lg.debug("< CtbUser::register(%s) DONE", self._NAME)
        return True


def _delete_user(_username, _mysqlcon):
    """
    Delete _username from t_users and t_addrs tables
    """
    lg.debug("> _delete_user(%s)", _username)
    try:
        sql_arr = ["DELETE from t_users WHERE username = %s",
                   "DELETE from t_addrs WHERE username = %s"]
        for sql in sql_arr:
            mysqlexec = _mysqlcon.execute(sql, _username.lower())
            if mysqlexec.rowcount <= 0:
                lg.warning("_delete_user(%s): rowcount <= 0 while executing <%s>", _username, sql % _username.lower())
    except Exception, e:
        lg.error("_delete_user(%s): error while executing <%s>: %s", _username, sql % _username.lower(), str(e))
        raise
    lg.debug("< _delete_user(%s) DONE", _username)
    return True
