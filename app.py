#!flask/bin/python
# Python standard libraries
import json
import os
import code
from db import db
# Third party libraries
from flask import Flask, redirect, request, url_for, jsonify
from models.user import User
from models.session import *

app = Flask(__name__)

@app.route("/start_session/<int:session_id>",methods=['POST'])
def start_session(session_id):
    params = request.get_json()
    # schema = SessionSchema()
    # session = Session(session_id)
    # session.startSession()
    # result = schema.dump(session)
    # result_ = result.copy()
    # db.sessions.insert_one(result_)
    session = Session("princepritam@gmail.com",'Bob', 'Ross')
    session.save()
    # code.interact(local=dict(globals(), **locals()))
    return jsonify({'session':"successfully saved"})

# @app.route("/end_session/<int:session_id>",methods=['POST'])
# def end_session(session_id):
#     params = request.get_json()
#     session = db.sessions.find_one({"session_id":session_id})
#     session_ = Session.get_session(**session)
#     code.interact(local=dict(globals(), **locals()))
#     session_.endSession()

#     db.sessions.update_one({"session_id":session_id},{'$set':{'end_time': dt.datetime.now()}})
#     # schema = SessionSchema()
#     # result = schema.dump(session)
#     # result_ = result.copy()
#     # db.sessions.update(result_)
#     # return jsonify({'session':result})
#     return "hi"





if __name__ == '__main__':
    app.run(debug=True, port=3000, ssl_context="adhoc")
