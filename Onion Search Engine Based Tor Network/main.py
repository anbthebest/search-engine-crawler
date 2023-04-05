import os
import sqlite3
import uuid
import hashlib
import re
import urllib.parse
import requests
import socks
import math
import socket
import stem.connection
import stem.descriptor.remote
import geoip2.database
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache
from werkzeug.middleware.proxy_fix import ProxyFix
from bs4 import BeautifulSoup
import urllib.parse
from urllib.parse import urlparse

app = Flask(__name__)


app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'secret-key-for-demostration')
app.config['SESSION_COOKIE_SECURE'] = True
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

limiter = Limiter(key_func=get_remote_address)
cache = Cache(app, config={'CACHE_TYPE': 'simple'})

# Set up the SOCKS proxy for connecting to the TOR network
socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5, "127.0.0.1", 9150, True)
socket.socket = socks.socksocket

# Check if the connection to the TOR network is successful
response = requests.get('http://check.torproject.org')
if "Congratulations. This browser is configured to use Tor." in response.text:
    print("Successfully connected to the TOR network")
else:
    print("Failed to connect to connect to the TOR network")

# Connect to the SQLite database and create the results table if it doesn't exist
def connect_db():
    conn = sqlite3.connect("results.db")
    conn.execute("""CREATE TABLE IF NOT EXISTS results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    uuid TEXT NOT NULL,
                    link TEXT NOT NULL,
                    text TEXT NOT NULL
                    )""")
    return conn

def connect_db2():
    conn2 = sqlite3.connect('tor_seach_engine.db')
    cursor2 = conn2.cursor()
    #ursor.execute("USE mydatabase")  # select the database
    return conn2


def retrieve_data():
    nodes = []
    consensus = stem.descriptor.remote.get_consensus()
    for router in consensus:
        node_name = router.nickname
        node_type = router.flags[0] if len(router.flags) > 0 else None
        country_code = router.country if hasattr(router, 'country') else ''
        IP_address = router.address
        bandwidth = router.bandwidth
        last_updated = router.published
        nodes.append((node_name, node_type, country_code, IP_address, bandwidth, last_updated, 0))

    # check if there are new nodes to be added
    conn = connect_db()
    cursor = conn.cursor()
    total_rows = count_total_rows_in_table(conn, "nodes")
    if len(nodes) > total_rows:
        new_nodes = nodes[total_rows:]
        cursor.executemany("INSERT INTO nodes (node_name, node_type, country_code, IP_address, bandwidth, last_updated, uptime) VALUES (?, ?, ?, ?, ?, ?, ?)", new_nodes)
        conn.commit()
    
    return nodes


# Function to populate the database with the nodes data
def populate_database():
    # Retrieve the existing nodes from the database
    conn2 = connect_db2()
    cursor2 = conn2.cursor()
    cursor2.execute("SELECT node_name FROM nodes")
    existing_nodes = [row[0] for row in cursor2.fetchall()]

    # Retrieve the latest nodes from the Tor network
    nodes = retrieve_data()

    # Filter out the existing nodes
    new_nodes = [node for node in nodes if node[0] not in existing_nodes]

    # Insert the new nodes into the database
    cursor2.executemany(
        "INSERT INTO nodes (node_name, node_type, country_code, IP_address, bandwidth, last_updated, uptime) VALUES (?, ?, ?, ?, ?, ?, ?)",
        new_nodes
    )
    conn2.commit()


def count_total_rows_in_table(conn, table_name):
    cursor = conn.cursor()
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    row_count = cursor.fetchone()[0]
    return row_count



@app.route("/", methods=["GET", "POST"])
def index():
    conn2 = connect_db2()
    cursor2 = conn2.cursor()
    cursor2.execute("SELECT * FROM nodes")
    if cursor2.fetchone() is None:
        retrieve_data()
    if request.method == "POST":
        keyword = request.form.get("keyword", "")
        if not keyword.strip() or re.search('[^a-zA-Z0-9\s]', keyword):
            flash('Invalid input')
            return redirect(request.url)
        return redirect(url_for('search', keyword=keyword))
    else:
        keyword = request.args.get("keyword", default="")
    return render_template("index.html", keyword=keyword)

@app.route("/contact/", methods=["GET", "POST"])
def  contact():
    email = ""
    pgp = true
    
    
    return render_template('/contact.html')

