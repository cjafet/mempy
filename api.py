from cs50 import SQL
from helpers import is_cache_enabled, api_key_required, build_error_message, build_error_message_with_detail, handle_ttl
from constants import NOT_FOUND, NOT_FOUND_MESSAGE, BAD_REQUEST, BAD_REQUEST_MESSAGE_INVALID_KEY, BAD_REQUEST_MESSAGE_KEY_EXISTS, SERVER_ERROR, SERVER_ERROR_MESSAGE
from flask import Flask, request, jsonify
from flask import Blueprint
import time
import json
import threading

from app import USER_CACHE
cache_lock = threading.Lock()

db = SQL("sqlite:///mempy.db")

apis = Blueprint('apis', __name__)


@apis.route("/api/set-cache", methods=["POST"])
# @api_key_required
@is_cache_enabled
def add_cache_api():
    """Add new item to the selected cache object"""
    req = json.loads(request.data)
    print(req)
    print(json.dumps(req))

    cache_name = req["cacheName"]
    cache_key = req["cacheKey"]
    value = req["data"]


    try:

        with cache_lock:
            db.execute('''CREATE TABLE IF NOT EXISTS json_table 
                 (id INTEGER PRIMARY KEY, cache_key TEXT NOT NULL, json_data TEXT, user_cache_id INTEGER NOT NULL, FOREIGN KEY(user_cache_id) REFERENCES user_cache(id))''')

            user_cache_id = db.execute("SELECT id FROM user_cache WHERE cache_name= ?", cache_name)
            print("user_cache_id", user_cache_id)
            if not user_cache_id:
                print("cache name not found. Adding to sql database.")
                user_cache_id = db.execute("INSERT INTO user_cache (cache_name, ttl, user_id) VALUES (?)", (cache_name, 7200, 1,))
                print("user_cache_id", user_cache_id)
                db.execute("INSERT INTO json_table (cache_key, json_data, user_cache_id) VALUES (?)", (cache_key, json.dumps(req), user_cache_id,))
            else:
                db.execute("INSERT INTO json_table (cache_key, json_data, user_cache_id) VALUES (?)", (cache_key, json.dumps(req), user_cache_id[0]['id'],))

            #conn.commit()
            #conn.close()
        
            print(cache_name)
            return req 
    except TypeError as e:
        print("Serialization error:", e)

@apis.route("/api/get-cache", methods=["GET"])
# @api_key_required
@is_cache_enabled
def cache_api():
    """Get cache item from cache key and cache name"""
    
    cache = request.args.get("cache")
    key = request.args.get("key")

    # Handle when user has no cache yet
    # if not USER_CACHE:
    #     return build_error_message(404, NOT_FOUND, NOT_FOUND_MESSAGE, "/api/get-cache")

    with cache_lock:
        user_cache_id = db.execute("SELECT id FROM user_cache WHERE cache_name= ?", cache)
        print("user_cahce_id", user_cache_id)
        data = db.execute("SELECT json_data FROM json_table WHERE cache_key= ? and user_cache_id= ?", key, user_cache_id[0]['id'])
        print("cache get response", data)
        # json_data = data.decode('utf-8')
        # Handle ttl logic
        # for item in USER_CACHE:
        #     print("API", USER_CACHE)
        #     if item["cache"] == cache and item["expiresOn"] < int(str(time.time()).split(".")[0]):
        #         handle_ttl(item)
        #         return build_error_message(404, NOT_FOUND, NOT_FOUND_MESSAGE, "/api/get-cache")
    
        print(data[0].keys())
        return json.loads(data[0]['json_data'])

@apis.route("/api/cache-invalidation", methods=["GET"])
# @api_key_required
@is_cache_enabled
def invalidate_cache_api():
    """API to Invalidate cache key"""
    
    cache = request.args.get("cache")
    key = request.args.get("key")

    # Check if cache key is not empty
    if not key:
        return build_error_message(400, BAD_REQUEST, BAD_REQUEST_MESSAGE_INVALID_KEY, "/api/cache-invalidation")

    with cache_lock:
        # Add to helper as get_cache
        try:
            # db.execute(f"DROP TABLE {cache} WHERE cache_name = ?", (cache,))
            # TO-DO Remove this select extra call
            user_cache_id = db.execute("SELECT id FROM user_cache WHERE cache_name= ?", cache)
            print("user_cahce_id", user_cache_id)
            if not user_cache_id:
                return build_error_message_with_detail(404, NOT_FOUND, NOT_FOUND_MESSAGE, "Cache " + request.args.get("cache") + " not found.", "/api/cache-invalidation")

            db.execute("DELETE FROM json_table WHERE cache_key= ? and user_cache_id= ?", key, user_cache_id[0]['id'])
            # return build_error_message(404, NOT_FOUND, NOT_FOUND_MESSAGE, "/api/cache-invalidation")
            return {"status": 204}

        except (ValueError, TypeError):
            return build_error_message(500, SERVER_ERROR, SERVER_ERROR_MESSAGE, "/api/cache-invalidation")
