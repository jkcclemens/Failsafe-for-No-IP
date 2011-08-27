#!/usr/bin/python

###########################
### FAILOVER PROTECTION ###
### FOR ANY NO-IP SITE  ###
###########################

# Written in nano! Use nano, /usr/bin/nano

### THIS WILL OVERWRITE ANY NOIP CONFIGURATION FILE ALREADY MADE!!
# To prevent this, change the variable createconfig, in the config file, to False. Note that, however, this may change the way Failover works if you don't follow the instructions below.

### THIS UPDATES ALL HOSTS IN YOUR NOIP ACCOUNT!
# To prevent this, please run 'noip2 -C' and set up which hosts should be updated in case the checksite goes down.
# Then, set the variable createconfig to False in the config file

# You may not touch the following.

from os import path, system, getgid, getenv
from getopt import gnu_getopt
from commands import getoutput
from sys import argv
from ConfigParser import ConfigParser

version = '0.0.50'
siteisdown = False
failsafeison = False
oldip = ''
noipconfigfile = '/usr/local/etc/no-ip2.conf'
configfile = '%s/.fnip/config.cfg' % getenv('HOME')

# Define config creating function

def create_new_config(where):
	if path.exists(where):
		print "Path already exists!\nAborting."
		quit()
	a = open(where, 'w')
	a.write("""[FNIP]
checksite: example.com ; Site to check up on, no http:// or www.
failsafeip: 12.34.56.78 ; IP to set checksite to when it goes down
portnumber: 80 ; Number of times to ping the checksite
noipuser: your@email.com ; Your No-Ip email
noippass: yourpassword ; Your No-Ip password
createconfig: True ; Whether to create new config file, read above
""")
	a.close()

# Check arguments

cmdline_params = argv[1:]
opts, args = gnu_getopt(cmdline_params, 'hc:n:C:v', ['help', 'config=', 'noipconfig=', 'newconfig=', 'version'])

for option, parameter in opts:
	if option in ('-h', '--help'):
		print "Failsafe for No-IP (FNIP) v%s" % version
		print
		print "-h, --help\t\tShow this output."
		print "-c, --config=\t\tSpecify FNIP configuration file."
		print "-n, --noipconfig=\tSpecify No-IP DUC configuration file."
		print "-C, --newconfig=\tCreate new, empty configuration file for FNIP at specified location."
		print "-v, --version\t\tShow version of FNIP."
		print
		quit()
	if option in ('-c', '--config'):
		if path.exists(parameter):
			print "FNIP config file specified exists. Using it."
			configfile = parameter
		else:
			print "FNIP config file specified does not exist. Ignoring."
	if option in ('-n', '--noipconfig'):
		if path.exists(parameter):
			print "No-IP DUC config file specified exists. Using it."
			noipconfigfile = parameter
		else:
			print "No-IP DUC config file specified does not exist. Ignoring."
	if option in ('-C', '--newconfig'):
		if not parameter:
			print "Need location for new config file!\nAborting."
			quit()
		print "Creating blank config at \'%s\'" % parameter
		create_new_config(parameter)
		print "Done!"
		print
		quit()
	if option in ('-v', '--version'):
		print "Failsafe for No-IP (FNIP) v%s" % version
		print
		quit()

# Grab UID of user running script

uid = getgid()

# Checking if it is root

if uid != 0:
	print "You need to run this as root!"
	quit()

# Checking for FNIP config file, creating if not present

if not path.exists(configfile):
	if not path.exists('%s/.fnip' % getenv('HOME')):
		from os import mkdir
		mkdir('%s/.fnip' % getenv('HOME'))
		print "Created .fnip directory!"
	print "No FNIP configuration file found at \'%s\', creating it." % configfile
	create_new_config(configfile)
	print "Please edit \'%s\' prior to restarting Failsafe for No-IP again." % configfile
	print
	quit()

# Loading config file

config = ConfigParser()
config.read(configfile)
checksite = config.get('FNIP', 'checksite')
failsafeip = config.get('FNIP', 'failsafeip')
portnumber = config.get('FNIP', 'portnumber')
noipuser = config.get('FNIP', 'noipuser')
noippass = config.get('FNIP', 'noippass')
createconfig = config.get('FNIP', 'createconfig')

# Checking that the noip2 binary is present at /usr/bin/

if path.exists("/usr/bin/noip2") != True:
	print "You need to move the noip2 binary to /usr/bin/ before this program can work!"
	quit()

# Shows starting status messages.

print "Failsafe for '%s' has started!" % checksite
print

# Sees if failsafe is already on.

if path.exists('/root/.failsafeison'):
	failsafeison = True
	siteisdown = True
 
# Using nmap against the server and splitting results into readable format

nmapresults = getoutput('nmap -p %s %s' % (portnumber, checksite))
nmapresults = nmapresults.split('\n')

# Saving site IP

oldip = nmapresults[2].partition('(')
oldip = oldip[2].partition(')')
oldip = oldip[0]

# Processing each ping

if not failsafeison:
	for item in nmapresults:
		if 'Host seems down.' in item:
			print "RED ALERT! \'%s\' appears to be down!" % checksite
			siteisdown = True
		elif '0 hosts up' in item:
			print "RED ALERT! \'%s\' appears to be down!" % checksite
			siteisdown = True	
else:
	for item in nmapresults:
		if 'Host is up' in item:
			print 'It appears the site has come back up, restoring old IP.'
			a = file('/root/.failsafeison', 'r')
			oldip = a.read()
			oldip = oldip.replace('\n', '')
			a.close()
			print getoutput('/usr/bin/noip2 -c %s -i %s' % (noipconfigfile, oldip))
			failsafeison = False
			siteisdown = False

# Check if ping processing reported that the site is down
# If it is, update the site's DNS to the failsafe IP

if siteisdown:
	if not failsafeison:
		if createconfig:
			print getoutput('/usr/bin/noip2 -c %s -u %s -p %s -U 1 -Y -C' % (noipconfigfile, noipuser, noippass))
		print getoutput('/usr/bin/noip2 -c %s -i %s' % (noipconfigfile, failsafeip))
		failsafeison = True

if failsafeison:
	print "Fail safe enabled! Testing connectivity!"
	print "Pinging failsafe IP!"
	print getoutput('ping -c 3 %s' % failsafeip)
	print
	print "Pinging site!"
	print getoutput('ping -c 3 %s' % checksite)
	print
	print "Writing failsafe file!"
	a = file('/root/.failsafeison', 'w')
	a.write('%s' % oldip)
	a.close()
	print "Done!"
else:
	if path.exists('/root/.failsafeison'):
		system('rm /root/.failsafeison')

print
if failsafeison:
	print "Failsafe is on!"
else:
	print "Failsafe is not on!"
if siteisdown:
	print "The checksite is down!"
else:
	print "The checksite is up!"
print
print "Failsafe script has completed."

quit()
