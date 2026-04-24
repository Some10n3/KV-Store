from flask import Flask

from app.api.routes import kv_blueprint


def create_app() -> Flask:
    app = Flask(__name__)
    app.register_blueprint(kv_blueprint)
    return app


app = create_app()
