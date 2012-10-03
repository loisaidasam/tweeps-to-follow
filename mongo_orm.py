
# ORM Classes
class Model(object):
	model = None
	
	def create_or_update(self, **data):
		self.model.insert(data)
		return data
	
	def fetch_one(self, criteria):
		return self.model.find_one(criteria)

	def fetch_all(self):
		return self.model.find()