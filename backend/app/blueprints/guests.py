"""Guest management endpoints (Phase 5 implements the logic)."""
from flask import Blueprint, jsonify

guests_bp = Blueprint("guests", __name__, url_prefix="/api/guests")


def _todo(name: str):
    return jsonify({"success": False, "error": {"code": "NOT_IMPLEMENTED", "message": f"{name} is implemented in Phase 5"}}), 501


@guests_bp.route("", methods=["POST"])
def register_guest():
    return _todo("guest registration")


@guests_bp.route("/batch", methods=["POST"])
def batch_register():
    return _todo("batch registration")


@guests_bp.route("", methods=["GET"])
def list_guests():
    return _todo("list guests")


@guests_bp.route("/search", methods=["GET"])
def search_guests():
    return _todo("search guests")


@guests_bp.route("/<guest_id>", methods=["GET"])
def get_guest(guest_id):
    return _todo("get guest")


@guests_bp.route("/<guest_id>", methods=["PUT"])
def update_guest(guest_id):
    return _todo("update guest")


@guests_bp.route("/<guest_id>", methods=["DELETE"])
def delete_guest(guest_id):
    return _todo("delete guest")
