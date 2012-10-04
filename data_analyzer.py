
import datetime
import operator

from jinja2 import Template

from data_collector import DataCollector
from emaillib import send_email
from models import FollowerModel
import settings
from twitterlib import TwitterLib


# Falloff per level, depending on how deep you go after each level
DEPRECIATION_PER_LEVEL = 0.8

# Number of tweeps to recommend
NUM_OF_RECOMMENDED_TWEEPS = 10

logger = settings.get_logger(__name__)


class DataAnalyzer(object):	
	def __init__(self):
		self.fm = FollowerModel()
		self.tl = TwitterLib()
	
	def analyze_data(self):
		logger.info("Analyzing tweeps...")
		
		# TODO: First find all the people I follow already
	        #dc = DataCollector(settings.TWITTER_ID)
		#dc.get_followers_helper(dc.user_id, 0, skip_new=False)

		# Now grab people who are already following me 
		# (so as not to recommend that I follow them)
		my_followers = []
		all_tweeps = self.fm.fetch_all()
		for tweep in all_tweeps:
			if tweep['level'] == 0:
				my_followers.append(tweep['id'])
		
		# Now calculate everyone else's scores...
		tweep_scores = {}
		all_tweeps = self.fm.fetch_all()
		for tweep in all_tweeps:
			for follower_id in tweep['followers']:
				if follower_id in my_followers:
					continue
				if follower_id not in tweep_scores:
					tweep_scores[follower_id] = 0
				tweep_scores[follower_id] += pow(DEPRECIATION_PER_LEVEL, tweep['level']-1)
		
		logger.info("Finished analyzing tweeps, now sorting them...")
		sorted_tweeps = sorted(tweep_scores.iteritems(), key=operator.itemgetter(1), reverse=True)
		
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
		logger.debug("plain text mail:\n%s" % email_txt)
		
		send_email(settings.EMAIL_FROM, settings.EMAIL_TO, subject, email_txt)

def main():
	da = DataAnalyzer()
	da.analyze_data()
	da.send_recommendation_email()


main()
