import sqlite3
import os
from flask import Flask, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from helper_methods import get_items, get_image_url, clear_search, get_artwork_for_search, get_db_connection
from dotenv import load_dotenv

load_dotenv()
db_path = os.getenv('DB_PATH')

# I built this application on the heels of completing the HarvardX CS50x's Finance Problem Set.
# I followed the prececent there for registration and login. That is where I learned to use flask_session, werkzeug.security's check_password_hash, etc.
# In general, the use of flask, jinja, etc. is influenced by that problem set, and I followed the format for rendering templates, etc. from that lab.


# set up the code to reference and interact with the session and database
app = Flask(__name__)

# This is the schema for the database
# CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, username TEXT NOT NULL, hash TEXT NOT NULL);
# CREATE TABLE sqlite_sequence(name,seq);
# CREATE TABLE searches (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, user_id INTEGER, name TEXT UNIQUE NOT NULL, page_limit INTEGER);
# CREATE TABLE artwork_searches (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, artwork_id INTEGER, search_id INTEGER, current_page INTEGER);
# CREATE TABLE collected_works (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, user_id INTEGER, artwork_id INTEGER, collection_id INTEGER);
# CREATE TABLE collections (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, user_id INTEGER NOT NULL, title NOT NULL);
# CREATE TABLE artworks (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, title TEXT, alt_text TEXT, artwork_id INTEGER NOT NULL, art_institute_url TEXT, display_url TEXT, artist_info TEXT, date_info TEXT);

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# the registration route, where users sign up for an account and are automatically logged in upon succesful creation of one
@app.route("/register", methods=["GET", "POST"])
def register():
    session.clear()

    if request.method == "GET":
        # display the registration form
        return render_template("register.html")

    elif request.method == "POST":
        # when the registration form is submitted, check whether the fields are filled out and are acceptable

        # check whether a username and password were submitted and whether the confirmation of the password matches the password
        # render an error message if one of these checks do not pass

        if not request.form.get('username'):
            return render_template("error_message.html", message="No username was entered.")

        elif not request.form.get('password'):
            return render_template("error_message.html", message="No password was entered.")

        elif not request.form.get('confirmation'):
            return render_template("error_message.html", message="You did not confirm the password.")

        elif request.form.get('confirmation') != request.form.get('password'):
            return render_template("error_message.html", message="The confirmation password did not match the password.")

        username = request.form.get("username")
        # for security reasons, hash the password so we are not storing a string literal in the database
        hash = generate_password_hash(request.form.get("password"))

        # check whether the user is already in the database
        # if the user is not in the database, go ahead and create the user
        conn = get_db_connection()
        user_rows = conn.execute("SELECT * FROM users WHERE username = ?", [username]).fetchall()
        if not len(user_rows):
            conn.execute(
                "INSERT INTO users (username, hash) VALUES(?, ?)", [username, hash]
            ).fetchall()
            conn.commit()
            conn.close()

            # automatically log the user in if all is successful
            conn = get_db_connection()
            user_rows = conn.execute("SELECT * FROM users WHERE username = ?", [username]).fetchall()
            conn.commit()
            conn.close()
            session["user_id"] = user_rows[0]["id"]
            return redirect("/")

        # if the user already exists, display an error message
        return render_template("error_message.html", message="Registration Unsuccessful.")


@app.route("/login", methods=["GET", "POST"])
def login():
    # clear any session that is open and render the form to log in
    session.clear()

    if request.method == "GET":
        return render_template("login.html")

    # check whether the user has submitted a username and password
    # if they have not, throw an error message
    if not request.form.get('username'):
        return render_template("error_message.html", message="No username was entered.")

    if not request.form.get('password'):
        return render_template("error_message.html", message="No password was entered.")

    # if a username and password were submitted, check that they are correct
    # if they are not, then display an error message

    conn = get_db_connection()

    user_rows = conn.execute(
        'SELECT * FROM users WHERE username = ?', [request.form.get("username")]
    ).fetchall()

    conn.commit()
    conn.close()

    if len(user_rows) != 1 or not check_password_hash(
        user_rows[0]["hash"], request.form.get("password")
    ):
        return render_template("error_message.html", message="invalid username and/or password")

    # if the username and password are correct, store the user id in the session to give the user access and redirect to the home page
    session["user_id"] = user_rows[0]["id"]

    # go to the home page
    return redirect("/")


