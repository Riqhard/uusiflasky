from flask import Flask
from flask_bootstrap import Bootstrap
from flask_mail import Mail
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import OperationalError
from flask_login import LoginManager
from config import config, get_datetime
from flask_wtf import CSRFProtect
import logging
import sys
from datetime import datetime
import pytz

class FinnishFormatter(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        helsinki_tz = pytz.timezone('Europe/Helsinki')
        created_time = datetime.fromtimestamp(record.created, helsinki_tz)
        return created_time.strftime(datefmt or '%Y-%m-%d %H:%M:%S')

csrf = CSRFProtect()
bootstrap = Bootstrap()
mail = Mail()
moment = Moment()
# db = SQLAlchemy()
db = SQLAlchemy(session_options={"autoflush": False})
login_manager = LoginManager()
login_manager.login_view = 'auth.login'

# Luo logger ja aseta tason kattavuus
logger = logging.getLogger('flask_app')
logger.setLevel(logging.DEBUG)
# Luo handlerit eri lokitustasoille
# stdout handler INFO- ja DEBUG-tasoisille viesteille
# stdout_handler = logging.StreamHandler(sys.stdout)
# stdout_handler.setLevel(logging.INFO)
# stderr handler ERROR- ja CRITICAL-tasoisille viesteille
stderr_handler = logging.StreamHandler(sys.stderr)
stderr_handler.setLevel(logging.DEBUG)
# Määritä formatteri, joka lisätään kaikkiin handlereihin
formatter = FinnishFormatter('%Y-%m-%d %H:%M:%S - %(name)s - %(levelname)s - %(message)s')
# stdout_handler.setFormatter(formatter)
stderr_handler.setFormatter(formatter)
# Lisää handlerit loggeriin
# logger.addHandler(stdout_handler)
logger.addHandler(stderr_handler)
# Estä duplikaattien syntyminen
logger.propagate = False

def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    bootstrap.init_app(app)
    mail.init_app(app)
    moment.init_app(app)
    # db.init_app(app)
    try:
        db.init_app(app)
    except OperationalError as e:
        app.logger.error(f"VIRHE: Database connection failed: {e}")
        # Handle the error, e.g., show a user-friendly message or retry connection
        return None

    csrf.init_app(app)
    
    login_manager.init_app(app)
    # Set Moment.js locale to Finnish
    # @app.context_processor
    # def inject_moment_locale():
    #    return {'moment_locale': 'fi'}


    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')

    return app