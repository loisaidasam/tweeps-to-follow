
import calendar
import datetime
import logging
from optparse import OptionParser
from pprint import pprint
import time

from twython import Twython

import settings


NUM_RETRIES = 3

logger = settings.get_logger(__name__)


class TwitterLibException(Exception):
	pass

class TwitterLib(object):
	# Default for unauth'd req's
	# TODO: auth'd requests
	total_requests_per_hour = 150
	
	def __init__(self):
		self._setup_twython()
		self._check_and_reset_rate_limits()
		
	def _setup_twython(self):
		self.client = Twython(app_key=settings.TWITTER_CONSUMER_KEY,
            app_secret=settings.TWITTER_CONSUMER_SECRET,
            oauth_token=settings.TWITTER_OAUTH_TOKEN,
            oauth_token_secret=settings.TWITTER_OAUTH_TOKEN_SECRET)
	
	def _check_and_reset_rate_limits(self):	
		rate_limit_ish = self.client.getRateLimitStatus()
		self.total_requests_per_hour = rate_limit_ish['hourly_limit']
		self.requests_left = rate_limit_ish['remaining_hits']
		logger.debug("%s remaining requests this hour - next reset time is %s" % (self.requests_left, rate_limit_ish['reset_time']))
	
	def _rate_limited_api_request(self, twitter_func, *args, **kwargs):
		logger.debug("%s/%s requests left" % (self.requests_left, self.total_requests_per_hour))
		# Timeout if we're at our max requests limit for the hour
		if self.requests_left <= 0:
			# Found this here: http://stackoverflow.com/questions/1595047/convert-to-utc-timestamp
			rate_limit_ish = self.client.getRateLimitStatus()
			reset_time = rate_limit_ish['reset_time_in_seconds']
			time_now = calendar.timegm(datetime.datetime.utcnow().utctimetuple())
			sleeptime = reset_time - time_now + 60
			logger.info("%s requests left. Sleeping for %s seconds..." % (self.requests_left, sleeptime))
			time.sleep(sleeptime)
			logger.info("And we're back!")
			while self.requests_left <= 0:
				self._check_and_reset_rate_limits()
				time.sleep(10)
		
		try:
			result = twitter_func(*args, **kwargs)
		except:
			raise
		finally:
			# Always decrement this counter (there's ALWAYS money in the banana stand!)
			self.requests_left -= 1
		
		return result
	
	
	def rate_limit_status(self):
		return self.client.getRateLimitStatus()
		
	
	def show_user(self, user_id=None, screen_name=None):
		if (user_id is None and screen_name is None) or (user_id is not None and screen_name is not None):
			raise TwitterLibException("Pass either a user_id OR a screen_name dep!")
		
		params = {}
		if user_id:
			params['user_id'] = user_id
		elif screen_name:
			params['screen_name'] = screen_name
		
		return self._rate_limited_api_request(self.client.showUser, **params)
	
	
	def get_user_info(self, user_ids):
		user_ids_str = ",".join(map(str, user_ids))
		return self._rate_limited_api_request(self.client.lookupUser, user_id=user_ids_str)
		
	
	def get_followers(self, user_id=None, screen_name=None):
		if (user_id is None and screen_name is None) or (user_id is not None and screen_name is not None):
			raise TwitterLibException("Pass either a user_id OR a screen_name dep!")
		
		# TODO: use cursor, via https://dev.twitter.com/docs/misc/cursoring
		params = {'cursor': -1}
		
		if user_id:
			params['user_id'] = user_id
		elif screen_name:
			params['screen_name'] = screen_name
		
		retries = 0
		e = None
		while retries < NUM_RETRIES:
			try:
				result = self._rate_limited_api_request(self.client.getFollowersIDs, **params)
				return result['ids']
			except Exception, e:
				logger.error("Exception in get_followers on try #%s: %s" % (retries, e))
				raise
			retries += 1
		
		if e is not None:
			raise e
		return []


def main():
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
	options, args = parser.parse_args()
	
	if options.twittername:
		tl = TwitterLib()
		pprint(tl.show_user(screen_name=options.twittername))
		return
	
	if options.ratelimitstatus:
		tl = TwitterLib()
		pprint(tl.rate_limit_status())
		return

	parser.print_help()
	

if __name__ == "__main__":
	main()