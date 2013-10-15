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

import logging, re, time
from pifkoin.bitcoind import Bitcoind, BitcoindException

lg = logging.getLogger('cointipbot')

class CtbCoin(object):
    """
    Coin class for cointip bot
    """

    conn = None
    conf = None

    def __init__(self, _conf = None):
        """
        Initialize CtbCoin with given parameters
            _conf is a coin config dictionary defined in sample-config.yml under 'cc'
        """

        # verify _conf is a config dictionary
        if not _conf or not _conf.has_key('name') or not _conf.has_key('conf-file'):
            raise Exception("CtbCoin::__init__(): _conf is empty or invalid")

        self.conf = _conf

        # connect to coin daemon
        try:
            lg.debug("CtbCoin::__init__(): connecting to %s...", self.conf['name'])
            self.conn = Bitcoind(self.conf['conf-file'])
        except BitcoindException as e:
            lg.error("CtbCoin::__init__(): error connecting to %s: %s", self.conf['name'], str(e))
            raise

        lg.info("CtbCoin::__init__():: connected to %s", self.conf['name'])

        # set transaction fee
        lg.info("Setting tx fee of %f", self.conf['txfee'])
        self.conn.settxfee(self.conf['txfee'])

    def getbalance(self, _user = None, _minconf = None):
        """
        Get user's tip or withdraw balance
            _minconf is number of confirmations to consider
        Returns (float) balance
        """
        lg.debug("CtbCoin::getbalance(%s, %s)", _user, _minconf)

        user = self._verify_user(_user=_user)
        minconf = self._verify_minconf(_minconf=_minconf)
        balance = float(0)

        try:
            balance = self.conn.getbalance(user, minconf)
        except BitcoindException as e:
            lg.error("CtbCoin.getbalance(): error getting %s (minconf=%s) balance for %s: %s", self.conf['name'], minconf, user, str(e))
            raise

        return float(balance)

    def sendtouser(self, _userfrom = None, _userto = None, _amount = None, _minconf = 1):
        """
        Transfer (move) coins to user
        Returns (bool)
        """
        lg.debug("CtbCoin::sendtouser(%s, %s, %s)", _userfrom, _userto, _amount)

        userfrom = self._verify_user(_user=_userfrom)
        userto = self._verify_user(_user=_userto)
        amount = self._verify_amount(_amount=_amount)

        # send request to coin daemon
        try:
            lg.info("CtbCoin::sendtouser(): moving %s %s from %s to %s", amount, self.conf['name'], userfrom, userto)
            result = self.conn.move(userfrom, userto, amount)
            time.sleep(1)
        except Exception as e:
            lg.error("CtbCoin::sendtouser(): error sending %s %s from %s to %s: %s", amount, self.conf['name'], userfrom, userto, str(e))
            return False

        return True

    def sendtoaddr(self, _userfrom = None, _addrto = None, _amount = None):
        """
        Send coins to address
        Returns (string) txid
        """
        lg.debug("CtbCoin::sendtoaddr(%s, %s, %s)", _userfrom, _addrto, _amount)

        userfrom = self._verify_user(_user=_userfrom)
        addrto = self._verify_addr(_addr=_addrto)
        amount = self._verify_amount(_amount=_amount)
        minconf = self._verify_minconf(_minconf=self.conf['minconf']['withdraw'])
        txid = ""

        # send request to coin daemon
        try:
            lg.info("CtbCoin::sendtoaddr(): sending %s %s from %s to %s", amount, self.conf['name'], userfrom, addrto)

            # Unlock wallet, if applicable
            if self.conf.has_key('walletpassphrase'):
                lg.debug("CtbCoin::sendtoaddr(): unlocking wallet...")
                self.conn.walletpassphrase(self.conf['walletpassphrase'], 1)

            # Perform transaction
            lg.debug("CtbCoin::sendtoaddr(): calling sendfrom()...")
            txid = self.conn.sendfrom(userfrom, addrto, amount, minconf)

            # Lock wallet, if applicable
            if self.conf.has_key('walletpassphrase'):
                lg.debug("CtbCoin::sendtoaddr(): locking wallet...")
                self.conn.walletlock()

            time.sleep(1)

        except Exception as e:
            lg.error("CtbCoin::sendtoaddr(): error sending %s %s from %s to %s: %s", amount, self.conf['name'], userfrom, addrto, str(e))
            raise

        return str(txid)

    def validateaddr(self, _addr = None):
        """
        Verify that _addr is a valid coin address
        Returns (bool)
        """
        lg.debug("CtbCoin::validateaddr(%s)", _addr)

        addr = self._verify_addr(_addr=_addr)
        addr_valid = self.conn.validateaddress(addr)

        if not addr_valid.has_key('isvalid') or not addr_valid['isvalid']:
            lg.debug("CtbCoin::validateaddr(%s): not valid", addr)
            return False
        else:
            lg.debug("CtbCoin::validateaddr(%s): valid", addr)
            return True

    def getnewaddr(self, _user = None):
        """
        Generate a new address for _user
        Returns (string) address
        """

        user = self._verify_user(_user=_user)
        addr = ""

        try:
            # Unlock wallet for keypoolrefill
            if self.conf.has_key('walletpassphrase'):
                self.conn.walletpassphrase(self.conf['walletpassphrase'], 1)
            # Generate address foruser
            addr = self.conn.getnewaddress(user)
            # Lock wallet
            if self.conf.has_key('walletpassphrase'):
                self.conn.walletlock()
        except BitcoindException as e:
            lg.error("CtbCoin::getnewaddr(%s): error: %s", user, str(e))
            raise

        if not addr:
            raise Exception("CtbCoin::getnewaddr(%s): empty addr", user)

        return str(addr)

    def _verify_user(self, _user = None):
        """
        Verify and return a username
        """

        if not _user or not type(_user) in [str, unicode]:
            raise Exception("CtbCoin::_verify_user(): _user wrong type (%s) or empty (%s)", type(_user), _user)

        return re.escape(_user.lower())

    def _verify_addr(self, _addr = None):
        """
        Verify and return coin address
        """

        if not _addr or not type(_addr) in [str, unicode]:
            raise Exception("CtbCoin::_verify_addr(): _addr wrong type (%s) or empty (%s)", type(_addr),_addr)

        return re.escape(_addr)

    def _verify_amount(self, _amount = None):
        """
        Verify and return amount
        """

        if not _amount or not type(_amount) in [int, float] or not _amount > 0:
            raise Exception("CtbCoin::_verify_amount(): _amount wrong type (%s), empty, or negative (%s)", type(_amount), _amount)

        return _amount

    def _verify_minconf(self, _minconf = None):
        """
        Verify and return minimum number of confirmations
        """

        if not _minconf or not type(_minconf) == int or not _minconf >= 0:
            raise Exception("CtbCoin::_verify_minconf(): _minconf wrong type (%s), empty, or negative (%s)", type(_minconf), _minconf)

        return _minconf
