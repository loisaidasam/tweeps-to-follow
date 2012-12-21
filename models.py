
import datetime
import sys

from pymongo import Connection

from mongo_orm import Model
import settings


connection = Connection(settings.MONGO_HOST, settings.MONGO_PORT)
db = connection.tweeps


class TweepModel(Model):
	'''
	Usage examples:
	>>> f = TweepModel()
	
	>>> print f.create_or_update(foo='bar', id=12)
	{'foo': 'bar', 'id': 12, '_id': ObjectId('5068bea1af9e0e183148fa15')}
	
	>>> print f.fetch_one(12)
	{u'_id': ObjectId('5068bc2aaf9e0e17a99b3067'), u'foo': u'bar', u'id': 12}
	
	>>> print f.fetch_one(13)
	None
	'''
	
	model = db.tweep_collection
	
	def fetch_one(self, id):
		return super(TweepModel, self).fetch_one({"id": id})


	def save_tweep(self, id, level, followers, following, timestamp=None):
		row = self.fetch_one(id) or {}
		row['id'] = id
		row['level'] = min(row.get('level', sys.maxint), level)
		
		if timestamp is None:
			timestamp = datetime.datetime.utcnow()
		
		row['followers'] = followers
		if 'followers_history' not in row:
			row['followers_history'] = {}
		row['followers_history'][timestamp] = followers
		
		row['following'] = following
		if 'following_history' not in row:
			row['following_history'] = {}
		row['following_history'][timestamp] = following
		
		return self.create_or_update(**row)