@app.route("/logout")
def logout():
    # clear any open searches, clear the session, and redirect to the home page, which should take the user to the login page
    clear_search()
    session.clear()
    return redirect("/")


@app.route("/", methods=["GET", "POST"])
def index():
    if not session or not session["user_id"]:
        return redirect("/login")

    # clear the search when a user navigates away from the search results
    clear_search()
    return render_template("index.html")

@app.route("/search", methods=["GET", "POST"])
def search():
    if not session or not session["user_id"]:
        return redirect("/")

    if request.method == "GET":
        # clear the last search when a user has navigated away from the search results and is starting a new search, and display the search input form
        clear_search()
        return render_template("search.html")

    elif request.method == "POST":
        # when the user has submitted a search term, make the fetch to get the first set of matches from the Art Institute of Chicago API
        if request.form.get('search'):
            search_term = request.form.get('search')
            page_number = 1
            artwork_rows = get_items(search_term, page_number)
            conn = get_db_connection()
   
            search_rows = conn.execute("SELECT * FROM searches WHERE user_id = ?", [session["user_id"]]).fetchall()

            conn.commit()
            conn.close()

            return render_template("search_results.html", items=artwork_rows, page_number=page_number, page_limit=search_rows[0]['page_limit'], search_term=search_term)


@app.route("/search_results", methods=["GET", "POST"])
def search_results():
    if not session or not session["user_id"]:
        return redirect("/")

    if request.method == "POST":
        page_number = request.form.get('page_number')
        # there should always only be one search in the database per user; get the information for this search
        conn = get_db_connection()
        search_rows = conn.execute("SELECT * from searches WHERE user_id = ?", [session["user_id"]]).fetchall()
        conn.commit()
        conn.close()
        page_limit = search_rows[0]['page_limit']
        search_term = search_rows[0]['name']

        # reset the page number that the user is requesting based on which arrow was pressed in the search results in order to navigate forwards or backwards
        if request.form.get('page_number_plus'):
            if int(request.form.get('page_number_plus')) < page_limit:
                # request the next page number (either from the API or from the database if it has already been fetched) if the forward arrow was pressed and the user is not already on the last page
                page_number = int(request.form.get('page_number_plus')) + 1
            else:
                # stay on the same page if the user is on the last page
                artwork_rows = get_artwork_for_search(page_number)
                return render_template("search_results.html", items=artwork_rows, page_number=page_number, page_limit=page_limit, search_term=search_term)

        elif request.form.get('page_number_minus'):
            if int(request.form.get('page_number_minus')) > 1:
                # request the prior page number (either from the API or from the database if it has already been fetched) when the user presses the back arrow and is not on the first results page
                page_number = int(request.form.get('page_number_minus')) - 1
            else:
                # stay on the same page if the user is on the first results page
                artwork_rows = get_artwork_for_search(page_number)
                return render_template("search_results.html", items=artwork_rows, page_number=page_number, page_limit=page_limit, search_term=search_term)

        elif request.form.get('page_number_end'):
                if int(request.form.get('page_number')) < page_limit:
                    # request the very last page of results (either from the API or from the database if it has already been fetched) when the user presses the double forward arrow if the user is not already on the last page
                    page_number=int(request.form.get('page_number_end'))
                else:
                    artwork_rows = get_artwork_for_search(page_number)
                    return render_template("search_results.html", items=artwork_rows, page_number=page_number, page_limit=page_limit, search_term=search_term)

        elif request.form.get('page_number_beginning'):
                # get the first page of results from the database when the user presses the double backwards arrow if the user is not already on the first page
                if int(request.form.get('page_number')) > 1:
                    page_number = 1
                else:
                    artwork_rows = get_artwork_for_search(page_number)
                    return render_template("search_results.html", items=artwork_rows, page_number=page_number, page_limit=page_limit, search_term=search_term)

        artwork_rows = get_items(search_term, page_number)
        return render_template("search_results.html", items=artwork_rows, page_number=page_number, page_limit=page_limit, search_term=search_term)


