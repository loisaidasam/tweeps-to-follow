
import datetime
import logging
import time

from models import FollowerModel
from optparse import OptionParser

from twitterlib import TwitterLib
import settings


# 0 is people who already follow you (root)
# 1 is people that follow them
# and so on...
MAX_DEPTH_LEVEL = 1

# How old of a record is considered "stale" 
# (duplicate API requests found more recently than this length of time ago are skipped)
STALE_AGE = 60 * 60 * 24 * 7

logger = settings.get_logger(__name__)


class DataCollector(object):
	
	def __init__(self, user_id):
		self.user_id = user_id
		self.fm = FollowerModel()
		self.tl = TwitterLib()
	
	def _get_followers_helper(self, id, level):
		# Skip requests that have been made too recently
		row = self.fm.get(id)
		if row:
			last_updated = row['followers_history_dates'][-1]
			if (datetime.datetime.utcnow() - last_updated).total_seconds() < STALE_AGE:
				return row['followers']
		
		# Make the actual API request
		followers = self.tl.get_followers(user_id=id)
		
		# Save the data
		data = self.fm.save_followers(id, level, followers)
		return data['followers']
		
	
	def _update_follower_tree(self, level, followers):
		'''Recursive breadth-first function for getting all followers
		'''
		if level > MAX_DEPTH_LEVEL:
			return
		logger.info("Updating %s followers at level %s..." % (len(followers), level))
		next_level_followers = set()
		for id in followers:
			their_followers = self._get_followers_helper(id, level)
			next_level_followers |= set(their_followers)
		logger.info("Finished updating all followers at level %s" % level)
		self._update_follower_tree(level+1, list(next_level_followers))
		
	
	def _update_followers(self):
		followers = self._get_followers_helper(self.user_id, 0)
		self._update_follower_tree(1, followers)
	
	def _main_loop(self):
		logger.debug("Main loop...")
		self._update_followers()
	
	def collect_data_once(self):
		self._main_loop()
	
	def collect_data_forever(self):
		while True:
			self._main_loop()


def do_args():
	parser = OptionParser()
	parser.add_option("-t",
		"--twitter-name", 
		dest="twittername",
		default=None,
		help="Do a lookup of a user's Twitter info"
	)
	parser.add_option("-r",
		"--rate-limit-status",
		action="store_true", 
		dest="ratelimitstatus",
		default=False,
		help="Do a lookup of rate limiting info"
	)
	parser.add_option(
		"-d", 
		"--debug",
		action="store_true", 
		dest="debug_mode", 
		default=False,
		help="Debug mode - only run through the loop once"
	)
	return parser.parse_args()


def main():
	options, args = do_args()
	if options.twittername:
		tl = TwitterLib()
		from pprint import pprint
		pprint(tl.show_user(options.twittername))
		return
	
	if options.ratelimitstatus:
		tl = TwitterLib()
		from pprint import pprint
		pprint(tl.rate_limit_status())
		return
	
	dc = DataCollector(settings.TWITTER_ID)
	if options.debug_mode:
		return dc.collect_data_once()
	dc.collect_data_forever()


if __name__ == "__main__":
	main()
