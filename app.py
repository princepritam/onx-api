#!flask/bin/python
from flask import Flask,request,jsonify
from flask_restful import Api
from mongoengine import connect

from resources.user import UserResource

# TODO:move this
SECRET_KEY = "MaVericK"

connect("onx-api-db")
app = Flask(__name__)
app.config['PROPAGATE_EXCEPTIONS'] = True
app.secret_key = SECRET_KEY
api = Api(app)
# app.config.from_pyfile('the-config.cfg')
app.config['MONGODB_DB'] = 'onx-api-db'



api.add_resource(UserResource, '/user')

if __name__ == '__main__':
    app.run(debug=True)
