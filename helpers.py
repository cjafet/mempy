import csv
import datetime
import pytz
import requests
import urllib
import uuid

from flask import redirect, render_template, session, request
from functools import wraps
from constants import SERVICE_UNAVAILABLE, SERVICE_UNAVAILABLE_MESSAGE, BAD_REQUEST, UNAUTHORIZED
import json
import time


def is_cache_enabled(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/latest/patterns/viewdecorators/
    """
    from app import USER_CACHE
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method == "POST":
            req = json.loads(request.data)
            if "cacheName" in req and req["cacheName"] != "":
                print(req["cacheName"])
                for item in USER_CACHE:
                    if item["cache"] == req["cacheName"]:
                        if item["isEnabled"] == False:
                            return build_error_message(503, SERVICE_UNAVAILABLE, SERVICE_UNAVAILABLE_MESSAGE, "/api/set-cache")
            else:
                return build_error_message(400, BAD_REQUEST, "Missing cache name.", "/api/set-cache")
        else:
            cache = request.args.get("cache")
            # Check if cache name is not empty
            if not cache:
                return build_error_message(400, BAD_REQUEST, "Missing cache param.", "/api/*")
            else:
                for item in USER_CACHE:
                    if item["cache"] == cache:
                        if item["isEnabled"] == False:
                            return build_error_message(503, SERVICE_UNAVAILABLE, SERVICE_UNAVAILABLE_MESSAGE, "/api/*")
        return f(*args, **kwargs)

    return decorated_function


def api_key_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/latest/patterns/viewdecorators/
    """
    from app import API_KEY
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('Api-Key')
        if not api_key:
            return {
                "timestamp": str(datetime.datetime.now()),
                "status": 400,
                "error": BAD_REQUEST,
                "message": "Missing Api-Key header.",
                "path": "/api/cache-invalidation"}
        if api_key not in API_KEY:
            return {
                "timestamp": str(datetime.datetime.now()),
                "status": 401,
                "error": UNAUTHORIZED,
                "message": "Invalid credentials.",
                "path": "/api/cache-invalidation"}
        return f(*args, **kwargs)

    return decorated_function


def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/latest/patterns/viewdecorators/
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)

    return decorated_function


def build_error_message(status, error, message, path):
    return {
            "timestamp": str(datetime.datetime.now()),
            "status": status,
            "error": error,
            "message": str(message),
            "path": path}

def build_error_message_with_detail(status, error, message, detail, path):
    return {
            "timestamp": str(datetime.datetime.now()),
            "status": status,
            "error": error,
            "message": str(message),
            "detail": detail,
            "path": path}

def handle_ttl(item):    
    try:
        print(f"Cache {item["cache"]} expired")
        # Calculate new ttl
        expires = int(str(time.time()).split(".")[0]) + int(item["ttl"])
        # Assign new ttl to expiresOn
        item["expiresOn"] = expires
        # Invalidate cache
        item["objects"] = []
    except (ValueError, TypeError) as e:
        return build_error_message(500, "500 Internal Server Error", e, "/view-cache")
