import os
import socket
from flask import Flask, jsonify

app = Flask(__name__)


@app.route("/")
def hello():
    return jsonify({
        "message": "Hello from ECS Fargate!",
        "container_id": socket.gethostname(),
        "environment": os.environ.get("ENVIRONMENT", "development"),
        "version": "1.0.0",
    })


@app.route("/health")
def health():
    return jsonify({"status": "healthy"}), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