@app.route("/artwork_showpage", methods=["GET", "POST"])
def artwork_showpage():
    if not session or not session["user_id"]:
        return redirect("/")

    if request.method == 'POST':
        # if the user clicked on the button to add an artwork to a collection
        if request.form.get('add_to_collection'):
            artwork_id = request.form.get('add_to_collection')
            search_term = request.form.get('search_term')
            page_number = request.form.get('page_number')
            collection_select_id = request.form.get('collection-select')

            conn = get_db_connection()
            search_rows = conn.execute("SELECT * FROM searches WHERE name = ? AND user_id = ?", [search_term, session["user_id"]]).fetchall()
            conn.commit()
            conn.close()
            search_id = search_rows[0]['id']
            page_limit = search_rows[0]['page_limit']

            conn = get_db_connection()
            artwork_rows = conn.execute("SELECT * FROM artworks JOIN artwork_searches on artwork_searches.artwork_id = artworks.artwork_id WHERE artwork_searches.search_id = ? AND artwork_searches.current_page = ?", [search_id, page_number]).fetchall()
            conn.commit()
            conn.close()
        
            conn = get_db_connection()
            collection_rows = conn.execute("SELECT * FROM collections WHERE id = ? OR title = ? AND user_id = ?", [collection_select_id, search_term, session["user_id"]]).fetchall()
            conn.commit()
            conn.close()
        
            if len(collection_rows):
                # if the collection the user is trying to add the artwork to already exists, add the work to that collection if it is not already in it
                collection_id = collection_rows[0]['id']
                conn = get_db_connection()           
                collected_works_rows = conn.execute("SELECT * FROM collected_works WHERE user_id = ? AND artwork_id = ? AND collection_id = ?", [session["user_id"], artwork_id, collection_id]).fetchall()
                conn.commit()
                conn.close()
        
                if not collected_works_rows:
                    conn = get_db_connection() 
                    conn.execute("INSERT INTO collected_works (collection_id, user_id, artwork_id) VALUES(?, ?, ?)", [collection_id, session["user_id"], artwork_id]).fetchall()
                    conn.commit()
                    conn.close()
                return render_template("search_results.html", items=artwork_rows, page_number=page_number, page_limit=page_limit, search_term=search_term)

            else:
                # if a collection needs to be created from the current search term, first create the collection, then add the artwork to the new collection
                conn = get_db_connection()
                conn.execute("INSERT INTO collections (title, user_id) VALUES(?, ?)", [search_term, session["user_id"]]).fetchall()
                conn.commit()
                conn.close()

                conn = get_db_connection()
                collection_rows = conn.execute("SELECT * FROM collections WHERE title = ? AND user_id = ?", [search_term, session["user_id"]]).fetchall()
                conn.commit()
                conn.close()
                collection_id = collection_rows[0]['id']
                
                conn = get_db_connection()
                collected_works_rows = conn.execute("SELECT * FROM collected_works WHERE user_id = ? AND artwork_id = ?", [session["user_id"], artwork_id]).fetchall()
                conn.execute("INSERT INTO collected_works (collection_id, user_id, artwork_id) VALUES(?, ?, ?)", [collection_id, session["user_id"], artwork_id]).fetchall()
                conn.commit()
                conn.close()
                return render_template("search_results.html", items=artwork_rows, page_number=page_number, page_limit=page_limit, search_term=search_term)

        if request.form.get('artwork_id'):
            # if the user clicked on the search term to expand the artwork, display the showpage for that artwork
            artwork_id = request.form.get('artwork_id')

            # at this point, get the image url and other details for the artwork to display on the showpage
            # it requires a separate fetch to the API, so I am only making this fetch if the user would like to see the showpage or stores an artwork in a collection
            get_image_url(artwork_id)

            conn = get_db_connection()
            artwork_rows = conn.execute("SELECT * FROM artworks WHERE artwork_id = ?", [artwork_id]).fetchall()
            conn.commit()
            conn.close()
            title = artwork_rows[0]['title']
            image_url = artwork_rows[0]['art_institute_url']
            full_url = artwork_rows[0]['display_url']
            artist_info = artwork_rows[0]['artist_info']
            date_info = artwork_rows[0]['date_info']
            alt_text = artwork_rows[0]['alt_text']

            # Pass along information about the current search to keep the user oriented and to help with navigation between pages
            search_term = request.form.get('search_term')
            conn = get_db_connection()
            current_search = conn.execute("SELECT * FROM searches WHERE user_id = ?", [session["user_id"]]).fetchall()
            conn.commit()
            conn.close()
            search_id = current_search[0]["id"]
            page_number = request.form.get('page_number')

            # pass along information about the user's collections in case they want to add the artwork to a collection when the showpage renders
            conn = get_db_connection()
            all_collections = conn.execute("SELECT * FROM collections WHERE user_id = ?", [session["user_id"]]).fetchall()
            conn.commit()
            conn.close()

            return render_template("artwork_showpage.html", artwork_id=artwork_id, url=full_url, alt_text=alt_text,
                                   artist_info=artist_info, date_info=date_info, search_term=search_term, page_number=page_number,
                                   title=title, image_url=image_url, collections=all_collections, search_id = search_id)


