
import datetime
import math
import operator

from jinja2 import Template

from emaillib import send_email
from models import TweepModel
import settings
from twitterlib import TwitterLib


# Falloff per level, depending on how deep you go after each level
DEPRECIATION_PER_LEVEL = 0.8

# Number of tweeps to recommend
NUM_OF_RECOMMENDED_TWEEPS = 10

logger = settings.get_logger(__name__)


class DataAnalyzer(object):	
	def __init__(self):
		self.tm = TweepModel()
		self.tl = TwitterLib()
	
	
	def analyze_data(self):
		logger.info("Analyzing tweeps...")
		
		# Let's calculate us some scores!
		tweep_scores = {}
		tweep_data = {}
		all_tweeps = self.tm.fetch_all()
		for tweep in all_tweeps:
			# Ignore people who already follow us
			if tweep['level'] == 0:
				continue
			
			# For everyone else, add some juice
			if tweep['id'] not in tweep_scores:
				tweep_scores[tweep['id']] = 0
			tweep_scores[tweep['id']] += pow(DEPRECIATION_PER_LEVEL, tweep['level']-1)
			
			# Get a ratio to be applied later
			if tweep['id'] not in tweep_data:
				tweep_data[tweep['id']] = {
					'followers': tweep['followers'],
					'following': tweep['following'],
				}
		
		logger.info("Applying some heuristics...")
		
		# Now penalize scores based on: 
		# 	1. followers/following ratio
		# 	2. total people following
		for id, score in tweep_scores.iteritems():
			# TODO: is this right?
			penalize_effect_1 = 1.0 * tweep_data['followers'] / tweep_data['following']
			tweep_scores[id] *= penalize_effect_1
			
			# TODO: is this right?
			if tweep_data['following'] >= 10:
				penalize_effect_2 = math.log(tweep_data['following'], 10)
				tweep_scores[id] /= penalize_effect_2
		
		logger.info("Sorting...")
		sorted_tweeps = sorted(tweep_scores.iteritems(), key=operator.itemgetter(1))
		
		self.recommended_tweeps = []
		tweep_ids = [x[0] for x in sorted_tweeps[:NUM_OF_RECOMMENDED_TWEEPS]]
		tweeps = self.tl.get_user_info(tweep_ids)
		
		for i, tweep in enumerate(tweeps):
			tweep['tweep_score'] = sorted_tweeps[i][1]
			self.recommended_tweeps.append(tweep)
		
		logger.info("OK!")
	
	def send_recommendation_email(self):
		logger.info("Emailing tweep recommendations now...")
		
		today = datetime.date.today()
		subject = "Tweeps to follow for %s" % today
		
		context = {
			'twitter_user_name': settings.TWITTER_SCREEN_NAME,
			'day_of_week': today.strftime("%A"),
			'tweeps': self.recommended_tweeps,
		}
		template_text = open('templates/who_to_follow_email.txt', 'r').read()
		email_txt = Template(template_text).render(**context).encode('utf-8')
		
		send_email(settings.EMAIL_FROM, settings.EMAIL_TO, subject, email_txt)

def main():
	da = DataAnalyzer()
	da.analyze_data()
	da.send_recommendation_email()


main()