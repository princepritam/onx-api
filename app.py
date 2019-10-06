#!flask/bin/python
from flask import Flask
from flask import request, jsonify
import json
from connect import db


app = Flask(__name__)


@app.route('/', methods=['GET'])
def home():
    return 'hello'


@app.route('/test', methods=['GET'])
def test():
    doc_ref = db.collection('test').document(u'doc')
    doc_ref.set({
        'first': 'Ada',
        'last': 'Lovelace',
        'born': 100000
    })
    return 'tested'


if __name__ == '__main__':
    app.run(debug=True)

