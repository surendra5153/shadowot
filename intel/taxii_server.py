import base64
import json
import os
from flask import Flask, jsonify, request

app = Flask(__name__)

BUNDLES_DIR = os.environ.get("BUNDLES_DIR", "/app/intel/bundles")
TAXII_USER = os.environ.get("TAXII_USER", "shadowot")
TAXII_PASS = os.environ.get("TAXII_PASS", "shadowot")
COLLECTION_ID = "shadow-ot-indicators"


def _check_auth(req):
    auth = req.headers.get("Authorization", "")
    if not auth.startswith("Basic "):
        return False
    try:
        decoded = base64.b64decode(auth.split(" ", 1)[1]).decode("utf-8")
        user, password = decoded.split(":", 1)
        return user == TAXII_USER and password == TAXII_PASS
    except Exception:
        return False


@app.before_request
def require_basic_auth():
    if not _check_auth(request):
        return jsonify({"error": "unauthorized"}), 401


@app.get("/taxii/collections/")
def list_collections():
    return jsonify({
        "collections": [
            {"id": COLLECTION_ID, "title": "shadow-ot-indicators", "can_read": True, "can_write": False}
        ]
    })


@app.get(f"/taxii/collections/{COLLECTION_ID}/objects/")
def list_objects():
    os.makedirs(BUNDLES_DIR, exist_ok=True)
    objects = []
    for file_name in sorted(os.listdir(BUNDLES_DIR)):
        if not file_name.endswith(".json"):
            continue
        with open(os.path.join(BUNDLES_DIR, file_name), "r", encoding="utf-8") as handle:
            bundle = json.load(handle)
            objects.extend(bundle.get("objects", []))
    return jsonify({"objects": objects})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8002)
