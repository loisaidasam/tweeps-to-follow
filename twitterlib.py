
import calendar
import datetime
import json
import logging
import time
import urllib
import urllib2

import settings


BASE_URL = 'http://api.twitter.com/1'
NUM_RETRIES = 3

logger = settings.get_logger(__name__)


class TwitterLibException(Exception):
	pass

class TwitterLib(object):
	# Default for unauth'd req's
	# TODO: auth'd requests
	total_requests_per_hour = 150
	
	def __init__(self):
		self._check_and_reset_rate_limits()
	
	def _check_and_reset_rate_limits(self):	
		rate_limit_ish = self.rate_limit_status()
		self.total_requests_per_hour = rate_limit_ish['hourly_limit']
		self.requests_left = rate_limit_ish['remaining_hits']
		logger.debug("%s remaining requests this hour - next reset time is %s" % (self.requests_left, rate_limit_ish['reset_time']))
	
	def _api_request(self, url, params):
		url = '%s/%s?%s' % (BASE_URL, url, urllib.urlencode(params))
		logger.debug("Making a GET request to %s" % url)
		f = urllib2.urlopen(url)
		return json.loads(f.read())
	
	def _rate_limited_api_request(self, url, params):
		logger.debug("%s/%s requests left" % (self.requests_left, self.total_requests_per_hour))
		# Timeout if we're at our max requests limit for the hour
		if self.requests_left <= 0:
			# Found this here: http://stackoverflow.com/questions/1595047/convert-to-utc-timestamp
			rate_limit_ish = self.rate_limit_status()
			reset_time = rate_limit_ish['reset_time_in_seconds']
			time_now = calendar.timegm(datetime.datetime.utcnow().utctimetuple())
			sleeptime = reset_time - time_now + 60
			logger.info("%s requests left. Sleeping for %s seconds..." % (self.requests_left, sleeptime))
			time.sleep(sleeptime)
			logger.info("And we're back!")
			while self.requests_left <= 0:
				self._check_and_reset_rate_limits()
				time.sleep(10)
		
		result = self._api_request(url, params)
		self.requests_left -= 1
		
		return result
	
	
	def rate_limit_status(self):
		return self._api_request('account/rate_limit_status.json', [])
		
	
	def show_user(self, user_id=None, screen_name=None):
		if (user_id is None and screen_name is None) or (user_id is not None and screen_name is not None):
			raise TwitterLibException("Pass either a user_id OR a screen_name dep!")
		
		params = {}
		if user_id:
			params['user_id'] = user_id
		elif screen_name:
			params['screen_name'] = screen_name
		
		return self._rate_limited_api_request('users/show.json', params)
	
	
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
				result = self._rate_limited_api_request('followers/ids.json', params)
				return result['ids']
			except urllib2.HTTPError, e:
				# Bad request, try again
				if e.code == 400:
					logger.warning("Bad request, maybe over limit per hour? %s" % e)
					pass
				# Unauthorized - ok for now?
				elif e.code == 401:
					logger.warning("Request is unauthorized: %s" % e)
					return []
				else:
					raise
			retries += 1
		
		if e is not None:
			raise e
		return []