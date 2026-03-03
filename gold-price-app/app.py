import logging
import os
import time
from datetime import datetime, timezone

import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template
from flask_cors import CORS

load_dotenv()

app = Flask(__name__)
CORS(app)

app.logger.setLevel(logging.INFO)

API_KEY = os.getenv("GOLD_API_KEY", "")
API_URL = "https://www.goldapi.io/api/XAU/USD"
CACHE_TTL = 20
TIMEOUT_SECONDS = 6

_cache = {
    "expires_at": 0.0,
    "payload": None,
}


def _get_cached_payload():
    if _cache["payload"] and time.time() < _cache["expires_at"]:
        return _cache["payload"]
    return None


def _set_cache(payload):
    _cache["payload"] = payload
    _cache["expires_at"] = time.time() + CACHE_TTL


def _fetch_gold_price():
    if not API_KEY:
        raise RuntimeError("Missing GOLD_API_KEY environment variable")

    headers = {
        "x-access-token": API_KEY,
        "Content-Type": "application/json",
    }

    response = requests.get(API_URL, headers=headers, timeout=TIMEOUT_SECONDS)
    response.raise_for_status()
    data = response.json()

    price = data.get("price")
    change = data.get("ch")
    change_percent = data.get("chp")
    timestamp = data.get("timestamp")

    if price is None or change is None or change_percent is None:
        raise ValueError("Unexpected API response format")

    if timestamp:
        updated_at = datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat()
    else:
        updated_at = datetime.now(timezone.utc).isoformat()

    return {
        "symbol": "XAU/USD",
        "price": round(float(price), 2),
        "change_24h": round(float(change), 2),
        "change_percent_24h": round(float(change_percent), 2),
        "updated_at": updated_at,
        "source": "goldapi.io",
        "cached": False,
    }


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/gold")
def gold_price():
    try:
        cached_payload = _get_cached_payload()
        if cached_payload:
            payload = dict(cached_payload)
            payload["cached"] = True
            return jsonify(payload)

        payload = _fetch_gold_price()
        _set_cache(payload)
        app.logger.info("Fetched fresh gold price: %s", payload["price"])
        return jsonify(payload)
    except requests.RequestException as exc:
        app.logger.error("Gold API request failed: %s", exc)
        return jsonify({"error": "Failed to fetch gold price"}), 502
    except Exception as exc:  # noqa: BLE001
        app.logger.error("Unexpected error: %s", exc)
        return jsonify({"error": str(exc)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=False)
