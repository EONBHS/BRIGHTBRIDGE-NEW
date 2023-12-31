from flask import render_template, redirect, request, abort, session, make_response, Response
from flask_cors import CORS, cross_origin
from app import app, db
from app.models import User, Games, Jams, GameJamGames
from werkzeug.utils import secure_filename
from sqlalchemy import desc, asc, func, and_, or_, not_
from datetime import datetime
import os
import json
import requests
import random
import string
import hashlib
# http
import requests
import json
import urllib.parse
import urllib.request
import urllib.error






# GOOGLE AUTH
from google_auth_oauthlib import flow
from google.oauth2 import id_token
import google.auth.transport.requests

import pathlib
import os
import zipfile
import requests
import cachecontrol

cors = CORS(app)



os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

GOOGLE_CLIENT_ID = "81031882791-gsi00o9hkktjep6ughav7vka774fv7bc.apps.googleusercontent.com"
client_secrets_file = os.path.join(
    pathlib.Path(__file__).parent, "client_secrets.json")
app.config['UPLOAD_FOLDER'] = 'app/static/temp'
app.config['JAM_FOLDER'] = 'app/static/jams'


flow = flow.Flow.from_client_secrets_file(
    client_secrets_file=client_secrets_file,
    scopes=["https://www.googleapis.com/auth/userinfo.profile",
            "https://www.googleapis.com/auth/userinfo.email", "openid"],
    redirect_uri="http://127.0.0.1:5000/callback"
)


def login_is_required(function):
    def wrapper(*args, **kwargs):
        if 'google_id' not in session:
            return abort(401)
        else:
            return function()
    return wrapper

# Login required


@app.route("/login")
def login():
    authorization_url, state = flow.authorization_url()
    session['state'] = state
    return redirect(authorization_url)

# google Callback


@app.route("/callback")
def callback():
    """Callback route after successful Google OAuth2 authorization."""
    flow.fetch_token(authorization_response=request.url)
    if not session["state"] == request.args["state"]:
        abort(500)

     # Verify the ID token and retrieve user information
    credentials = flow.credentials
    request_session = requests.session()
    cached_session = cachecontrol.CacheControl(request_session)
    token_request = google.auth.transport.requests.Request(
        session=cached_session)

    id_info = id_token.verify_oauth2_token(
        id_token=credentials._id_token,
        request=token_request,
        audience=GOOGLE_CLIENT_ID
    )

    # Store user information in the session
    session['google_id'] = id_info['sub']
    session['name'] = id_info['name']
    session['email'] = id_info['email']
    session['picture'] = id_info['picture']

    # If user already exists in database
    if User.query.filter_by(google_ID=session['google_id']).first():
        session['logged_in'] = True
        print("User already exists")
        return redirect('/')
    else:
        new_user = User(google_ID=session['google_id'], name=session['name'],
                        email=session['email'], Profilepicture=session['picture'])
        db.session.add(new_user)
        db.session.commit()
        session['logged_in'] = True
    return redirect('/')


@app.route("/logout")
def logout():
    """Clears the session data to log out the user."""
    session.clear()
    return redirect('/')


@app.route('/', methods=["GET", "POST"])
def home():
    games = Games.query.all()

    return render_template('index.html', games=games)


@app.route('/browse', methods=["GET", "POST"])
def browse():
    ''' Route Responsible for displaying catagories games by Genre'''
    actions = Games.query.filter(Games.genre == "1").all()
    adventures = Games.query.filter(Games.genre == "2").all()
    rpgs = Games.query.filter(Games.genre == "3").all()
    strategys = Games.query.filter(Games.genre == "4").all()
    sports = Games.query.filter(Games.genre == "5").all()
    simulations = Games.query.filter(Games.genre == "6").all()
    puzzles = Games.query.filter(Games.genre == "7").all()
    idles = Games.query.filter(Games.genre == "8").all()
    horrors = Games.query.filter(Games.genre == "9").all()
    platformers = Games.query.filter(Games.genre == "10").all()
    others = Games.query.filter(Games.genre == "11").all()
    return render_template('browse.html', actions=actions, adventures=adventures, rpgs=rpgs, strategys=strategys, sports=sports, simulations=simulations, puzzles=puzzles, idles=idles, horrors=horrors, platformers=platformers, others=others)

