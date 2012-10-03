
import logging


MONGO_HOST = 'localhost'
MONGO_PORT = 27017

TWITTER_ID = 15851927
TWITTER_SCREEN_NAME = 'loisaidasam'

TWITTER_CONSUMER_KEY = ""
TWITTER_CONSUMER_SECRET = ""
TWITTER_OAUTH_TOKEN = ""
TWITTER_OAUTH_TOKEN_SECRET = ""

EMAIL_FROM = "sender@example.com"
EMAIL_TO = "receiver@example.com"

# Logging stuff
def get_logger(name, logger_level=logging.DEBUG):
	logger = logging.getLogger(name)
	logger.setLevel(logger_level)
	fh = logging.FileHandler('tweeps.log')
	fh.setLevel(logging.DEBUG)
	ch = logging.StreamHandler()
	ch.setLevel(logging.DEBUG)
	formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
	fh.setFormatter(formatter)
	ch.setFormatter(formatter)
	logger.addHandler(fh)
	logger.addHandler(ch)
	return logger


from localsettings import *
