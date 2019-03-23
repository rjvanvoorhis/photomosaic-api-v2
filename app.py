from flask import Flask
from api import api
from flask_cors import CORS


def initialize_app():
    application = Flask(__name__)
    application.config.from_pyfile('config/config.py', silent=False)
    api.init_app(application)
    CORS(application, resorces={r'/api/*': {"origins": '*'}})
    return application


if __name__ == '__main__':
    app = initialize_app()
    app.run(host='0.0.0.0', port=5050)
