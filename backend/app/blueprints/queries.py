"""Natural language query endpoints (Phase 9 implements the logic)."""
from flask import Blueprint, jsonify

queries_bp = Blueprint("queries", __name__, url_prefix="/api/queries")


def _todo(name: str):
    return jsonify({"success": False, "error": {"code": "NOT_IMPLEMENTED", "message": f"{name} is implemented in Phase 9"}}), 501


@queries_bp.route("", methods=["POST"])
def process_query():
    return _todo("natural language query")


@queries_bp.route("/history", methods=["GET"])
def query_history():
    return _todo("query history")
