from helpers import is_cache_enabled, api_key_required, build_error_message, build_error_message_with_detail, handle_ttl
from constants import NOT_FOUND, NOT_FOUND_MESSAGE, BAD_REQUEST, BAD_REQUEST_MESSAGE_INVALID_KEY, BAD_REQUEST_MESSAGE_KEY_EXISTS, SERVER_ERROR, SERVER_ERROR_MESSAGE
from flask import Flask, request
from flask import Blueprint
import time
import json

from app import USER_CACHE

apis = Blueprint('apis', __name__)


@apis.route("/api/set-cache", methods=["POST"])
@api_key_required
@is_cache_enabled
def add_cache_api():
    """Add new item to the selected cache object"""
    req = json.loads(request.data)
    print(req)

    # Handle ttl logic
    for item in USER_CACHE:
        if item["cache"] == req["cacheName"] and item["expiresOn"] < int(str(time.time()).split(".")[0]):
            handle_ttl(item)

    for item in USER_CACHE:
        if item["cache"] == req["cacheName"]:
            # Check if key already exists
            for obj in item["objects"]:
                if obj["key"] == req["data"]["id"]:
                    return build_error_message(400, BAD_REQUEST, BAD_REQUEST_MESSAGE_KEY_EXISTS, "/api/set-cache")
            item["objects"].append({"key": req["data"]["id"], "value": req["data"]})
            print(item["objects"])
            print(json.dumps(req["data"]))

    print(req["cacheName"])
    return req 

@apis.route("/api/get-cache", methods=["GET"])
@api_key_required
@is_cache_enabled
def cache_api():
    """Get cache item from cache key and cache name"""
    
    cache = request.args.get("cache")
    key = request.args.get("key")

    # Handle when user has no cache yet
    if not USER_CACHE:
        return build_error_message(404, NOT_FOUND, NOT_FOUND_MESSAGE, "/api/get-cache")

    # Handle ttl logic
    for item in USER_CACHE:
        print("API", USER_CACHE)
        if item["cache"] == cache and item["expiresOn"] < int(str(time.time()).split(".")[0]):
            handle_ttl(item)
            return build_error_message(404, NOT_FOUND, NOT_FOUND_MESSAGE, "/api/get-cache")

    try:
        print(USER_CACHE)
        for item in USER_CACHE:
            if item["cache"] == cache:
                if not key:
                    return item["objects"]
                else:
                    for obj in item["objects"]:
                        if obj["key"] == key:
                            print(obj["value"])
                            return obj["value"]
                    # Return error message if no key found
                    return build_error_message(404, NOT_FOUND, NOT_FOUND_MESSAGE, "/api/get-cache")
        return build_error_message_with_detail(404, NOT_FOUND, NOT_FOUND_MESSAGE, "Cache " + cache + " not found.", "/api/get-cache")
    except (ValueError, TypeError):
            return build_error_message(500, SERVER_ERROR, SERVER_ERROR_MESSAGE, "/api/get-cache")


@apis.route("/api/cache-invalidation", methods=["GET"])
@api_key_required
@is_cache_enabled
def invalidate_cache_api():
    """API to Invalidate cache key"""
    cache = request.args.get("cache")

    key = request.args.get("key")
    # Check if cache key is not empty
    if not key:
        return build_error_message(400, BAD_REQUEST, BAD_REQUEST_MESSAGE_INVALID_KEY, "/api/cache-invalidation")

    # Add to helper as get_cache
    try:
        for item in USER_CACHE:
            if item["cache"] == cache and item["objects"]:
                for index,obj in enumerate(item["objects"]):
                    if obj["key"] == key:
                        print(obj["key"])
                        item["objects"].pop(index)
                        return {"status": 204}
                return build_error_message(404, NOT_FOUND, NOT_FOUND_MESSAGE, "/api/cache-invalidation")
        return build_error_message_with_detail(404, NOT_FOUND, NOT_FOUND_MESSAGE, "Cache " + request.args.get("cache") + " not found.", "/api/cache-invalidation")
    except (ValueError, TypeError):
        return build_error_message(500, SERVER_ERROR, SERVER_ERROR_MESSAGE, "/api/cache-invalidation")