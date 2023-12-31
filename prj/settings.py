from os import environ
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from flask_bcrypt import Bcrypt
from flask_caching import Cache
from flask_login import LoginManager

load_dotenv(dotenv_path=".env.docker")
# load_dotenv(dotenv_path=".env.local")

db = SQLAlchemy()
cache = Cache()
csrf = CSRFProtect()
bcrypt = Bcrypt()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'

SECRET_KEY = environ.get('SECRET_KEY')
APP_IP = environ.get('APP_IP')
APP_PORT = environ.get('APP_PORT') 
APP_DEBUG = environ.get('APP_DEBUG') == "True" 

DB_IP = environ.get('DB_IP')
DB_PORT = environ.get('DB_PORT')
DB_USERNAME =  environ.get('DB_USERNAME')
DB_PASSWORD = environ.get('DB_PASSWORD')
DB_NAME = environ.get('DB_NAME')

DB_CONNECTION_STRING = f'postgresql://{DB_USERNAME}:{DB_PASSWORD}@{DB_IP}:{DB_PORT}/{DB_NAME}'

MAIL_SERVER = environ.get('MAIL_SERVER')
MAIL_EMAIL = environ.get('MAIL_EMAIL')
MAIL_PASSWORD = environ.get('MAIL_PASSWORD')
MAIL_PORT = environ.get('MAIL_PORT')

FTP_HOST = environ.get('FTP_HOST')
FTP_USER = environ.get('FTP_USER')
FTP_PASSWORD = environ.get('FTP_PASSWORD')

CACHE_TYPE = environ.get('CACHE_TYPE')
CACHE_REDIS_HOST = environ.get('CACHE_REDIS_HOST')
CACHE_REDIS_PORT = environ.get('CACHE_REDIS_PORT')
CACHE_REDIS_DB = environ.get('CACHE_REDIS_DB')

YANDEX_ID_URL = environ.get('YANDEX_ID_URL')
YANDEX_ID_CLIENT_ID = environ.get('YANDEX_ID_CLIENT_ID')
YANDEX_ID_CLIENT_SECRET = environ.get('YANDEX_ID_CLIENT_SECRET')
YANDEX_ID_TOKEN_URL = environ.get('YANDEX_ID_TOKEN_URL')
YANDEX_ID_CALLBACK_URI = environ.get('YANDEX_ID_CALLBACK_URI')

IS_CODE_SEND_EMAIL = True
