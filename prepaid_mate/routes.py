from aiohttp_wsgi import WSGIHandler
from lona.routing import Route

from prepaid_mate.app import app as flask_app

flask_wsgi_handler = WSGIHandler(flask_app)


routes = [
    Route('/api/<path:.*>', flask_wsgi_handler, http_pass_through=True),
]