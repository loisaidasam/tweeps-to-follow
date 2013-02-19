tweeps-to-follow
================

Use Twitter's API to find out the tweople who will most likely follow you back after you follow them

Setup:
------
	$ cp localsettings.py.template localsettings.py

and then set up your twitter credentials

Usage:
------

Collect data (debug mode - one loop):
	$ python data_collector.py --debug

Collect data (forever - do this in a screen):
	$ python data_collector.py

Analyze data and send an email with recommendations:
	$ python data_analyzer.py

