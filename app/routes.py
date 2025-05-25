from flask import Blueprint, jsonify, request
import base64
import logging
from .psi_logic import simulate_server_response, process_client_reencrypted

bp = Blueprint("routes", __name__)
logger = logging.getLogger(__name__)

@bp.route("/health", methods=["GET"])
def health():
    return jsonify(status="ok"), 200

@bp.route("/psi", methods=["POST"])
def psi():
    if not request.is_json:
        return jsonify(error="Expected application/json"), 400

    data = request.get_json()
    client_request = data.get("client_request")
    if not client_request:
        return jsonify(error="Missing 'client_request' field"), 400

    try:
        decoded = base64.b64decode(client_request)
    except Exception:
        return jsonify(error="Invalid base64 in 'client_request'"), 400

    try:
        server_items = ["foo.com", "bar.com", "baz.net"]
        setup_b64, response_b64, server_request_b64 = simulate_server_response(decoded, server_items)
        return jsonify(
            server_setup=setup_b64,
            server_response=response_b64,
            server_request=server_request_b64
        ), 200
    except Exception as e:
        logger.exception("PSI processing failed")
        return jsonify(error="Server error during PSI generation"), 500

@bp.route("/client_response", methods=["POST"])
def client_response():
    if not request.is_json:
        return jsonify(error="Expected application/json"), 400

    data = request.get_json()
    encoded_items = data.get("reencrypted_server_items", [])
    try:
        intersection = process_client_reencrypted(encoded_items)
        return jsonify(intersection=intersection), 200
    except Exception as e:
        logger.exception("Error processing reencrypted elements")
        return jsonify(error="Failed to compute intersection"), 500

