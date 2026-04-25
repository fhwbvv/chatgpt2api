import os
import sys

from a2wsgi import ASGIMiddleware


sys.path.append(os.getcwd())

from main import app as asgi_app


application = ASGIMiddleware(asgi_app)
