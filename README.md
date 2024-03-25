# Mempy InMemory Data Store
#### Video Demo:  [Mempy](https://www.youtube.com/watch?v=Oy6zvRpPX9g)
#### Description:
Mempy is an in-memory data store used by applications that need to offload database access by storing all values in memory for fast access of frequently used data. Mempy can also be used as a NoSql database.

Mempy has out-of-the-box exposed Web APIs so that all you need to do in order to interact with it is sending an HTTP web request to any of its available endpoints. You can find all the related documentation in the below sections of this document.

Mempy InMemory Data Store also comes with a web admin console where you can access all its features and various information about each individual cache object created on the system. You can also quickly interact with the APIs through the web console by simply entering the cache information into the forms. Following is a description of all its features.

# Features

## Web Console

- Dashboard: You can use your browser to access your dashboard in the Mempy Web Console to in any Cache Item (row), add an item to the cache by clicking in the "Add Cache Item" link, remove all information from the cache by clicking in the "Clear Cache" link , delete a cache from the database by clicking in the "Delete Cache" link, view at any time all objects in the cache in json format in the browser just by clicking in the "View Cache" link in any cache item available in your dashboard, which is the Mempy Home page of the logged user. From the dashboard you can also view the configured TTL for each cache object, view the number of objects already added to any cache object that you have created and even toggle cache on and off. When disabling the cache all the requests to the /api endpoints will return a 503 Service Unavailable error code causing any system that is using the cache to have to fetch the data directly from the database instead of consuming the cached value. 

- Cache creation: You can use your browser to create and configure a new cache object in the Mempy Web Console. You can configure the TTL (time to live), for each new cache object created independently.

- Add to Cache: You can use your browser to access the Cache API in the Mempy Web Console to add a new item to your desired cache object by selecting the available caches created for the user and filling with a cache key and a cache value. If the key already exists, the system will return with the error code 400 and the error message: "Key already exists.".

- Retrieve from Cache: You can use your browser to access the Search API in the Mempy Web Console to get information from the cache by selecting the desired cache object you want to retrieve the value from and filling with the key information. 

- Cache Invalidation API: You can use your browser to access the Invalidation API in the Mempy Web Console to invalidate any keys associated with a cache. You just need to select the cache object that you want to remove a key from and fill in the cache key form with the key name you want to remove from it.

- API_KEY: The user can use the web console to view it's current API key and even generate a new one if he believes that his key may have been compromised by going to the App Settings section of the Web Console. In addition to viewing and generating a new API key, the application settings are also your place to check user-related information, such as the name of the user logged into the system.
 

## Rest API

Mempy exposes 3 APIs that the user can access to add an item to the cache, get an item from the cache and invalidate a cache item by it's key. All exposed APIs require that you send a header with your Api-Key algong with the request. You can get your Api-Key by visiting the App Settings menu in the Mempy Web Console. Below are all the endpoints with the following requests.

Endpoint: /api/set-cache<br/>
Available methods: POST<br/>
Header: Api-Key<br/>

Sample request object:<br/>

```
{
    "cacheName": "products",
    "data": {
        "id": "10001",
        "title": "Python for Finance",
        "price": "$89.99"
    }
}
```

Full request example in curl: 

```
curl --location --request POST 'http://127.0.0.1:7777/api/set-cache' \
--header 'Api-Key: ********-****-****-****-************' \
--header 'Content-Type: application/json' \
--data-raw '{
    "cacheName": "products",
    "data": {
        "id": "10001",
        "title": "Python for Finance",
        "price": "$89.99"
    }
}'
```

Endpoint: /api/get-cache<br/>
Available methods: GET<br/>
Query Parameters: cache, key
Header: Api-Key<br/>

Full example of the curl request

```
curl --location --request GET 'http://127.0.0.1:7777/api/get-cache?cache=product&key=10001' \
--header 'Api-Key: ********-****-****-****-************'
```

Response:

```
{
    "id": "10002",
    "price": "$89.99",
    "title": "Python for Finance - 2nd Edition"
}
```

Endpoint: /api/cache-invalidation<br/>
Available methods: GET<br/>
Query Parameters: cache, key<br/>
Header: Api-Key<br/>

Full example of the curl request

```
curl --location --request GET 'http://127.0.0.1:7777/api/cache-invalidation?cache=products&key=10001' \
--header 'Api-Key: ********-****-****-****-************'
```


# Creating the Database

Mempy makes use of sqlite to store the name and configuration of the cache objects created by the user so that it can have the cache object ready to be used on every system startup. As of any cache system, all cache items are deleted on system restart or when TTL expires, but not the cache objects where users can save items to it. Run the following command to create the database:

```
sqlite3 finance.db
```

## Database schemas

```
CREATE TABLE users (
id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, 
username TEXT NOT NULL UNIQUE, 
hash TEXT NOT NULL, 
api_key TEXT NOT NULL);


CREATE UNIQUE INDEX username ON users (username);


CREATE TABLE user_cache (
id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, 
cache_name TEXT NOT NULL UNIQUE, 
ttl INTEGER NOT NULL, 
user_id INTEGER NOT NULL,
FOREIGN KEY(user_id) REFERENCES users(id)
);


CREATE UNIQUE INDEX cache_name ON user_cache (cache_name);
```

# Running Mempy

flask run --port 7000