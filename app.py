# from cs50 import SQL
import sqlite3
import traceback
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import login_required, build_error_message, handle_ttl
from constants import NOT_FOUND, NOT_FOUND_MESSAGE, BAD_REQUEST, BAD_REQUEST_MESSAGE_KEY_EXISTS, BAD_REQUEST_MESSAGE_INVALID_KEY, SERVER_ERROR, SERVER_ERROR_MESSAGE, SERVICE_UNAVAILABLE, SERVICE_UNAVAILABLE_MESSAGE
import uuid
import datetime, time
import json

app = Flask(__name__)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_FILE_DIR"] = "./session_data"  # Specify directory
app.config["SESSION_FILE_THRESHOLD"] = 50  # Max number of sessions
app.config["SESSION_FILE_MODE"] = 0o600  # File permissions
Session(app)

# Configure CS50 Library to use SQLite database
# db = SQL("sqlite:///mempy.db")
conn = sqlite3.connect("mempy.db")
conn.row_factory = sqlite3.Row  # This enables dictionary-like access
cursor = conn.cursor()

# Global user cache
# Can not be used outside httpcontext
# session['user_cache'] = []#

# Global app api keys
# API_KEY = []

from api import apis
app.register_blueprint(apis)

@app.route("/")
@login_required
def index():
    if 'user_cache' not in session:
        session['user_cache'] = []

    # Load application api-keys
    if 'api_key' not in session:
        session['api_key'] = []
        rows = conn.execute("SELECT api_key FROM users")
        keys = rows.fetchall()
        for key in keys:
            session['api_key'].append(key["api_key"])

    if 'user_cache' not in session:
        session['user_cache'] = []
    
    
    print("USER_CACHE", session['user_cache'])

    # Get user_cache from database
    # rows = conn.execute("SELECT * FROM user_cache WHERE user_id = ? ORDER BY id", (session["user_id"],))
    # user_cache = rows.fetchall()
    # print("user_cache", user_cache)

    # Add cache to USER_CACHE
    # if not USER_CACHE:
        # for cache in user_cache:
            # expires = int(str(time.time()).split(".")[0]) + int(cache["ttl"])
            # print(expires)
            # cache_item = {"id": cache["id"], "cache": cache["cache_name"], "ttl": cache["ttl"], "objects": [], "isEnabled": True, "expiresOn": expires}
            # USER_CACHE.append(cache_item)

    return render_template("index.html", cache=session['user_cache'], len=len)


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
        rows = conn.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = rows.fetchone()
        user_dict = dict(user)
        print(f"User data: {user_dict}")

        # Ensure username exists and password is correct
        if not user_dict or not check_password_hash(
            user_dict["hash"], request.form.get("password")
        ):
            flash('Invalid username and/or password')
            return redirect("/login")

        # Remember which user has logged in
        session["user_id"] = user_dict["id"]
        print(f"user_id value: {session.get("user_id")}")
        print(f"user_id type: {type(session.get("user_id"))}")

        # Add user ApiKey to session
        session["api_key"] = user_dict["api_key"]

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

        check_user = cursor.execute("SELECT username FROM users WHERE username = ?", username)
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
            # cursor = conn.execute("INSERT INTO user_cache (cache_name, ttl, user_id) VALUES (?, ?, ?)", (cache, ttl, session["user_id"]))
            # conn.commit()
            # print(f"Insert successful. Rows affected: {cursor.rowcount}")
            # id = cursor.lastrowid
            # print("id", id)
            expires = int(str(time.time()).split(".")[0]) + int(ttl)
            print(expires)
            # USER_CACHE.append({"id": id, "cache": cache, "ttl": ttl, "objects": [], "isEnabled": True, "expiresOn": expires})
            # USER_CACHE.append({"cache": cache, "ttl": ttl, "objects": [], "isEnabled": True, "expiresOn": expires})
            
            if 'user_cache' not in session:
                session['user_cache'] = []
                
            new_cache = {"cache": cache, "objects": [], "isEnabled": True, "expiresOn": expires}
            # USER_CACHE.append(new_cache)
            session['user_cache'].append(new_cache)
            
            # Mark session as modified
            session.modified = True
            
            print(f"Added cache: {new_cache}")
            print(f"USER_CACHE after append: {session['user_cache']}")
            print(f"USER_CACHE length: {len(session['user_cache'])}")
            return redirect("/")
        # except sqlite3.Error as e:
            # print(f"SQLite error: {e}")
            # print(f"Error type: {type(e).__name__}")
            # conn.rollback()
        except Exception as e:
            print(f"General error: {e}")
            print(f"Full traceback: {traceback.format_exc()}")
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
    
    for index,item in enumerate(USER_CACHE):
        if item["id"] == int(cache_id):
            # Remove cache from database
            cursor.execute("DELETE FROM user_cache WHERE id = ?", cache_id)
            con.commit()
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
    
    for item in session['user_cache']:
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
    for item in session['user_cache']:
        if item["cache"] == cache_name and item["expiresOn"] < int(str(time.time()).split(".")[0]):
            handle_ttl(item)
    
    for item in session['user_cache']:
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

        # Handle ttl logic
        for item in session['user_cache']:
            if item["cache"] == cache and item["expiresOn"] < int(str(time.time()).split(".")[0]):
                handle_ttl(item)

        for item in session['user_cache']:
            if item["cache"] == cache:
                for obj in item["objects"]:
                    print(obj["key"], key)
                    if obj["key"] == key:
                        return build_error_message(400, BAD_REQUEST, BAD_REQUEST_MESSAGE_KEY_EXISTS, "/set-cache")

        for item in session['user_cache']:
            if item["cache"] == cache:
                item["objects"].append({"key": key, "value": json.loads(value)})
        return redirect("/")
    else:
        # Redirect user to login form
        cache_name = request.args.get("cache_name")
        return render_template("set-cache.html", cache=session['user_cache'], len=len, cache_name=cache_name)


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
        if not session['user_cache']:
            flash('No cache found')
            return redirect("/")

        # Handle ttl logic
        for item in session['user_cache']:
            if item["cache"] == cache and item["expiresOn"] < int(str(time.time()).split(".")[0]):
                handle_ttl(item)
                return json.dumps(build_error_message(404, NOT_FOUND, NOT_FOUND_MESSAGE, "/get-cache"))

        # Add to helper as get_cache
        try:
            for item in session['user_cache']:
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
        return render_template("get-cache.html", cache=session['user_cache'], len=len)


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

        # Add to helper as get_cache
        try:
            for item in session['user_cache']:
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
        return render_template("cache-invalidation.html", cache=session['user_cache'], len=len)


