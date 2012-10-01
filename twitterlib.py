
import datetime
import json
import logging
import time
import urllib
import urllib2

import settings


BASE_URL = 'http://api.twitter.com/1'

logger = settings.get_logger(__name__)


class TwitterLibException(Exception):
	pass

class TwitterLib(object):
	# Default for unauth'd req's
	# TODO: auth'd requests
	TOTAL_REQUESTS_PER_PERIOD = 150
	
	def __init__(self):
		rate_limit_ish = self.rate_limit_status()
		self.TOTAL_REQUESTS_PER_PERIOD = rate_limit_ish['hourly_limit']
		self.requests = rate_limit_ish['hourly_limit'] - rate_limit_ish['remaining_hits']
		logger.debug("%s remaining requests this hour - next reset time is %s" % (rate_limit_ish['remaining_hits'], rate_limit_ish['reset_time']))
	
	def _api_request(self, url, params):
		url = '%s/%s?%s' % (BASE_URL, url, urllib.urlencode(params))
		logger.debug("Making a GET request to %s" % url)
		f = urllib2.urlopen(url)
		return json.loads(f.read())
	
	def _rate_limited_api_request(self, url, params):
		# Timeout if we're at our max requests limit for the hour
		if self.requests > self.TOTAL_REQUESTS_PER_PERIOD:
			rate_limit_ish = self.rate_limit_status()
			reset_time = rate_limit_ish['reset_time_in_seconds']
			time_now = time.mktime(datetime.datetime.utcnow().timetuple())
			sleeptime = reset_time - time_now
			logger.info("Hit %s requests. Sleeping for %s seconds..." % (self.requests, sleeptime))
			time.sleep(sleeptime)
			logger.info("And we're back!")
			self.requests = 0
			self.reset_time = datetime.datetime.utcnow()
		
		result = self._api_request(url, params)
		self.requests += 1
		
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
		
		try:
			result = self._rate_limited_api_request('followers/ids.json', params)
		except urllib2.HTTPError, e:
			# Unauthorized - ok for now?
			if e.code == 401:
				logger.warning("Request is unauthorized: %s" % e)
				return []
			else:
				raise
		
		return result['ids']
