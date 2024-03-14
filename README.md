# Chicago Artwork Collection App

#### Video Demo: https://youtu.be/htQ8wr_J2WU

## I. Introduction:
    This is an application that allows you to search through the collections at the Art Institute of Chicago.
    It fetches data available via their public API for works that are in the public domain.

    You can save images and information about particular works of art according to categories that you create yourself.
    I envisage this being useful for presentations, research, teaching, or just for your own enjoyment.

    All information and images are sourced from the Art Institute of Chicago.
    If you would like to download any of the images, there is a link to the Art Institute's website on the artwork's show page where you can do so.
    I hope you enjoy perusing the art!

    The Art Institute of Chicago's API: https://api.artic.edu/docs/

    The Art Institute of Chicago's Collections: https://www.artic.edu/collection

## II. Description of the User Experience:

### Getting the Application Up and Running:
    Install Python
    Install Flask-Session
    Install python-dotenv
    
    After cloning the repository and navigating to it in your file directory, 
    enter "DB_PATH=aic_collections.db flask run" in the terminal to start the server.

### Searching:
    After registering and logging in, going to 'Search' in the navigation bar
    will take you to the search route where you can enter a search term
    to receive a set of images and information about works of art.

    The first fetch returns up to ten items.
    You can navigate using the arrow icons to fetch additional matches in increments of ten.
    You are also able to navigate to the first or last set of items by clicking on the double arrows.
    If your search has a lot of matches, you are only able get the first 100 pages from the Art Institute.

    When the matches are fetched, they are stored in the database until the user navigates to another route.
    There is no long-term storage of searches; this is only to facilitate navigation through the pages of search results.

    In the case that the user would like to return back to an earlier page that was already viewed,
    not having to fetch the same data from the API multiple times reduces the time it takes to retrieve search results.

### Adding an Item to a Collection:
    Once users have submitted a search term,
    they can click on the titles of matches in the search results list
    to see an expanded view of the artwork with more information about it.

    On that showpage, the user can add the item to a collection.
    There is a select menu with the first option being the search term
    and the rest of the options being the titles of collections that the user already has.

    If the search term is selected from the options and is not already the name of a collection,
    a collection will be created with the search term as the title.

    After adding a work to a collection, users are taken back to the results page where they were before.

    In the case that they do not want to select the artwork for a collection,
    there is also a back button to take them back to the last search results page they were on.

### Adding Items to Collections:
    When users navigate to the collection route via the navigation bar at the top of the screen,
    there is a list of their collections along with inputs for creating or deleting a collection.

    If you click on one of the collection titles in the list, you will be taken to the collection showpage,
    where there is an image of all of the works of art in the collection along with their titles.

    The title is a clickable button that takes you to the showpage for that work of art,
    where there is an enlarged image of the artwork and further information about it.

    There is also a link to get more information about the item on the Art Institute of Chicago's website,
    and there are buttons to either remove the work from the collection or to return to the collection.

    Users can add an artwork to multiple collections and can delete an artwork from one collection while leaving it in another.
    Clicking the delete button only deletes the work from the particular collection that the user is currently viewing.

    Collections are specific to individual users stored in the database.
    So, if one user deletes a work of art from their collection, it does not affect another user's collections.
    Collections are not shared between users or viewable by anyone but themselves.

## III. Technical Overview:
    This application is built using Python, SQL, Jinja, and Flask.
    I created it after doing the final Finance problem set for the EdX Harvard CS50 class,
    applying what I learned from the course overall and what I learned from that problem set in particular.

    The essence of the work on this application is my own (I am communicating with a different API,
    am allowing for different sorts of user interaction with the data that I fetch,
    and am displaying that information in a different way),
    but I want to acknowledge that I built on what I learned.

    The Finance problem set showed me how to register and log in a user,
    how to run the server using Flask,
    how to use Jinja for template rendering,
    and how to communicate with the database, for example.

    Beyond that I drew from the coursework overall,
    from the years I spent studying web development,
    and from my two years of experience working as a software engineer.

## IV. File Structure
    The main file is app.py, where all of the routes are defined to control what happens
    depending on where a user is in the app.

    The templates directory holds all of the views rendered with Jinja,
    which includes HTML, applies the CSS styles, and allows for some logic
    such as loops for mapping over data to display it.

    The static files directory includes the CSS styles.

    The helper_methods file has a few functions for retrieving information from fetches
    to the API endpoints and from the database via queries.

    The database is in project.db.

