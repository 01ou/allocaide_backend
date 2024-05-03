# __init__.py

import os
from flask import Flask
from flask_cors import CORS
from .extensions import db, login_manager, migrate

def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY') or 'default_secret_key',
        SQLALCHEMY_DATABASE_URI='sqlite:///' + os.path.join(app.instance_path, 'db.sqlite'),
        SQLALCHEMY_TRACK_MODIFICATIONS=False
    )

    if test_config is None:
        app.config.from_pyfile('config.py', silent=True)
    else:
        app.config.from_mapping(test_config)

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    login_manager.init_app(app)
    CORS(app)
    db.init_app(app)
    migrate.init_app(app, db)

    register_blueprints(app)

    app.add_url_rule('/', endpoint='index')

    return app

def register_blueprints(app):
    # Import and register blueprints here
    from .api import index, auth, task, workbook
    app.register_blueprint(index.bp)
    app.register_blueprint(auth.bp)
    app.register_blueprint(task.bp)
    app.register_blueprint(workbook.bp)