@app.route("/collections", methods=["GET", "POST"])
def collections():
    if not session or not session["user_id"]:
        return redirect("/")

    if request.method == "GET":
        # if a user goes to the collections tab, clear the most recent search and get the user's collections from the database to display
        clear_search()
        conn = get_db_connection()
        collections = conn.execute("SELECT * FROM collections WHERE user_id = ?", [session["user_id"]]).fetchall()
        conn.commit()
        conn.close()
        return render_template("collections.html", collections=collections)

    if request.method == "POST":
        if request.form.get('create-new-collection'):
            # check whether the user already has a collection with the title that was submitted
            new_collection_title = request.form.get('create-new-collection')
            conn = get_db_connection()
            collections = conn.execute("SELECT * FROM collections WHERE user_id = ? AND title = ?", [session["user_id"], new_collection_title]).fetchall()
            conn.commit()
            conn.close()
            if len(collections):
                # render an error message if the user already has a collection with that title
                return render_template("error_message.html", message="That collection title already exists")

            else:
                # if the user does not already have a collection with the title submitted, create that collection
                conn = get_db_connection()
                conn.execute("INSERT into collections (title, user_id) VALUES(?, ?)", [new_collection_title, session["user_id"]]).fetchall()
                conn.commit()
                conn.close()

                conn = get_db_connection()
                collections = conn.execute("SELECT * FROM collections WHERE user_id = ?", [session["user_id"]]).fetchall()
                conn.commit()
                conn.close()
                return render_template("collections.html", collections=collections)

        # if no title was submitted, render an error message
        return render_template("error_message.html", message="You did not enter a collection title.")