@app.route("/app-settings", methods=["GET", "POST"])
@login_required
def app_settings():
    """Create a new user cache"""

    user_id = int(session.get("user_id"))
    print(f"user_id value: {user_id}")
    print(f"user_id type: {type(user_id)}")
    
    if request.method == "POST":
        try:
            id = conn.execute("UPDATE users SET api_key = ? WHERE id = ?", (str(uuid.uuid4()), user_id))
            print("userId from setting", id)
            return redirect("/app-settings")
        except (ValueError, TypeError) as e:
            return build_error_message(400, BAD_REQUEST, e, "/app-settings")
    else:
        # Redirect user to login form
        try:
            rows = conn.execute("SELECT * FROM users WHERE username = ?", (user_id,))
            user = rows.fetchone()
            user_dict = dict(user)
            print(f"User dict: {user_dict}")
            return render_template("app-settings.html", api_key=user_dict["api_key"], user_id=user_dict["ser_id"], username=user_dict["username"])
        except sqlite3.Error as e:
            print(f"SQLite error: {e}")
            print(f"Error type: {type(e).__name__}")
        except Exception as e:
            print(f"General error: {e}")
            print(f"Full traceback: {traceback.format_exc()}")


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

        for item in session['user_cache']:
            if item["cache"] == cache:
                if item["isEnabled"] == False:
                    item["isEnabled"] = True
                else:
                    item["isEnabled"] = False
        return redirect("/")
    else:
        return render_template("toggle-cache.html")
