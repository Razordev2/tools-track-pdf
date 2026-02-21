#!/usr/bin/env python3
"""
Tracking Server untuk menerima notifikasi dari PDF
"""

from flask import Flask, request, jsonify
from datetime import datetime
import json
import os

app = Flask(__name__)
LOG_FILE = "pdf_access_log.json"

@app.route('/track', methods=['POST'])
def track_pdf():
    """Endpoint untuk menerima tracking data"""
    data = request.json
    
    # Tambahkan timestamp server
    data['server_time'] = str(datetime.now())
    
    # Tampilkan di console
    print("\n" + "="*50)
    print("🔔 PDF DI AKSES!")
    print(f"📧 User: {data.get('user', {}).get('email', 'Unknown')}")
    print(f"🆔 Tracking ID: {data.get('tracking_id', 'N/A')}")
    print(f"📁 File: {data.get('pdf', 'N/A')}")
    print(f"⏱️  Waktu: {data.get('time', 'N/A')}")
    print("="*50)
    
    # Simpan ke file
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'r') as f:
            logs = json.load(f)
    else:
        logs = []
    
    logs.append(data)
    
    with open(LOG_FILE, 'w') as f:
        json.dump(logs, f, indent=2)
    
    return jsonify({"status": "success", "message": "PDF access logged"})

@app.route('/logs', methods=['GET'])
def view_logs():
    """Lihat semua log"""
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'r') as f:
            logs = json.load(f)
        return jsonify(logs)
    return jsonify([])

@app.route('/stats', methods=['GET'])
def get_stats():
    """Dapatkan statistik"""
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'r') as f:
            logs = json.load(f)
        
        stats = {
            'total_access': len(logs),
            'unique_users': len(set([l.get('user', {}).get('email') for l in logs])),
            'last_access': logs[-1]['server_time'] if logs else None
        }
        return jsonify(stats)
    return jsonify({'total_access': 0})

if __name__ == '__main__':
    print("🚀 Tracking Server running on http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)