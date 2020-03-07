"""Contains all classes related to app initialization.

Application launches with one of the options in the config dictionary
at the bottom of this file.

"""

import os
basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    """Houses all global configuration for the flask application."""

    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard to guess string'
    WTF_CSRF_SECRET_KEY = 'aeoiureaw5309843jagow394'
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.googlemail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', '587'))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in \
        ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    FLASKY_MAIL_SUBJECT_PREFIX = '[Flasky]'
    FLASKY_MAIL_SENDER = 'Flasky Admin <bentestflask@gmail.com>'
    FLASKY_ADMIN = os.environ.get('FLASKY_ADMIN')
    BLOGGING_URL_PREFIX = "/blog"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_RECORD_QUERIES = True
    FLASKY_POSTS_PER_PAGE = 20
    FLASKY_FOLLOWERS_PER_PAGE = 20
    FLASKY_COMMENTS_PER_PAGE = 20
    FLASKY_SLOW_DB_QUERY_TIME = 0.5
    SIMPLEMDE_JS_IIFE = True
    SIMPLEMDE_USE_CDN = True
    SSL_REDIRECT = False
    AJAX_ROOT_URL = 'localhost:5000'

    @staticmethod
    def init_app(app):
        """NEED TO EXPLORE WHAT THIS DOES.

        Args:
            app ([type]): [description]

        """
        pass


class DevelopmentConfig(Config):
    """Used to launch app in development mode.

    Args:
        Config (class): Activates configuration variables in Config class

    """

    DEBUG = True
    SERVER_NAME = 'localhost:5000'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'data-dev.sqlite')


class TestingConfig(Config):
    """Used to launch app in testing mode.

    Initializes fully functionality non-existent test database in memory.

    Args:
        Config (class): Activates configuration variables in Config class

    """

    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or \
        'sqlite://'
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    """Used to launch app in basic production mode.

    Args:
        Config (class): Activates configuration variables in Config class

    """

    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'data-dev.sqlite')

    @classmethod
    def init_app(cls, app):
        """Launch app using production configuration.

        Args:
            app (???): ???????

        """
        Config.init_app(app)

        # email errors to administrators
        import logging
        from logging.handlers import SMTPHandler
        credentials = None
        secure = None
        if getattr(cls, 'MAIL_USERNAME', None) is not None:
            credentials = (cls.MAIL_USERNAME, cls.MAIL_PASSWORD)
            if getattr(cls, 'MAIL_USER_TLS', None):
                secure = ()
            mail_handler = SMTPHandler(
                mailhost=(cls.MAIL_SERVER, cls.MAIL_PORT),
                fromaddr=cls.FLASKY_MAIL_SENDER,
                toaddrs=[cls.FLASKY_ADMIN],
                subject=cls.FLASKY_MAIL_SUBJECT_PREFIX + ' Application Error',
                credentials=credentials,
                secure=secure)
            mail_handler.setLevel(logging.ERROR)
            app.logger.addHandler(mail_handler)


class HerokuConfig(ProductionConfig):
    """Used to launch app in Heroku production mode.

    Set Heroku specific settings, then initializes ProductionConfig.

    Args:
        Config (class): Activates configuration variables in Config class

    """

    SSL_REDIRECT = True if os.environ.get('DYNO') else False

    @classmethod
    def init_app(cls, app):
        """Initialize ProductionConfig within HerokuConfig class.

        Args:
            app ([type]): [description]

        """
        ProductionConfig.init_app(app)

        # handle reverse proxy server headers
        from werkzeug.contrib.fixers import ProxyFix
        app.wsgi_app = ProxyFix(app.wsgi_app)

        # log to stderr
        import logging
        from logging import StreamHandler
        file_handler = StreamHandler()
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)


class DockerConfig(ProductionConfig):
    """Used to launch app in Docker production mode.

    Set Docker specific settings, then initializes ProductionConfig.

    Args:
        Config (class): Activates configuration variables in Config class

    """

    @classmethod
    def init_app(cls, app):
        """Initialize ProductionConfig within DockerConfig class.

        Args:
            app ([type]): [description]

        """
        ProductionConfig.init_app(app)

        # log to stderr
        import logging
        from logging import StreamHandler
        file_handler = StreamHandler()
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)


config = {
        'development': DevelopmentConfig,
        'testing': TestingConfig,
        'production': ProductionConfig,
        'heroku': HerokuConfig,
        'docker': DockerConfig,

        'default': DevelopmentConfig
        }
