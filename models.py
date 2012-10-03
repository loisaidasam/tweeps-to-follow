
import datetime
import sys

from pymongo import Connection

from mongo_orm import Model
import settings


connection = Connection(settings.MONGO_HOST, settings.MONGO_PORT)
db = connection.tweeps


class FollowerModel(Model):
	'''
	Usage examples:
	>>> f = FollowerModel()
	
	>>> print f.create_or_update(foo='bar', id=12)
	{'foo': 'bar', 'id': 12, '_id': ObjectId('5068bea1af9e0e183148fa15')}
	
	>>> print f.fetch_one(12)
	{u'_id': ObjectId('5068bc2aaf9e0e17a99b3067'), u'foo': u'bar', u'id': 12}
	
	>>> print f.fetch_one(13)
	None
	'''
	
	model = db.followers_collection
	
	def fetch_one(self, id):
		return super(FollowerModel, self).fetch_one({"id": id})


	def save_followers(self, id, level, followers, timestamp=None):
		row = self.fetch_one(id) or {}
		row['id'] = id
		row['level'] = min(row.get('level', sys.maxint), level)
		row['followers'] = followers
		if 'followers_history' not in row:
			row['followers_history'] = []
		if 'followers_history_dates' not in row:
			row['followers_history_dates'] = []
		row['followers_history'].append(followers)
		if timestamp is None:
			timestamp = datetime.datetime.utcnow()
		row['followers_history_dates'].append(timestamp)
		return self.create_or_update(**row)