@app.route("/search/", methods=["GET", "POST"])
@limiter.limit("20/minute")
def search():
    conn = connect_db()
    total_rows = count_total_rows_in_table(conn, "results")
    if request.method == "POST":
        keyword = request.form.get("keyword", "")
        if keyword.strip() and not re.search('[^a-zA-Z0-9\s]', keyword):
            return redirect(url_for('search', keyword=keyword))
        else:
            flash("Invalid input: please enter only alphanumeric characters and spaces.")
    else:
        keyword = request.args.get("keyword", default="")
    page = request.args.get("page", default=1, type=int)
    per_page = request.args.get("per_page", default=15, type=int)

    # Connect to the database and check if the results for this keyword already exist
    uid = hashlib.sha256(keyword.encode()).hexdigest()
    conn = connect_db()
    cursor = conn.cursor()

    total_results = cursor.execute("SELECT COUNT(*) FROM results WHERE uuid=?", (uid,)).fetchone()[0]
    if total_results == 0:
        # Get results from each search engine and store in the database
        results = []
        urls = ["http://torchdeedp3i2jigzjdmfpn5ttjhthh5wbmda2rr3jvqjg5p77c54dqd.onion/search?query={}".format(keyword),
                "https://duckduckgogg42xjoc72x3sjasowoarfbgcmvfimaftt6twagswzczad.onion/?q={}&hps=1".format(keyword)
                ]
        for url in urls:
            try:
                response = requests.get(url)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, "html.parser")
                    results += [(link.get("href"), link.text) for link in soup.find_all("a") if keyword in link.text or ".onion" in link.get("href")]
            except Exception as e:
                print(f"Exception raised while accessing {url}: {e}")

        cursor.execute("BEGIN")
        cursor.executemany("INSERT OR IGNORE INTO results (uuid, link, text) VALUES (?, ?, ?)", [(uid, result[0], result[1]) for result in results])
        cursor.execute("COMMIT")
        total_results = len(results)

    # Retrieve the results from the database
    results = cursor.execute("SELECT link, text FROM results WHERE uuid=? ORDER BY id LIMIT ? OFFSET ?", (uid, per_page, (page-1)*per_page)).fetchall()
    for i, result in enumerate(results):
        link = result[0]
        if 'redirect_url' in link:
            redirect_url = urlparse(link).query.split('redirect_url=')[1]
            new_result = [redirect_url, result[1]]
            if result in results:
                results[i] = tuple(new_result)
            else:
                results.append(tuple(new_result))

    conn.close()
    return render_template("results3.html", results=results, total_results=total_results, per_page=per_page, page=page, total_rows=total_rows, keyword=keyword)



@app.route("/get_total_rows")
def get_total_rows():
    conn = connect_db()
    total_rows = count_total_rows_in_table(conn, "results")
    conn.close()
    return str(total_rows)




@app.route("/insert", methods=["GET", "POST"])
def insert_link():
    if request.method == "POST":
        # Get the link and text from the form
        link = request.form.get("link")
        text_value = request.form.get("text")
        
        if not link:
            flash("Link cannot be empty.")
            return redirect(url_for("insert_link"))
        
        # Check if the link already exists in the database
        conn = connect_db()
        cursor = conn.cursor()
        existing_link = cursor.execute("SELECT link FROM results WHERE link=?", (link,)).fetchone()
        
        if existing_link:
            # Link already exists, redirect back to the search page with an error message
            flash("Link already exists in the database.")
            return redirect(url_for("search"))
        
        # Generate a unique id for the new result
        uuid_value = str(uuid.uuid4())
        
        # Insert the new result into the database
        cursor.execute("INSERT INTO results (link, text, uuid) VALUES (?, ?, ?)", (link, text_value, uuid_value))
        conn.commit()
        
        # Redirect back to the search page with a success message
        flash("Link inserted into database.")
        return redirect(url_for("search"))
    
    # Render the HTML form for inserting a new link
    return render_template("insert_link.html")



@app.route('/nodes')
def show_nodes():
    # retrieve pagination parameters from the request
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 100, type=int)

    # calculate the limits for the SQL query
    start = (page - 1) * per_page
    end = start + per_page

    # connect to the database
    conn = sqlite3.connect('tor_seach_engine.db')
    c = conn.cursor()

    # select the columns you want to display and limit the results
    c.execute('SELECT node_name, node_type, country_code, ip_address, bandwidth, last_updated, uptime FROM nodes LIMIT ? OFFSET ?', (per_page, start))

    # fetch the selected rows
    nodes = c.fetchall()

    # count the total number of rows
    c.execute('SELECT COUNT(*) FROM nodes')
    total_rows = c.fetchone()[0]

    # close the database connection
    conn.close()

    # calculate pagination metadata
    total_pages = math.ceil(total_rows / per_page)

    # render the nodes in an HTML table using a template, along with pagination links
    return render_template('nodes.html', nodes=nodes, page=page, per_page=per_page, total_pages=total_pages, total_rows=total_rows)



















if __name__ == "__main__":
    app.run(port=80)