"""Shared Flask extension instances.

Kept in a dedicated module to avoid circular imports: models and the app
factory both import `db` from here.
"""
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow

db = SQLAlchemy()
ma = Marshmallow()
