web: gunicorn --worker-class eventlet -w 1 main:app
celery -A main:celery worker --loglevel=info
