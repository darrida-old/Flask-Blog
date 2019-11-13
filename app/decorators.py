import os
import click
from flask_migrate import Migrate
from app import create_app, db
from app.models import User, Role, Permission
from flask import abort
from functools import wraps
from flask_login import current_user

#app = create_app(os.getenv('FLASK_CONFIG') or 'default')
#migrate = Migrate(app, db)


#@app.shell_context_processor
#def make_shell_context():
#    return dict(db=db, User=User, Role=Role, Permission=Permission)


#@app.cli.command()
#@click.argument('test_names', nargs=-1)
#def test(test_names):
#    """Run the unit tests."""
#    import unittest
#    if test_names:
#        tests = unittest.TestLoader().loadTestsFromNames(test_names)
#    else:
#        tests = unittest.TestLoader().discover('tests')
#    unittest.TextTestRunner(verbosity=2).run(tests)
    

def permission_required(permission):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.can(permission):
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def admin_required(f):
    return permission_required(Permission.ADMIN)(f)