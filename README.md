# A fork of Dogetipbot to facilitate asset tipping on Reddit.

I've unfortunately run into time constraints and can't continue development on the asset tipbot, but committing what I've done so far.   
   
I'll outline the changes I was aiming for:   
1) Simulated Reddit. This is simply a testing tool. It recreates a basic reddit environment as if it was connected through praw. With each request to reddit, it returns similarly formatted data, so that you can test the asset tipbot without having to be connected to Reddit, and have a tipbot activated account on the ready. Additionally, when in a testing environement it also uses test_conf instead of normal conf.  
  
There are several ways to add asset support. The one I've chosen is a bit of a hack with this codebase that will allow it to work without much effort (but isn't that clean). You don't have to rewrite the phrase regex matches. The idea is to have REGEX_COIN match an alphabet characters "[a-zA-Z]+" instead of the usual "doge, dogecoin, etc". It would thus match any alphabet characters in the "coin" part of the altcointip phrasing. ie "+/u/partybot 500 NACHOS" or "+/u/partyboy 500 doge" or "+/u/partybot 500 oaimwoimadw". When matched, it would then check with the original coin regex whether it is just dogecoin itself. ie is "NACHO" == "doge"? Is "doge" == "doge"? If so, it would then transfer the coins with the normal dogecoind. If it is not doge itself, it would then attempt to send the asset through dogepartyd. If there is an error, it wouldn't parse. In other words, as usual, dogepartyd would let the tipbot know there is either not enough or that the person who has the asset do not own it. For scalability, the additional option would be to store available assets by checking every 15min for new ones (get_asset_names). Luckily get_asset_names is not restricted to a certain amount (which is returned). Additionally, for more scalability, because new assets that are sent to the tipbot, would just then check each time since assets would not be sendable otherwise.  
  
Potential problems:  
1) Not sure what happens if the tipbot stores a lot of assets (get_balances only returns a 1000).
2) Depending on the desire to ad market information, doing conversions between asset prices to fiat IS possible. This will require dogeblockd as well. I'd rather just keep it out for now. Low liquidity in asset tipping is not ideal though (skews the use of fiat denomination).  
  
I've also started documenting the process to get a full setup running. It's quite extensive. You required a host of services to be synced properly: Dogecoind, Dogepartyd, Insight, Mongo, MySQL, etc. If you have any issues, don't hesitate to ask for help. I might have run into issues. The Dogeparty docker information is very useful (by Lars), however Dogeparty wasn't really set up to work on mac natively, so it requires quite some strong-arming to make it play nice.  

##Running Dogeparty on Mac OS X.

Here's the long install process as well as conf files that I went through to get it to run on OS X. https://gist.github.com/simondlr/9871056d4cb232a8aa16

----
((OLD README))
# It's dogetipbot!

## Introduction

dogetipbot is a fork of vindimy's ALTcointip bot, found at __https://github.com/vindimy/altcointip__

This is the version that's currently running on reddit at __http://www.reddit.com/r/dogetipbot/wiki/index__ 

v2 is being developed, but this is stable (for now). only minor patches will be added on to this repo as bugs are squashed.

note that this bot only accepts dogecoins.

The instructions below are from ALTcointip, but the instructions are the same. Cheers!

## ALTCointip Getting Started Instructions

### Python Dependencies

The following Python libraries are necessary to run ALTcointip bot:

