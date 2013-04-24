#!/usr/bin/env python

from ctb import ctb_db, ctb_action

import sys
import logging
import gettext
import locale
import yaml
import sqlalchemy
import praw
import time
from pifkoin.bitcoind import Bitcoind, BitcoindException

logger = logging.getLogger('cointipbot')
logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)

class CointipBot(object):
    """
    Main class for cointip bot
    """
    _DEFAULT_CONFIG_FILENAME = './config.yml'
    _DEFAULT_SLEEP_TIME = 60*0.5
    _REDDIT_BATCH_LIMIT=10

    _config = None
    _mysqlcon = None
    _bitcoindcon = None
    _litecoindcon = None
    _ppcoindcon = None
    _redditcon = None

    def _init_localization(self):
        """
        Prepare localization
        """
        locale.setlocale(locale.LC_ALL, '')
        filename = "res/messages_%s.mo" % locale.getlocale()[0][0:2]
        try:
            logger.debug("Opening message file %s for locale %s", filename, locale.getlocale()[0])
            trans = gettext.GNUTranslations(open(filename, "rb"))
        except IOError:
            logger.debug("Locale not found (file %s, locale %s). Using default messages", filename, locale.getlocale()[0])
            trans = gettext.NullTranslations()
        trans.install()
        logger.debug(_("Testing localization..."))

    def _parse_config(self, filename=_DEFAULT_CONFIG_FILENAME):
        """
        Returns a Python object with CointipBot configuration

        :param filename:
            The filename from which the configuration should be read.
        """
        logger.debug("Parsing config file...")
        try:
            config = yaml.load(open(filename))
        except yaml.YAMLError, e:
            logger.error("Error reading config file "+filename)
            if hasattr(e, 'problem_mark'):
                logger.error("Error position: (line "+str(e.problem_mark.line+1)+", column "+str(e.problem_mark.column+1));
            sys.exit(1)
        logger.info("Config file has been read")
        return config

    def _connect_db(self, config):
        """
        Returns a database connection object
        """
        logger.debug("Connecting to MySQL...")
        dsn = "mysql+mysqldb://" + str(config['mysql-user']) + ":" + str(config['mysql-pass']) + "@" + str(config['mysql-host']) + ":" + str(config['mysql-port']) + "/" + str(config['mysql-db'])
        dbobj = ctb_db.CointipBotDatabase(dsn)
        try:
            conn = dbobj.connect()
        except sqlalchemy.SQLAlchemyError, e:
            logger.error("Error connecting to database: "+str(e))
            sys.exit(1)
        logger.info("Connected to database")
        return conn

    def _connect_bitcoind(self, config):
        """
        Returns a bitcoind connection object
        """
        logger.debug("Connecting to bitcoind...")
        try:
            conn = Bitcoind('~/.bitcoin/bitcoin.conf')
        except BitcoindException, e:
            logger.error("Error connecting to bitcoind: "+str(e))
            sys.exit(1)
        logger.info("Connected to bitcoind")
        return conn

    def _connect_litecoind(self, config):
        """
        Returns a litecoind connection object
        """
        logger.debug("Connecting to litecoind...")
        try:
            conn = Bitcoind('~/.litecoin/litecoin.conf')
        except BitcoindException, e:
            logger.error("Error connecting to litecoind: "+str(e))
            sys.exit(1)
        logger.info("Connected to litecoind")
        return conn

    def _connect_ppcoind(self, config):
        """
        Returns a ppcoind connection object
        """
        logger.debug("Connecting to ppcoind...")
        try:
            conn = Bitcoind('~/.ppcoin/bitcoin.conf')
        except BitcoindException, e:
            logger.error("Error connecting to ppcoind: "+str(e))
            sys.exit(1)
        logger.info("Connected to ppcoind")
        return conn

    def _connect_reddit(self, config):
        """
        Returns a praw connection object
        """
        logger.debug("Connecting to Reddit...")
        try:
            conn = praw.Reddit(user_agent = config['reddit-useragent'])
            conn.login(config['reddit-user'], config['reddit-pass'])
        except Exception, e:
            logger.error("Error connecting to Reddit: "+str(e))
            sys.exit(1)
        logger.info("Logged in to Reddit")
        return conn

    def __init__(self, config_filename=_DEFAULT_CONFIG_FILENAME):
        """
        Constructor.
        Parses configuration file and initializes bot.
        """
        # Localization
        self._init_localization()
        # Configuration file
        self._config = self._parse_config(config_filename)
        # MySQL
        self._mysqlcon = self._connect_db(self._config)
        # Coin daemons
        if not self._config['bitcoind-enabled'] and not self._config['litecoind-enabled'] and not self._config['ppcoind-enabled']:
            logger.error("Error: please enable at least one type of coin")
            sys.exit(1)
        if self._config['bitcoind-enabled']:
            self._bitcoindcon = self._connect_bitcoin(self._config)
        if self._config['litecoind-enabled']:
            self._litecoindcon = self._connect_litecoind(self._config)
        if self._config['ppcoind-enabled']:
            self._ppcoindcon = self._connect_ppcoin(self._config)
        # Reddit
        self._redditcon = self._connect_reddit(self._config)

    def _check_inbox(self):
        """
        Evaluate new messages in inbox
        """
        logger.debug("_check_inbox()")
        # Try to fetch some messages
        try:
            messages = self._redditcon.get_unread(limit=self._REDDIT_BATCH_LIMIT)
        except Exception, e:
            logger.error("_check_inbox(): couldn't fetch messages: %s", str(e))
            return False
        # Process messages
        for m in messages:
            # Ignore replies to bot's comments
            if m.was_comment:
                logger.debug("_check_inbox(): ignoring reply to bot's comments")
                m.mark_as_read()
                continue
            # Ignore self messages
            if m.author.name.lower() == self._config['reddit-user'].lower():
                logger.debug("_check_inbox(): ignoring message from self")
                m.mark_as_read()
                continue
            # Attempt to evaluate message
            action = self._eval_message(m)
            # Perform action if necessary
            if action != None:
                try:
                    action.do()
                    logger.debug("_check_inbox(): executed action %s from message_id %s", action.type(), str(m.id))
                except Exception, e:
                    logger.error("_check_inbox(): error executing action %s from message_id %s: %s", action.type(), str(m.id), str(e))
                    return False
            # Mark message as read
            m.mark_as_read()
        logger.debug("check_inbox() DONE")
        return True

    def _eval_message(self, _message):
        return None

    def main(self):
        """
        Main loop
        """
        while (True):
            logger.debug("Beginning main() iteration...")
            # Refresh exchange rates
            #ctb_misc._refresh_exchange_rate(_mysqlcon)
            # Check personal messages
            self._check_inbox()
            # Check subreddit comments for tips
            #self._check_subreddits(_redditcon, _mysqlcon)
            # Process transactions
            #ctb_misc._process_transactions(_mysqlcon)
            # Process outgoing messages
            #ctb_reddit._send_messages(_redditcon, _mysqlcon)
            # Sleep
            logger.debug("Sleeping for "+str(self._DEFAULT_SLEEP_TIME)+" seconds")
            time.sleep(self._DEFAULT_SLEEP_TIME)