## V. Routes, Templates, and Methods:

### Layout.html:
    This includes the navigation bar, which appears on every route.
    All of the other templates extend this file.

### Registration and Login Routes:
    There is a registration route to create a username and password for a user.
    That renders the register.html template.
    The password is hashed before being stored in the database for security purposes,
    and the username is checked so that there are no duplicate usernames.

    Upon successful registration, a user is automatically logged in.
    I thought avoiding having the user re-enter login credentials created a more seamless user experience.

    If the user already has a login, they can go to the login page.
    The login route renders the login.html template.
    Upon successful login, a user is brought to the home page, which has a brief welcome message
    that explains the functionality of the app.

### Index Route:
    The index route either displays the welcome message in index.html
    or redirects to login.html if there is no user logged in.

### The Search Route:
    The search route has handling for a 'get' or a 'post' request.

    A 'get' request returns the search.html template for the form to display the search input,
    where a user can type in a search term.

    The 'put' request eventually renders the search_results.html template.

    First it calls the get_items method from the helper_methods file,
    passing in the search term and the page number request (1).
    That method makes a request to the Art Institute of Chicago API to get the first 10 matches,
    then processes the data to store it in the database.

    The reason information is stored in the database before being returned
    for display to the user is to save the user time in navigating between pages.
    (When a user navigates away from the search_results page, the user's last search is deleted,
    so the search is only saved while the user is actively searching.)
    If the requested page, with all its associated information, has already been saved in the database,
    then we do not make a fetch and are able to query the database instead.

    These are the database tables that I leverage in the get_items method and elsewhere to track a user's search:

    TABLE searches (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, user_id INTEGER, name TEXT UNIQUE NOT NULL, page_limit INTEGER)

    TABLE artwork_searches (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, artwork_id INTEGER, search_id INTEGER, current_page INTEGER)

    TABLE artworks (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, title TEXT, alt_text TEXT,
    artwork_id INTEGER NOT NULL, art_institute_url TEXT, display_url TEXT, artist_info TEXT, date_info TEXT)

    The artworks table stores some of the data that is returned from the API to display artwork information to the user.
    This is used when displaying both search results and artwork showpages for a user's collections.

    The searches table includes the search term (stored as 'name'), a page limit, and a user id.

    The user id allows the search to be specific to a user,
    and it allows for the search to be deleted when a particular user navigates away from the search results.

    The page limit is stored in order to handle pagination for the search.
    It allows the application to let the user know how many pages of information are available,
    though data is fetched incrementally as a user navigates with the pagination arrows.
    It also allows for calculating whether users are able to go further ahead.
    If they have already reached the page limit and are trying to go forward, that is not possible.

    If the page total is more than 100, it is scaled back to 100, because the API returns a 403
    if pages beyond that number are requested. They encourage you to refine your search to narrow the results.
    The API documentation states that you can get a data dump instead, but that was beyond the scope of this project.

    The 'artwork_searches' table is a join table between artworks and searches.
    It allows for tracking of the current page number for an artwork as it appears in a particular search.
    That information cannot be on the artwork table, because the artwork could appear in lots of different searches,
    and it would not necessarily be on the same page in different searches.
    The join table allows for artworks to be displayed in a paginated way based on the current search.
    The database can be queried to display the artworks that belong to a particular page of a particular search,
    and all of the artwork information that is needed is available through the join.

### The Search Results Route:
    The search results route has handling for a post request.
    It handles the case of the user trying to move backwards or forwards through the search results.
    If the page a user is trying to go to exists, the get_items method is called with the requested page number passed in.

    I am passing a lot of information to the routes via hidden input fields to retain information about
    the search and where the user is in the search results. This is not ideal;
    though it is working, it is something I could improve upon in the future (more on that below).

