from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import login_required, build_error_message, handle_ttl
from constants import NOT_FOUND, NOT_FOUND_MESSAGE, BAD_REQUEST, BAD_REQUEST_MESSAGE_KEY_EXISTS, BAD_REQUEST_MESSAGE_INVALID_KEY, SERVER_ERROR, SERVER_ERROR_MESSAGE, SERVICE_UNAVAILABLE, SERVICE_UNAVAILABLE_MESSAGE
import uuid
import datetime, time
import json
import threading

app = Flask(__name__)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///mempy.db")

# Global user cache
USER_CACHE = []
cache_lock = threading.Lock()

# Global app api keys
API_KEY = []

from api import apis
app.register_blueprint(apis)

@app.route("/")
@login_required
def index():
    # Load application api-keys
    if not API_KEY:
        keys = db.execute("SELECT api_key FROM users")
        for key in keys:
            API_KEY.append(key["api_key"])
    print(USER_CACHE)

    # Get user_cache from database
    user_cache = db.execute("SELECT * FROM user_cache WHERE user_id = ? ORDER BY id", session["user_id"])
    print("user_cache", user_cache)

    # Add cache to USER_CACHE
    if not USER_CACHE:
        for item in user_cache:
            expires = int(str(time.time()).split(".")[0]) + int(item["ttl"])
            print(expires)
            cache_item = {"id": item["id"], "cache": item["cache_name"], "ttl": item["ttl"], "objects": [], "isEnabled": True, "expiresOn": expires}
            USER_CACHE.append(cache_item)

    return render_template("index.html", cache=USER_CACHE, len=len)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        username = request.form.get("username")
        # Check if username is not empty
        if not username:
            flash('Enter a valid username')
            return redirect("/login")

        # Ensure password was submitted
        password = request.form.get("password")
        # Check if username is not empty
        if not password:
            flash('Enter your password')
            return redirect("/login")

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            flash('Invalid username and/or password')
            return redirect("/login")

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Add user ApiKey to session
        session["api_key"] = rows[0]["api_key"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":

        username = request.form.get("username")
        # Check if username is not empty
        if not username:
            flash('Enter a valid username')
            return redirect("/register")

        check_user = db.execute("SELECT username FROM users WHERE username = ?", username)
        if check_user:
            if check_user[0]["username"] == username:
                flash('Username already exists!')
                return redirect("/register")

        password = request.form.get("password")
        # Check if username is not empty
        if not password:
            flash('Password can not be blank!')
            return redirect("/register")

        confirmation = request.form.get("confirmation")
        # Check if password matches
        if confirmation != password:
            flash('Password do not match!')
            return redirect("/register")

        hash = generate_password_hash(password)
        db.execute("INSERT INTO users (username, hash, api_key) VALUES (?, ?, ?)", username, hash, str(uuid.uuid4()))
        return redirect("/login")
    else:
        return render_template("register.html")


@app.route("/logout")
@login_required
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/create-cache", methods=["GET", "POST"])
@login_required
def cache():
    """Create a new user cache"""

    if request.method == "POST":
        cache = request.form.get("cache")
        # Check if cache name is not empty
        if not cache:
            flash('Enter a valid cache name.')
            return redirect("/create-cache")

        # Add try 

        ttl = request.form.get("ttl")
        # Check if ttl is positive and not empty
        if not ttl or int(ttl) <= 0:
            flash('TTL must be a positive value.')
            return redirect("/create-cache")
        try:
            with cache_lock:
                id = db.execute("INSERT INTO user_cache (cache_name, ttl, user_id) VALUES (?, ?, ?)", cache, ttl, session["user_id"])
                expires = int(str(time.time()).split(".")[0]) + int(ttl)
                print(expires)
                USER_CACHE.append({"id": id, "cache": cache, "ttl": ttl, "objects": [], "isEnabled": True, "expiresOn": expires})
                return redirect("/")
        except (ValueError, TypeError) as e:
            return build_error_message(400, BAD_REQUEST, e, "/create-cache")
    else:
        # Redirect user to login form
        return render_template("cache.html")


@app.route("/remove-cache", methods=["POST"])
@login_required
def remove_cache():
    """Remove user cache from database"""

    cache_id = request.form.get("cache_id")
    # Check if cache id is not empty
    if not cache_id:
        flash('Enter a valid cache id.')
        return redirect("/")
    
    with cache_lock:
        for index,item in enumerate(USER_CACHE):
            if item["id"] == int(cache_id):
                # Remove cache from database
                db.execute("DELETE FROM user_cache WHERE id = ?", cache_id)
                # Remove cache from USER_CACHE
                USER_CACHE.pop(index)
    
        flash('Cache successfully removed from database!')
    
        return redirect("/")

@app.route("/clear-cache", methods=["POST"])
@login_required
def clear_cache():
    """Clear cache name"""

    cache_name = request.form.get("cache_name")
    # Check if cache name is not empty
    if not cache_name:
        flash('Enter a valid cache name')
        return redirect("/")
    
    with cache_lock:
        for item in USER_CACHE:
            if item["cache"] == cache_name:
                # Clear cache from USER_CACHE
                item["objects"] = []
    
        flash('Cache removed successfully!')
    
        return redirect("/")


@app.route("/view-cache", methods=["POST"])
@login_required
def view_cache():
    """Get all cache items"""

    cache_name = request.form.get("cache_name")
    # Check if cache name is not empty
    if not cache_name:
        flash('Enter a valid cache name')
        return redirect("/")

    # Handle ttl logic
    for item in USER_CACHE:
        if item["cache"] == cache_name and item["expiresOn"] < int(str(time.time()).split(".")[0]):
            handle_ttl(item)
    
    for item in USER_CACHE:
        if item["cache"] == cache_name:
            # Return selected cache
            return jsonify(item["objects"]) 


@app.route("/set-cache", methods=["GET", "POST"])
@login_required
def add_cache():
    """Add new item to the selected cache object"""

    if request.method == "POST":
        cache = request.form.get("cache")
        # Check if cache name is not empty
        if not cache:
            flash('Select a valid cache name')
            return redirect("/set-cache")

        key = request.form.get("key")
        # Check if key is not empty
        if not key:
            flash('Enter a valid key name')
            return redirect("/set-cache")

        value = request.form.get("value")
        # Check if value is not empty
        if not value:
            flash('Enter a valid value')
            return redirect("/set-cache")

        with cache_lock:

        # Handle ttl logic
            for item in USER_CACHE:
                if item["cache"] == cache and item["expiresOn"] < int(str(time.time()).split(".")[0]):
                    handle_ttl(item)

            for item in USER_CACHE:
                if item["cache"] == cache:
                    for obj in item["objects"]:
                        print(obj["key"], key)
                        if obj["key"] == key:
                            return build_error_message(400, BAD_REQUEST, BAD_REQUEST_MESSAGE_KEY_EXISTS, "/set-cache")

            for item in USER_CACHE:
                if item["cache"] == cache:
                    item["objects"].append({"key": key, "value": json.loads(value)})
            return redirect("/")
    else:
        # Redirect user to login form
        cache_name = request.args.get("cache_name")
        return render_template("set-cache.html", cache=USER_CACHE, len=len, cache_name=cache_name)


@app.route("/get-cache", methods=["GET", "POST"])
@login_required
def search_cache():
    """Search for a key in the cache object"""

    if request.method == "POST":
        cache = request.form.get("cache")
        # Check if cache name is not empty
        if not cache:
            flash('Select a valid cache name')
            return redirect("/get-cache")
        print(cache)

        key = request.form.get("key")
        # Check if key is not empty
        if not key:
            flash('Enter a valid key name')
            return redirect("/get-cache")

        # Handle when user has no cache yet
        if not USER_CACHE:
            flash('No cache found')
            return redirect("/")

        with cache_lock:
            
            # Handle ttl logic
            for item in USER_CACHE:
                if item["cache"] == cache and item["expiresOn"] < int(str(time.time()).split(".")[0]):
                    handle_ttl(item)
                    return json.dumps(build_error_message(404, NOT_FOUND, NOT_FOUND_MESSAGE, "/get-cache"))

            # Add to helper as get_cache
            try:
                for item in USER_CACHE:
                    print("entering looping")
                    print(item["cache"] == cache)
                    if item["cache"] == cache and item["objects"]:
                        print("entering if")
                        for obj in item["objects"]:
                            print(obj["key"], key)
                            if obj["key"] == key:
                                return obj["value"]
                        # Return the error message if no key found
                        return json.dumps(build_error_message(404, NOT_FOUND, NOT_FOUND_MESSAGE, "/get-cache"))
            except (ValueError, TypeError):
                return json.dumps(build_error_message(500, SERVER_ERROR, SERVER_ERROR_MESSAGE, "/get-cache"))
    else:
        # Redirect user to login form
        return render_template("get-cache.html", cache=USER_CACHE, len=len)


@app.route("/cache-invalidation", methods=["GET", "POST"])
@login_required
def invalidate_cache():
    """Invalidate cache key"""
    if request.method == "POST":
        cache = request.form.get("cache")
        # Check if cache name is not empty
        if not cache:
            flash('Select a valid cache name')
            return redirect("/cache-invalidation")
        print(cache)

        key = request.form.get("key")
        # Check if key is not empty
        if not key:
            flash('Enter a valid key name')
            return redirect("/cache-invalidation")

        with cache_lock:
            # Add to helper as get_cache
            try:
                for item in USER_CACHE:
                    if item["cache"] == cache and item["objects"]:
                        for index,obj in enumerate(item["objects"]):
                            if obj["key"] == key:
                                print(obj["key"])
                                item["objects"].pop(index)
                                return json.dumps({"status": 204})
                        # Return the error message if no key found
                        return json.dumps(build_error_message(404, NOT_FOUND, NOT_FOUND_MESSAGE, "/cache-invalidation"))
            except (ValueError, TypeError):
                return json.dumps(build_error_message(500, SERVER_ERROR, SERVER_ERROR_MESSAGE, "/cache-invalidation"))
    else:
        # Redirect user to login form
        return render_template("cache-invalidation.html", cache=USER_CACHE, len=len)


@app.route("/app-settings", methods=["GET", "POST"])
@login_required
def app_settings():
    """Create a new user cache"""

    if request.method == "POST":
        try:
            id = db.execute("UPDATE users SET api_key = ? WHERE id = ?", str(uuid.uuid4()), session["user_id"])
            return redirect("/app-settings")
        except (ValueError, TypeError) as e:
            return build_error_message(400, BAD_REQUEST, e, "/app-settings")
    else:
        # Redirect user to login form
        result = db.execute("SELECT api_key,username FROM users WHERE id= ?", session["user_id"])
        return render_template("app-settings.html", api_key=result[0]["api_key"], user_id=session["user_id"], username=result[0]["username"])


@app.route("/toggle-cache", methods=["POST", "GET"])
def toggle_cache():
    """Toggle cache object on/off"""
    if request.method == "POST":
        cache = request.form.get("cache")
        # Check if cache name is not empty
        if not cache:
            flash('Select a valid cache')
            return redirect("/")
        print(cache)

        for item in USER_CACHE:
            if item["cache"] == cache:
                if item["isEnabled"] == False:
                    item["isEnabled"] = True
                else:
                    item["isEnabled"] = False
        return redirect("/")
    else:
        return render_template("toggle-cache.html")
