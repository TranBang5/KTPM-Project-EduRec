from flask import Blueprint

# Create Profile Service Blueprint
profile_bp = Blueprint('profile', __name__, url_prefix='/api/profile')

from .routes import *