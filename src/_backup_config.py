# Simple script to backup ALTcointip database

import sys, os, datetime
import cointipbot

if not len(sys.argv) in [2, 3] or not os.access(sys.argv[1], os.W_OK):
	print "Usgae: %s DIRECTORY [RSYNC-TO]" % sys.argv[0]
	print "(DIRECTORY must be writeable, RSYNC-TO is optional location to RSYNC the file to)"
	sys.exit(1)

cb = cointipbot.CointipBot(self_checks=False, init_reddit=False, init_coins=False, init_db=True)

_c = cb._config
_filename = "%s/config_%s.yml.gz" % (sys.argv[1], datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))

print "Backing up to %s..." % _filename
os.popen("cat config.yml | gzip --best -c >%s" % _filename)

try:
	print "Encrypting..."
	os.popen("echo %s | gpg --passphrase-fd 0 -c %s" % (_c['misc']['encryptionpassphrase'], _filename))
	os.popen("rm -f %s" % _filename)
	_filename += '.gpg'
except AttributeError:
	print "Not encrypting"

if len(sys.argv) == 3:
	print "Calling rsync..."
	os.popen("rsync -urltv %s %s" % (_filename, sys.argv[2]))
