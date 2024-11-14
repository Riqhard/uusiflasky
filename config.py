import os
from datetime import datetime
import pytz

basedir = os.path.abspath(os.path.dirname(__file__))
helsinki_tz = pytz.timezone('Europe/Helsinki')

def get_datetime(tz=helsinki_tz, format='%Y-%m-%d %H:%M:%S'):
    current_time = datetime.now(tz).strftime(format)
    print("current_time: " + current_time)
    return current_time



class Config:
    GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'Vaikeasti arvattavissa oleva salasana'
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.googlemail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', '587'))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in \
        ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    print("MAIL_USERNAME: "+MAIL_USERNAME)
    SOVELLUSMALLI_MAIL_SUBJECT_PREFIX = '[Sovellusmalli]'
    SOVELLUSMALLI_MAIL_SENDER = 'Sovellusmalli Admin <sovellusmalli@example.com>'
    SOVELLUSMALLI_ADMIN = os.environ.get('SOVELLUSMALLI_ADMIN')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    FS_POSTS_PER_PAGE = 25
    WTF_CSRF_ENABLED = True
    UPLOAD_FOLDER = 'profiilikuvat/'
    ALLOWED_EXTENSIONS = ['png','jpg','jpeg','gif']
    # Huom. MAX_CONTENT_LENGTH aiheuttaa HTTP-virheen Error 413 Request Entity Too Large
    # MAX_CONTENT_LENGTH = 2 * 1024 * 1024
    MAX_FILE_SIZE = 2 * 1024 * 1024
    KUVAPOLKU = os.path.join(os.path.abspath('.'),UPLOAD_FOLDER)
    print("KUVAPOLKU: "+KUVAPOLKU)
    GET_TIME = get_datetime

    @staticmethod
    def init_app(app):
        
        kuvapolku = app.config['KUVAPOLKU']
        if not os.path.exists(kuvapolku):
            try:
                os.makedirs(kuvapolku)
            except PermissionError as e:
                errmsg = f'Permission denied ({e}): Unable to create directory {kuvapolku}.'
                app.logger.exception(errmsg)

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'data-dev.sqlite')
    
class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or \
        'sqlite://'

class XamppConfig(Config):
    DEBUG = True
    DB_USERNAME= os.environ.get('DB_USERNAME') or 'root'
    DB_PASSWORD= os.environ.get('DB_PASSWORD') or ''
    DB_HOST= os.environ.get('DB_HOST') or 'localhost'
    DB_PORT= os.environ.get('DB_PORT') or '3306'
    DB_NAME= os.environ.get('DB_NAME') or 'sovellusmalli'
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://'+DB_USERNAME+':'+DB_PASSWORD+'@'+DB_HOST+':'+DB_PORT+'/'+DB_NAME
    print("SQLALCHEMY_DATABASE_URI: "+SQLALCHEMY_DATABASE_URI)

class ProductionConfig(XamppConfig):
    DEBUG = False
    DIR = '/home'
    KUVAPOLKU = os.path.join(DIR, Config.UPLOAD_FOLDER)

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'xampp': XamppConfig,
    'default': XamppConfig
}