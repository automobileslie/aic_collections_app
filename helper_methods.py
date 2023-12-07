from flask import Flask, flash, redirect, render_template, request, session
import os
import sqlite3
import requests
from dotenv import load_dotenv

load_dotenv()
db_path = os.getenv('DB_PATH')

def get_db_connection():
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def get_items(search_term, page_number):
    # check whether we already stored the information for the requested page in the database
    conn = get_db_connection()
    search_rows = conn.execute("SELECT * FROM searches WHERE name = ? AND user_id = ?", [search_term, session["user_id"]]).fetchall()
    conn.commit()
    conn.close()

    conn = get_db_connection()
    artwork_search_rows = conn.execute("SELECT * FROM artwork_searches JOIN searches on artwork_searches.search_id = searches.id WHERE searches.user_id = ? AND artwork_searches.current_page = ?", [session["user_id"], page_number]).fetchall()
    conn.commit()
    conn.close()

    if not len(search_rows) or not len(artwork_search_rows):
        # if we do not already have the requested page for the current search in the database, make a fetch to the API
        response = requests.get(f'https://api.artic.edu/api/v1/artworks/search?q={search_term}&query[term][is_public_domain]=true&page={page_number}')

        if response.status_code != 200:
            #render an error message if we could not get the requested page
            return render_template("error_message", message="There was an error retrieving that page")

        artworks = response.json()['data']

        # if a page number higher than 100 is requested, the Art Institute responds with a 403 status code, so reset the page limit accordingly
        if response.json()['pagination']['total_pages'] > 100:
            total_pages = 100
        else:
            total_pages = response.json()['pagination']['total_pages']

        # if there is not already a search stored with the current search term, save the current search
        # it is not saved long-term but is stored while the user is performing a search in order to minimize the number of fetches made and help with navigation between pages
        if not len(search_rows):
            conn = get_db_connection()
            conn.execute(
                "INSERT INTO searches (user_id, name, page_limit) VALUES(?, ?, ?)",
                [session["user_id"],
                search_term,
                total_pages
                ]
            ).fetchall()
            conn.commit()
            conn.close()

        conn = get_db_connection()
        search_rows = conn.execute("SELECT * FROM searches WHERE name = ? AND user_id = ?", [search_term, session["user_id"]]).fetchall()
        search_id = search_rows[0]['id']
        conn.commit()
        conn.close()

        print(artworks)


        # set properties of the artwork for display purposes
        for artwork in artworks:
            title = artwork['title']
            artwork_id = artwork['id']
            image_url = f'https://www.artic.edu/artworks/{artwork_id}'

            conn = get_db_connection()
            artwork_rows = conn.execute("SELECT * FROM artworks WHERE artwork_id = ?", [artwork_id]).fetchall()
            conn.commit()
            conn.close()

            # if this artwork does not already exist in the database, create a new row for it
            if not len(artwork_rows):
                conn = get_db_connection()
                conn.execute(
                    "INSERT INTO artworks (title, artwork_id, art_institute_url) VALUES(?, ?, ?)",
                    [title,
                    artwork_id,
                    image_url
                    ]
                ).fetchall()
                conn.commit()
                conn.close()


            conn = get_db_connection()
            artwork_searches = conn.execute("SELECT * FROM artwork_searches WHERE current_page = ? AND artwork_id = ? AND search_id = ?", [page_number, artwork_id, search_id]).fetchall()
            conn.commit()
            conn.close()

            # also create a new artwork_search; this saves the current page number that the artwork belongs to for this user's search
            # it is used to help with paginating the results
            if not len(artwork_searches):
                conn = get_db_connection()
                conn.execute(
                    "INSERT INTO artwork_searches (current_page, search_id, artwork_id) VALUES(?, ?, ?)",
                    [page_number,
                    search_id,
                    artwork_id
                    ]
                ).fetchall()
                conn.commit()
                conn.close()

    artworks = get_artwork_for_search(page_number)

    return artworks

def get_image_url(artwork_id):
    # make a fetch to get more information about a particular artwork
    # this is used for display on the artwork showpages when a user clicks on a title in the search results
    # or it is used for display when a work of art is saved to a collection and its showpage is viewed within a user's collection
    response = requests.get(f'https://api.artic.edu/api/v1/artworks/{artwork_id}')

    if response.status_code != 200:
        return

    image_id = response.json()['data']['image_id']

    if response.json()['config']:
        iiif_url = response.json()['config']['iiif_url']

    artist_info = response.json()['data']['artist_display']
    date_info = response.json()['data']['date_display']

    if response.json()['data']['thumbnail']:
        alt_text = response.json()['data']['thumbnail']['alt_text']

    else:
        alt_text = None

    if iiif_url and image_id:
        full_url = iiif_url + '/' + image_id + '/full/843,/0/default.jpg'
    else:
        full_url = None

    # add the additional information that was fetched and the image url for displaying the image to the row for the artwork
    conn = get_db_connection()
    rows = conn.execute(
            "UPDATE artworks SET alt_text = (?), display_url = (?), artist_info = (?), date_info = (?) WHERE artwork_id = (?)",
            [alt_text,
            full_url,
            artist_info,
            date_info,
            artwork_id
            ]
        ).fetchall()
    conn.commit()
    conn.close()

    return

def get_artwork_for_search(page_number):
    # return all of the works of art in the database that are associated with the user's current search
    conn = get_db_connection()
    search_rows = conn.execute("SELECT * FROM searches WHERE user_id = ?", [session["user_id"]]).fetchall()
    conn.commit()
    conn.close()
    id_of_search = search_rows[0]['id']

    conn = get_db_connection()
    artwork_rows = conn.execute("SELECT * FROM artworks JOIN artwork_searches on artwork_searches.artwork_id = artworks.artwork_id WHERE artwork_searches.search_id = ? AND artwork_searches.current_page = ?", [id_of_search, page_number]).fetchall()
    conn.commit()
    conn.close()
    return artwork_rows

def clear_search():
    # clear the database of the user's last search
    conn = get_db_connection()
    search_rows = conn.execute("SELECT * FROM searches WHERE user_id = ?", [session["user_id"]]).fetchall()
    conn.commit()
    conn.close()

    if len(search_rows):
        search_id = search_rows[0]['id']
        conn = get_db_connection()
        conn.execute("DELETE FROM artwork_searches WHERE search_id = ?", [search_id]).fetchall()
        conn.commit()
        conn.close()

        conn = get_db_connection()
        conn.execute("DELETE FROM searches WHERE user_id = ?", [session["user_id"]]).fetchall()
        conn.commit()
        conn.close()
        # delete artworks that are neither in a current search nor in a collection

        conn = get_db_connection()
        conn.execute("DELETE FROM artworks WHERE artwork_id NOT IN (SELECT artwork_id FROM artwork_searches) AND artwork_id NOT IN (SELECT artwork_id FROM collected_works)").fetchall()
        conn.commit()
        conn.close()
