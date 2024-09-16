# src/server/flask_app.py

from flask import Flask, send_file
import os

app = Flask(__name__)

@app.route('/get_cached_content')
def get_cached_content():
    file_path = os.path.join(os.path.dirname(__file__), '..', 'cached_content.csv')
    if os.path.exists(file_path):
        return send_file(file_path, mimetype='text/csv')
    else:
        return "Cached content file not found", 404