from flask import Blueprint

# Create Catalog Service Blueprint
catalog_bp = Blueprint('catalog', __name__, url_prefix='/api/catalog')

from .routes import *
