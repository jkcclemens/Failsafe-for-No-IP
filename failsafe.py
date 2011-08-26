#!/usr/bin/python

###########################
### FAILOVER PROTECTION ###
### FOR ANY NO-IP SITE  ###
###########################

# Magical version: v0.0.1
# Written in nano! Use nano, /usr/bin/nano

# /----------------\
# |   RUNS ONCE    |
# |   EVERY FIVE   |
# |   MINUTES BY   |
# |      CRON      |
# \----------------/

### THIS WILL OVERWRITE ANY NOIP CONFIGURATION FILE ALREADY MADE!!
# To prevent this, change the variable createconfig, below, to False. Note that, however, this may change the way Failover works if you don't follow the instructions below.

### THIS UPDATES ALL HOSTS IN YOUR NOIP ACCOUNT!
# To prevent this, please run 'noip2 -C' and set up which hosts should be updated in case the checksite goes down.
# Then, set the variable createconfig to False

### IMPORTANT VARIABLES ###
# You may touch the following.

checksite     = '' # Site to check up on, no http:// or www.
failsafeip    = '' # IP to set checksite to when it goes down
portnumber    = 80 # Number of times to ping the checksite
noipuser      = '' # Your No-Ip email
noippass      = '' # Your No-Ip password
createconfig  = True # Whether to create new config file, read above

# You may not touch the following.

siteisdown = False
failsafeison = False
oldip = ''
configfile = '/usr/local/etc/no-ip2.conf'

from os import path, system, getgid
from commands import getoutput
from sys import argv

# Check for config file

try:
	argv[1]
except:
	print "No No-IP DUC config file specified. Using default."
else:
	if argv[1] == '-h':
		print "Add the path to a separate No-IP DUC config file to use it instead of the default."
	else:
		configfile = argv[1] 

# Grab UID of user running script

uid = getgid()

# Checking if it is root

if uid != 0:
	print "You need to run this as root!"
	quit()

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

pingresults = getoutput('ping -c 1 %s' % checksite)
pingresults = pingresults.split('\n')
nmapresults = getoutput('nmap -p %s %s' % (portnumber, checksite))
nmapresults = nmapresults.split('\n')

# Saving site IP

oldip = pingresults[0].partition('(')
oldip = oldip[2].partition(')')
oldip = oldip[0]

# Processing each ping

if not failsafeison:
	for item in nmapresults:
		if 'Host seems down.' in item:
			print "RED ALERT! \'%s\' appears to be down!" % checksite
			#print "By reason of icmp_seq timout."
			siteisdown = True
#		elif 'unknown host' in item:
#			print "RED ALERT! \'%s\' appears to be down!" % checksite
#			print "By reason of unknown host error."
#			siteisdown = True
#		elif '100% packet loss' in item:
#			print "RED ALERT! \'%s\' appears to be down!" % checksite
#			print "By reason of 100% packet loss."
#			siteisdown = True
else:
	for item in nmapresults:
		if 'Interesting ports' in item:
			print 'It appears the site has come back up, restoring old IP.'
			a = file('/root/.failsafeison', 'r')
			oldip = a.read()
			oldip = oldip.replace('\n', '')
			a.close()
			print getoutput('/usr/bin/noip2 -i %s' % oldip)
			failsafeison = False
			siteisdown = False

# Check if ping processing reported that the site is down
# If it is, update the site's DNS to the failsafe IP

if siteisdown:
	if not failsafeison:
		if createconfig:
			print getoutput('/usr/bin/noip2 -u %s -p %s -U 1 -Y -C' % (noipuser, noippass))
		print getoutput('/usr/bin/noip2 -i %s' % failsafeip)
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
