from flask import Flask, jsonify
from dataextract import scrape_pagasa_water_level
from pagasa_scraper import scrape_pagasa_rainfall
import pandas as pd
from datetime import datetime

app = Flask(__name__)

@app.route('/api/water-level', methods=['GET'])
def get_water_level():
    """API endpoint for water level data"""
    headers, data = scrape_pagasa_water_level()
    if data:
        return jsonify({
            "status": "success",
            "data": data,
            "timestamp": datetime.now().isoformat()
        })
    else:
        return jsonify({"status": "error", "message": "Failed to fetch data"}), 500

@app.route('/api/rainfall', methods=['GET'])
def get_rainfall():
    """API endpoint for rainfall data"""
    headers, data = scrape_pagasa_rainfall()
    if data:
        return jsonify({
            "status": "success",
            "data": data,
            "timestamp": datetime.now().isoformat()
        })
    else:
        return jsonify({"status": "error", "message": "Failed to fetch data"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)