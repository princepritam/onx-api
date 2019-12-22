from flask import Flask
from flask_socketio import SocketIO, emit
from celery import Celery
app = Flask(__name__)

app.config['CELERY_BROKER_URL_LOCAL'] = 'redis://localhost:6379/1'
app.config['CELERY_RESULT_BACKEND_LOCAL'] = 'redis://localhost:6379/1'
app.config['CELERY_BROKER_URL'] = 'redis://redistogo:45efe1ab922687bd6d3f31101e657317@barb.redistogo.com:10037/'
app.config['CELERY_RESULT_BACKEND'] = 'redis://redistogo:45efe1ab922687bd6d3f31101e657317@barb.redistogo.com:10037/'
celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

socketio = SocketIO(app, cors_allowed_origins="*")

emit = emit