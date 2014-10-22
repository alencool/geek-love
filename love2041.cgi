#!/usr/bin/python
from wsgiref.handlers import CGIHandler
from love2041 import app

CGIHandler().run(app)