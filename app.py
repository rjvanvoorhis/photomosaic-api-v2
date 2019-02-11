from flask import Flask
from api import api
from flask_cors import CORS
from flask_mail import Mail


def initialize_app():
    application = Flask(__name__)
    mail = Mail()
    application.config.from_pyfile('config/config.py', silent=False)
    api.init_app(application)
    mail.init_app(application)
    application.mail = mail
    # application.config.from_pyfile('config/config.py', silent=False)
    # application.config['CORS_HEADERS'] = 'Content-Type'
    cors = CORS(application, resorces={r'/api/*': {"origins": '*'}})
    return application


if __name__ == '__main__':
    app = initialize_app()
    app.run(host='0.0.0.0', port=5050)
