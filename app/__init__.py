from flask import Flask
from flask_bootstrap import Bootstrap
from flask_mail import Mail
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from config import config
from flask_login import LoginManager
from flask_pagedown import PageDown
from flask_simplemde import SimpleMDE
from flask_wtf.csrf import CSRFProtect

pagedown = PageDown()
bootstrap = Bootstrap()
csrf = CSRFProtect()
mail = Mail()
moment = Moment()
db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'


def create_app(config_name):
    try:
        app = Flask(__name__)
        app.config.from_object(config[config_name])
        config[config_name].init_app(app)
        csrf.init_app(app)
        bootstrap.init_app(app)
        mail.init_app(app)

        moment.init_app(app)
        db.init_app(app)
        login_manager.init_app(app)
        pagedown.init_app(app)
        SimpleMDE(app)

        if app.config['SSL_REDIRECT']:
            from flask_sslify import SSLify
            sslify = SSLify(app)

        from .main import main as main_blueprint
        app.register_blueprint(main_blueprint)

        from .auth import auth as auth_blueprint
        app.register_blueprint(auth_blueprint, url_prefix='/auth')

        from .api import api as api_blueprint
        app.register_blueprint(api_blueprint, url_prefix='/api/v1')

        return app
    except KeyError as e:
        if e.startswith('<flask.cli.ScriptInfo object'):
            print('Environmental variables may not be initialzied.\n \
                Try using scripts in \'tools\' directory first.')
