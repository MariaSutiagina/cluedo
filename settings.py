import os
import logging
from logging.handlers import RotatingFileHandler

import yaml




os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

INSTALLED_APPS = (
    'data',
)

CONFIG_PATH = os.getenv('CONFIG_PATH', 'config/config.yaml')
CONFIG_PATH = os.path.join(BASE_DIR, CONFIG_PATH)

with open(CONFIG_PATH, 'r') as f:
    config_yaml = yaml.safe_load(f.read())

API_TOKEN = os.getenv('BOT_TOKEN',config_yaml['telegram']['token'])

# webhook settings
WEBHOOK_HOST = config_yaml['telegram']['webhook_host']
WEBHOOK_PATH = config_yaml['telegram']['webhook_path']
WEBHOOK_PORT = config_yaml['telegram']['webhook_port']
WEBHOOK_CERT = config_yaml['telegram']['webhook_cert']
WEBHOOK_KEY = config_yaml['telegram']['webhook_key']


# webserver settings
WEBAPP_HOST = config_yaml['server']['host']
WEBAPP_PORT = config_yaml['server']['port']

# django secret key
SECRET_KEY = os.getenv('DJANGO_SECRET',config_yaml['django']['secret'])

ALLOWED_HOSTS = config_yaml['django']['allowed_hosts']

LOG_FILE = config_yaml['server']['log_file']

WEBHOOK_URL = f"{WEBHOOK_HOST}:{WEBHOOK_PORT}{WEBHOOK_PATH}"

LOG_FORMAT = '%(name)s - %(levelname)s - %(asctime)s # %(message)s'

logger = logging.getLogger()

log_handler = RotatingFileHandler(LOG_FILE, maxBytes=50 * 2 ** 20, backupCount=50)
                                  
log_handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt='%I:%M:%S'))

logger.addHandler(log_handler)
logger.setLevel(logging.INFO)
