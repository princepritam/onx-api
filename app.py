#!flask/bin/python
from flask import Flask
from flask import request, jsonify
import json

app = Flask(__name__)

@app.route('/', methods=['GET'])
def home():
    return 'hello'

if __name__ == '__main__':
    app.run(debug=True)