@app.route("/delete_collection", methods=["GET", "POST"])
def delete_collection():
    if not session or not session["user_id"]:
        return redirect("/")

    if request.method == "POST":
        if request.form.get('collection-delete-select'):
            # if the user selected a collection to delete, go ahead and delete the user's collection and re-render the page to show it is gone
            collection_delete_id = request.form.get('collection-delete-select')

            conn = get_db_connection()
            conn.execute("DELETE FROM collected_works WHERE collection_id = ?", [collection_delete_id]).fetchall()
            conn.commit()
            conn.close()
            
            conn = get_db_connection()
            conn.execute("DELETE FROM collections WHERE id = ?", [collection_delete_id]).fetchall()
            conn.commit()
            conn.close()

            conn = get_db_connection()
            conn.execute("DELETE FROM artworks WHERE artwork_id NOT IN (SELECT artwork_id FROM artwork_searches) AND artwork_id NOT IN (SELECT artwork_id FROM collected_works)").fetchall()
            conn.commit()
            conn.close()

            conn = get_db_connection()
            collections = conn.execute("SELECT * FROM collections WHERE user_id = ?", [session["user_id"]]).fetchall()
            conn.commit()
            conn.close()
            return render_template("collections.html", collections=collections)

        # if the user did not select a collection, render an error message
        return render_template("error_message.html", message="You did not select a collection to delete")


@app.route("/collection_showpage", methods=["GET", "POST"])
def collection_showpage():
    if not session or not session["user_id"]:
        return redirect("/")
    if request.method == "POST":
        if request.form.get('collection_id'):
            # render the display page for the collection of artwork that the user requested
            collection_id = request.form.get('collection_id')
            conn = get_db_connection()
            collection_title = conn.execute("SELECT title FROM collections WHERE id = ?", [collection_id]).fetchall()[0]['title']
            conn.commit()
            conn.close()

            conn = get_db_connection()
            artworks = conn.execute("SELECT * FROM artworks JOIN collected_works on artworks.artwork_id = collected_works.artwork_id WHERE collected_works.user_id = ? AND collected_works.collection_id = ?", [session["user_id"], collection_id]).fetchall()
            conn.commit()
            conn.close()
            return render_template("collection_showpage.html", artworks=artworks, collection_title=collection_title, collection_id=collection_id)

        # if the user did not select a particular collection, render an error message
        return render_template("error_message.html", message="You did not select a particular collection to view")


@app.route("/collection_artwork_showpage", methods=["GET", "POST"])
def collection_artwork_showpage():
    if not session or not session["user_id"]:
        return redirect("/")

    if request.method == "POST":
        collection_id = request.form.get('collection_id')
        artwork_id = request.form.get('artwork_id')

        if not collection_id or not artwork_id :
            # render an error message if there is no collection or artwork id
            return render_template("error_message.html", message="Missing collection and/or artwork id")

        if request.form.get('remove-artwork-from-collection'):
            # if the user clicked on the remove button, remove the collected_work from the user's collection
            # if the artwork is in another of the user's collections, it should still be in that other collection

            conn = get_db_connection()
            conn.execute("DELETE from collected_works WHERE artwork_id = ? AND collection_id = ? AND user_id = ?", [artwork_id, collection_id, session["user_id"]]).fetchall()
            conn.commit()
            conn.close()

            conn = get_db_connection()
            conn.execute("DELETE FROM artworks WHERE artwork_id NOT IN (SELECT artwork_id FROM artwork_searches) AND artwork_id NOT IN (SELECT artwork_id FROM collected_works)").fetchall()
            conn.commit()
            conn.close()

            conn = get_db_connection()
            collection_title = conn.execute("SELECT title FROM collections WHERE id = ?", [collection_id]).fetchall()[0]['title']
            conn.commit()
            conn.close()

            conn = get_db_connection()
            artworks = conn.execute("SELECT * FROM artworks JOIN collected_works on artworks.artwork_id = collected_works.artwork_id WHERE collected_works.user_id = ? AND collected_works.collection_id = ?", [session["user_id"], collection_id]).fetchall()
            conn.commit()
            conn.close()
            return render_template("collection_showpage.html", artworks=artworks, collection_title=collection_title, collection_id=collection_id)

        else:
            # if the user clicked on a particular artwork's title on the collection showpage, then display the showpage for that artwork
            conn = get_db_connection()
            artwork = conn.execute("SELECT * FROM artworks WHERE artwork_id = ?", [artwork_id]).fetchall()
            conn.commit()
            conn.close()
            return render_template("collection_artwork_showpage.html", artwork=artwork[0], collection_id=collection_id)