### The Artwork Showpage Route:
    When users are viewing the list of search results, they can select a title
    and go to the showpage for it. Clicking on the title takes them to the artwork_showpage route.

    The artwork_showpage route calls the get_image_url method in helper_methods.
    This function makes a new API call for information specific to that artwork.
    In order to get certain information, including the pieces of the puzzle to construct the url for displaying an image,
    this API call has to be made for individual works.

    Since it would be a time drain to make all of these calls from the beginning,
    it seemed safe to make individual calls for this information when a user goes to a show page.

    After this fetch is made, the information is saved by updating the already-existing row for the artwork.
    The get_image_url method could be improved to check whether we already have the information we need
    in the database before making the API call, just like at the beginning of the get_items method.

    In the artwork_showpage.html file that is rendered, information about the artwork is displayed,
    and there is a link to the Art Institute's website with more information about the work.

    There is also a select input for adding the artwork to one of a user's collections.
    The first select option is the current search term, and if the user selects that,
    then a new collection with the search term as the title is created, if one with that name did not already exist.

    After adding an item to a collection, the user is brought back to the search results page they were on before.
    Alternatively, they can return to their search results page by clicking the back button.


### The Collections Routes:
    There are three collections routes: collections, collection_showpage, and collection_artwork_showpage.

    When the user goes to the collections route, the collections.html file is rendered,
    and the list of a user's collections is displayed.

    Users see titles of all of their collections that can be clicked on to go to the collection showpage.
    Below that list are two forms, one for deleting a collection and one for adding a collection.

    If the route receives a 'post' request, it means a user is trying to delete or create a collection,
    and a query is made to the database to do so.

    These are the tables related to collections:

    TABLE collected_works (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, user_id INTEGER, artwork_id INTEGER, collection_id INTEGER)
    TABLE collections (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, user_id INTEGER NOT NULL, title NOT NULL)
    TABLE artworks (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, title TEXT, alt_text TEXT,
    artwork_id INTEGER NOT NULL, art_institute_url TEXT, display_url TEXT, artist_info TEXT, date_info TEXT)

    The artworks table was described above; it contains information about particular artworks for display.
    The collections table has a title and a user id to associate it with a particular user.
    The 'collected works' table is a join between a user's collection and the artworks table.
    It allows the database to be queried to get the particular artworks associated with a user's collection.

    When a user "collects" an artwork, a collection may need to be generated if it does not exist yet,
    and a collected_work also has to be generated.

    When a collection is deleted, the collected_works have to be deleted, too.
    If the artwork associated with that collection is not associated with a search
    or with another user's collection, then it is also deleted from the database.

    When the user clicks on a title in the collection list, they can see
    an image of all of the works in that collection along with the titles.
    When they click on the title on the collection_showpage, they are brought
    to the collection_artwork_showpage route.

    The collection artwork showpage is much like the artwork showpage.
    However, instead of having a select dropdown for adding a work to a collection,
    there is a button for deleting the work from the collection.

    The back button on the showpage takes the user back to the collection_showpage route.

### Error_message.html:
    This takes an argument of a message that it plugs into the template
    to let the user know what went wrong.

## VI. Ideas for Improvement or Future Work:

    A. My limited knowledge of Jinja (and possibly the limitations of Jinja?)
    led me to create forms in the templates where I really just wanted a button
    with an onclick event handler that calls a function and passes information as arguments.
    Instead, I used forms to pass information in hidden input fields, but this seems like bad design.
    Better state management tools might have also obviated the need for passing along information in this way.

    The artwork_showpage and collection_artwork_showpage templates have a lot of similarities;
    they should share a template with common features extended to both.
    However, there were some issues related to passing information from the forms that made that a challenge.

    In the future, I would learn more about what Jinja is capable of.
    I would also consider using a Javascript framework for the front-end instead,
    with a backend framework for using Python to communicate with the database and make API calls.


    B. I would consider changing the list of search results from being a list of titles to displaying the
    ten images associated with the search results on the current page for a nicer display.
    It would take a little longer to load but might be worth the wait if a brief loading page was used.

    Similarly, I could improve the display of the user's collections page, where the titles of collections are listed.
    

    C. The search terms entered into the search box should be sanitized before making the api calls.


    D. If this application were being used for educational or research purposes, it might feel limited to only
    be able to get artwork from the Art Institute of Chicago's API,
    even given the large collection that they have.

    I could build the application out more to fetch data from other institutions.
    However, that could end up being a big project.
    So for now I prefer to focus on the Art Institute in this city that I love.