* __jinja2__ (http://jinja.pocoo.org/)
* __pifkoin__ (https://github.com/dpifke/pifkoin)
* __praw__ (https://github.com/praw-dev/praw)
* __sqlalchemy__ (http://www.sqlalchemy.org/)
* __yaml__ (http://pyyaml.org/wiki/PyYAML)

You can install `jinja2`, `praw`, `sqlalchemy`, and `yaml` using `pip` (Python Package Index tool) or a package manager in your OS. For `pifkoin`, you'll need to copy or symlink its "python" subdirectory to `src/ctb/pifkoin`.

### Database

Create a new MySQL database instance and run included SQL file [altcointip.sql](altcointip.sql) to create necessary tables. Create a MySQL user and grant it all privileges on the database. If you don't like to deal with command-line MySQL, use `phpMyAdmin`.

### Coin Daemons

Download one or more coin daemon executable. Create a configuration file for it in appropriate directory (such as `~/.dogecoin/dogecoin.conf` for Dogecoin), specifying `rpcuser`, `rpcpassword`, `rpcport`, and `server=1`, then start the daemon. It will take some time for the daemon to download the blockchain, after which you should verify that it's accepting commands (such as `dogecoind getinfo` and `dogecoind listaccounts`).

### Reddit Account

You should create a dedicated Reddit account for your bot. Initially, Reddit will ask for CAPTCHA input when bot posts a comment or message. To remove CAPTCHA requirement, the bot account needs to accumulate positive karma.

### Configuration

Copy included set of configuration files [src/conf-sample/](src/conf-sample/) as `src/conf/` and edit `reddit.yml`, `db.yml`, `coins.yml`, and `regex.yml`, specifying necessary settings.

Most configuration options are described inline in provided sample configuration files.

### Running the Bot

1. Ensure MySQL is running and accepting connections given configured username/password
1. Ensure each configured coin daemon is running and responding to commands
1. Ensure Reddit authenticates configured user. _Note that from new users Reddit will require CAPTCHA responses when posting and sending messages. You will be able to type in CAPTCHA responses when required._
1. Execute `_start.sh` from [src](src/) directory. The command will not return for as long as the bot is running.

Here's the first few lines of DEBUG-level console output during successful initialization.

    user@host:/opt/altcointip/altcointip/src$ ./_start.sh
    INFO:cointipbot:CointipBot::init_logging(): -------------------- logging initialized --------------------
    DEBUG:cointipbot:CointipBot::connect_db(): connecting to database...
    INFO:cointipbot:CointipBot::connect_db(): connected to database altcointip as altcointip
    DEBUG:cointipbot:CtbCoin::__init__(): connecting to Peercoin...
    DEBUG:bitcoin:Read 5 parameters from /opt/altcointip/coins/ppcoin/ppcoin.conf
    DEBUG:bitcoin:Making HTTP connection to 127.0.0.1:19902
    INFO:cointipbot:CtbCoin::__init__():: connected to Peercoin
    INFO:cointipbot:Setting tx fee of 0.010000
    DEBUG:bitcoin:Starting "settxfee" JSON-RPC request
    DEBUG:bitcoin:Got 36 byte response from server in 4 ms
    DEBUG:cointipbot:CtbCoin::__init__(): connecting to Primecoin...
    DEBUG:bitcoin:Read 5 parameters from /opt/altcointip/coins/primecoin/primecoin.conf
    DEBUG:bitcoin:Making HTTP connection to 127.0.0.1:18772
    INFO:cointipbot:CtbCoin::__init__():: connected to Primecoin
    INFO:cointipbot:Setting tx fee of 0.010000
    DEBUG:bitcoin:Starting "settxfee" JSON-RPC request
    DEBUG:bitcoin:Got 36 byte response from server in 1 ms
    DEBUG:cointipbot:CtbCoin::__init__(): connecting to Megacoin...
    DEBUG:bitcoin:Read 5 parameters from /opt/altcointip/coins/megacoin/megacoin.conf
    DEBUG:bitcoin:Making HTTP connection to 127.0.0.1:17950
    INFO:cointipbot:CtbCoin::__init__():: connected to Megacoin
    INFO:cointipbot:Setting tx fee of 0.010000
    DEBUG:bitcoin:Starting "settxfee" JSON-RPC request
    DEBUG:bitcoin:Got 36 byte response from server in 1 ms
    DEBUG:cointipbot:CtbCoin::__init__(): connecting to Litecoin...
    DEBUG:bitcoin:Read 5 parameters from /opt/altcointip/coins/litecoin/litecoin.conf
    DEBUG:bitcoin:Making HTTP connection to 127.0.0.1:19332
    INFO:cointipbot:CtbCoin::__init__():: connected to Litecoin
    INFO:cointipbot:Setting tx fee of 0.020000
    DEBUG:bitcoin:Starting "settxfee" JSON-RPC request
    DEBUG:bitcoin:Got 36 byte response from server in 2 ms
    DEBUG:cointipbot:CtbCoin::__init__(): connecting to Namecoin...
    DEBUG:bitcoin:Read 5 parameters from /opt/altcointip/coins/namecoin/namecoin.conf
    DEBUG:bitcoin:Making HTTP connection to 127.0.0.1:18336
    INFO:cointipbot:CtbCoin::__init__():: connected to Namecoin
    INFO:cointipbot:Setting tx fee of 0.010000
    DEBUG:bitcoin:Starting "settxfee" JSON-RPC request
    DEBUG:bitcoin:Got 36 byte response from server in 1 ms
    DEBUG:cointipbot:CtbCoin::__init__(): connecting to Bitcoin...
    DEBUG:bitcoin:Read 5 parameters from /opt/altcointip/coins/bitcoin/bitcoin.conf
    DEBUG:bitcoin:Making HTTP connection to 127.0.0.1:18332
    INFO:cointipbot:CtbCoin::__init__():: connected to Bitcoin
    INFO:cointipbot:Setting tx fee of 0.000100
    DEBUG:bitcoin:Starting "settxfee" JSON-RPC request
    DEBUG:bitcoin:Got 36 byte response from server in 1 ms
    DEBUG:cointipbot:CtbExchange::__init__(): initialized exchange crypto-trade.com
    DEBUG:cointipbot:CtbExchange::__init__(): initialized exchange www.bitstamp.net
    DEBUG:cointipbot:CtbExchange::__init__(): initialized exchange bter.com
    DEBUG:cointipbot:CtbExchange::__init__(): initialized exchange blockchain.info
    DEBUG:cointipbot:CtbExchange::__init__(): initialized exchange campbx.com
    DEBUG:cointipbot:CtbExchange::__init__(): initialized exchange vircurex.com
    DEBUG:cointipbot:CtbExchange::__init__(): initialized exchange pubapi.cryptsy.com
    DEBUG:cointipbot:CtbExchange::__init__(): initialized exchange btc-e.com
    DEBUG:cointipbot:CointipBot::connect_reddit(): connecting to Reddit...
    INFO:cointipbot:CointipBot::connect_reddit(): logged in to Reddit as ALTcointip
    ...
    
ALTcointip bot is configured by default to append INFO-level log messages to `logs/info.log`, and WARNING-level log messages to `logs/warning.log`, while DEBUG-level log messages are output to the console.

### Cron: Backups

Backups are very important! The last thing you want is losing user wallets or records of transactions in the database. 

There are three simple backup scripts included that support backing up the database, wallets, and configuration files to local directory and (optionally) to a remote host with `rsync`. Make sure to schedule regular backups with cron and test whether they are actually performed. Example cron configuration:

    0 8,20 * * * cd /opt/altcointip/altcointip/src && python _backup_db.py ~/backups
    0 9,21 * * * cd /opt/altcointip/altcointip/src && python _backup_wallets.py ~/backups
    0 10 * * * cd /opt/altcointip/altcointip/src && python _backup_config.py ~/backups

### Cron: Statistics

ALTcointip bot can be configured to generate tipping statistics pages (overall and per-user) and publish them using subreddit's wiki. After you configure and enable statistics in configuration, add the following cron job to update the main statistics page periodically:

    0 */3 * * * cd /opt/altcointip/altcointip/src && python _update_stats.py
    
### What If I Want To Enable More Cryptocoins Later?

If you want to add a new cryptocoin after you already have a few registered users, you need to retroactively create the new cryptocoin address for users who have already registered. See [src/_add_coin.py](src/_add_coin.py) for details.
