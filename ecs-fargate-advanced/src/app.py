import os
import socket
import platform
from datetime import datetime, timezone
from flask import Flask, jsonify, request

app = Flask(__name__)

START_TIME = datetime.now(timezone.utc)


@app.route("/")
def index():
    return jsonify({
        "service": os.environ.get("SERVICE_NAME", "ecs-advanced-app"),
        "message": "ECS Fargate Advanced — Running",
        "container_id": socket.gethostname(),
        "environment": os.environ.get("ENVIRONMENT", "production"),
        "region": os.environ.get("AWS_DEFAULT_REGION", "us-east-1"),
        "version": os.environ.get("APP_VERSION", "2.0.0"),
    })


@app.route("/health")
def health():
    return jsonify({
        "status": "healthy",
        "uptime_seconds": int(
            (datetime.now(timezone.utc) - START_TIME).total_seconds()
        ),
        "container_id": socket.gethostname(),
    }), 200


@app.route("/info")
def info():
    return jsonify({
        "python_version": platform.python_version(),
        "platform": platform.system(),
        "container_id": socket.gethostname(),
        "environment_vars": {
            "SERVICE_NAME": os.environ.get("SERVICE_NAME", "not-set"),
            "ENVIRONMENT": os.environ.get("ENVIRONMENT", "not-set"),
            "APP_VERSION": os.environ.get("APP_VERSION", "not-set"),
        },
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
