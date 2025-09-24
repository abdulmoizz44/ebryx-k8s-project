from flask import Flask, render_template, jsonify, request
import os
import logging
from datetime import datetime
import sys

app = Flask(__name__)

# Configure logging for HTTP access logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)

# Create custom logger for access logs
access_logger = logging.getLogger('werkzeug')
access_logger.setLevel(logging.INFO)

# Application state to simulate readiness
app_ready = True
app_alive = True

@app.after_request
def log_request(response):
    """Log HTTP access details in a structured format"""
    access_logger.info(
        f'{request.remote_addr} - - [{datetime.now().strftime("%d/%b/%Y:%H:%M:%S %z")}] '
        f'"{request.method} {request.full_path if request.query_string else request.path} HTTP/1.1" '
        f'{response.status_code} {response.content_length or "-"} '
        f'"{request.headers.get("Referer", "-")}" "{request.headers.get("User-Agent", "-")}"'
    )
    return response

@app.route('/')
def index():
    """Main page with simple UI"""
    return render_template('index.html', 
                         current_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                         app_status="Running")

@app.route('/healthz')
def readiness_probe():
    """Readiness probe endpoint - checks if app is ready to serve traffic"""
    if app_ready:
        return jsonify({
            "status": "ready",
            "timestamp": datetime.now().isoformat(),
            "message": "Application is ready to serve traffic"
        }), 200
    else:
        return jsonify({
            "status": "not ready",
            "timestamp": datetime.now().isoformat(),
            "message": "Application is not ready to serve traffic"
        }), 503

@app.route('/failcheck')
def liveness_probe():
    """Liveness probe endpoint - checks if app is alive"""
    if app_alive:
        return jsonify({
            "status": "alive",
            "timestamp": datetime.now().isoformat(),
            "message": "Application is alive and healthy"
        }), 200
    else:
        return jsonify({
            "status": "dead",
            "timestamp": datetime.now().isoformat(),
            "message": "Application is not responding properly"
        }), 500

@app.route('/toggle-readiness')
def toggle_readiness():
    """Toggle readiness state for testing purposes"""
    global app_ready
    app_ready = not app_ready
    status = "ready" if app_ready else "not ready"
    return jsonify({
        "message": f"Readiness toggled to: {status}",
        "ready": app_ready
    })

@app.route('/toggle-liveness')
def toggle_liveness():
    """Toggle liveness state for testing purposes"""
    global app_alive
    app_alive = not app_alive
    status = "alive" if app_alive else "dead"
    return jsonify({
        "message": f"Liveness toggled to: {status}",
        "alive": app_alive
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
