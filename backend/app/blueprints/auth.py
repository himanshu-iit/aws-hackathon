"""Authentication endpoints (Phase 4 implements the logic).

Phase 2 defines the routes and wiring. Handlers return 501 Not Implemented
until Phase 4, except where noted.
"""
from flask import Blueprint, jsonify

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


def _todo(name: str):
    return jsonify({"success": False, "error": {"code": "NOT_IMPLEMENTED", "message": f"{name} is implemented in Phase 4"}}), 501


@auth_bp.route("/otp-request", methods=["POST"])
def otp_request():
    return _todo("otp-request")


@auth_bp.route("/otp-verify", methods=["POST"])
def otp_verify():
    return _todo("otp-verify")


@auth_bp.route("/master-setup", methods=["POST"])
def master_setup():
    return _todo("master-setup")


@auth_bp.route("/login", methods=["POST"])
def login():
    return _todo("login")


@auth_bp.route("/logout", methods=["POST"])
def logout():
    return _todo("logout")


@auth_bp.route("/validate", methods=["GET"])
def validate():
    return _todo("validate")