@app.route('/dashboard', methods=["GET", "POST"])
def dashboard():
    ''' This Route acts as a bridge between the Add Game View own Games page '''
    return render_template('dashboard.html')


@app.route('/addgame')
def upload():

    jams = Jams.query.all()
    """Renders the game upload page."""
    return render_template('addgame.html', jams=jams)


@app.route('/zip', methods=["GET", "POST"])
def zip():
    """Handles game zip file uploads."""
    if request.method == 'POST':
        name = request.form.get('Title')
        description = request.form.get('GameDescription')
        downloadable = bool(request.form.get('Downloadable'))
        jam_id= request.form.get('jam_id')
        genre = request.form.get('genre')
        splashscreen = request.files.get('splashscreen')
        file = request.files.get('zipfile')

        filename = secure_filename(file.filename)
        # save file
        if os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], filename)):
            print("File exists")
        else:
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            # create directory with the name of the zip file
            dirname = os.path.splitext(filename)[0]
            dirpath = os.path.join('app/static/temp', dirname)
            os.mkdir(dirpath)
            splash = secure_filename(splashscreen.filename)
            splashscreen.save(os.path.join(dirpath, splash))

            new_game = Games(name=name, description=description, downloadable=downloadable, genre=genre,User_ID=session['google_id'], splashscreen=splash, filename=filename, dirname=dirname, dirpath=dirpath,jam_id=jam_id)
            db.session.add(new_game)
            db.session.commit()

            jam_id = 1
            if jam_id != 0:
                GameID = Games.query.filter(Games.name == name).first()
                new_jamgame = GameJamGames(jam_id=jam_id, game_id=GameID.id,splashscreen=splash)
                db.session.add(new_jamgame)
                db.session.commit()
            else:
                pass
            with zipfile.ZipFile(os.path.join(app.config['UPLOAD_FOLDER'], filename), 'r') as zip_ref:
                zip_ref.extractall(dirpath)
            return redirect("/dashboard")
        

            
        # JAM ID IS NOT BEING DEFINED! JAM ID IS EQUAL TO NOTHING!
        # GAMEID.ID IS ALSO NOT BEING DEFINED
      
        # extract contents of the zip file to the new directory
       


@app.route('/<int:id>', methods=["GET", "POST"] )
@cross_origin(origin='http://localhost:5000',headers=['Content- Type','Authorization'])
def game(id):
    # Response = make_response(render_template('game.html', game=game))
    # Response.headers['Cross-Origin-Opener-Policy'] = 'same-origin'
    # Response.headers['Cross-Origin-Embedder-Policy'] = 'require-corp'
    """Displays a specific game based on its ID."""
    game = Games.query.get(id)
    return render_template('game.html', game=game)

@app.route('/jam/addjam')
def addjam():
    """Renders the game upload page."""
    return render_template('createjam.html')

@app.route('/createjam', methods=["GET", "POST"])
def create_jams():
    # Create a jam
    if request.method == 'POST':
        name = request.form.get('JamName')
        description = request.form.get('JamDescription')
        startdate = request.form.get('JamStartDate')
        enddate = request.form.get('JamEndDate')
        image = request.files.get('JamImage')

        imagename = secure_filename(image.filename)
        image.save(os.path.join(app.config['JAM_FOLDER'], imagename))

        new_jam = Jams(name=name, description=description, startdate=startdate,image=imagename,enddate=enddate)
        db.session.add(new_jam)
        db.session.commit()
        return redirect('/jams')
    else:
        return render_template('createjam.html')  
    
@app.route('/jam/<int:id>', methods=["GET", "POST"])
def jam(id):
    # Display a jam
    jams = Jams.query.get(id)
    jamgames = GameJamGames.query.filter_by(jam_id = id).all()
    return render_template('jam.html', jam=jams, jamgames=jamgames)

        
@app.route('/jams', methods=["GET", "POST"])
def display_jams():
    # Display all jams
    jams = Jams.query.all()
    return render_template('jams.html', jams=jams)

@app.route("/search", methods=["GET", "POST"])
def search():
    """Handles game search requests."""
    if request.method == 'POST':
        search = request.form.get('search')
        games = Games.query.filter(Games.name.contains(search)).all()
        return render_template('search.html', games=games, search=search)
    return render_template('index.html')

@app.errorhandler(404)
def page_not_found(e):
    """Handles 404 page not found errors."""
    return render_template('404.html'), 404
