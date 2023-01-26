from aiohttp_wsgi import WSGIHandler
from lona.routing import Route

from prepaid_mate._django.wsgi import application as django_application
from prepaid_mate.app import app as flask_app

flask_wsgi_handler = WSGIHandler(flask_app)
django_wsgi_handler = WSGIHandler(django_application)


routes = [
    Route('/api/<path:.*>', flask_wsgi_handler, http_pass_through=True),
    Route('/admin/<path:.*>', django_wsgi_handler, http_pass_through=True),
]