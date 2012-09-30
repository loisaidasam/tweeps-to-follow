
import json
import urllib
import sys

class RawLibException(Exception):
	pass

def get_followers(user_id=None, screen_name=None):
	if user_id is None and screen_name is None:
		raise RawLibException("Pass either a user_id or a screen_name dep!")
	
	params = {'cursor': -1}
	if user_id:
		params['user_id'] = user_id
	if screen_name:
		params['screen_name'] = screen_name
	 
	url = 'http://api.twitter.com/1/followers/ids.json?%s' % urllib.urlencode(params)
	f = urllib.urlopen(url)
	return json.loads(f.read())
