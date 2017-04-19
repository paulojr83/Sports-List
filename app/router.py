from sqlalchemy.orm.exc import NoResultFound\
    , MultipleResultsFound

from engine import *
from flask import session as login_session
import random
import string

from flask import Flask, render_template, jsonify, request\
    , flash\
    , redirect\
    , url_for

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Sport Catalog Application"

def login_verified():
    access_token = login_session.get('access_token')
    if access_token:
        return True
    return False

@app.route('/')
def home():
    categories = session.query(Category).all()
    sports = session.query(Sport).order_by(Sport.id.desc()).limit(5).all()
    access = login_verified()
    return render_template('home.html', categories=categories, sports=sports, rows=-1, access=access)

@app.route('/about')
def about():
    access = login_verified()
    return render_template('about.html',access=access)

@app.route('/login')
def login():
    access = None
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state, access=access)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    return output


@app.route('/gdisconnect')
def logout():
    if 'username' in login_session:
        access_token = login_session['access_token']
        print access_token
        if access_token is None:
            response = make_response(json.dumps('Current user not connected.'), 401)
            response.headers['Content-Type'] = 'application/json'
            return response

        url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % login_session['access_token']
        h = httplib2.Http()
        result = h.request(url, 'GET')[0]
        if result['status'] == '200':
            del login_session['access_token']
            del login_session['gplus_id']
            del login_session['username']
            del login_session['email']
            del login_session['picture']
            response = make_response(json.dumps('Successfully disconnected.'), 200)
            response.headers['Content-Type'] = 'application/json'
            flash("you are now disconnected")

        else:
            response = make_response(json.dumps('Failed to revoke token for given user.', 400))
            response.headers['Content-Type'] = 'application/json'
            flash("Failed to revoke token for given user")
            return redirect(url_for('home'))
    else:
        flash("Failed to revoke token for given user")
        return redirect(url_for('home'))

    return redirect(url_for('home'))

@app.route('/category/new/', methods=['GET', 'POST'])
def newCategory():
    if 'username' not in login_session:
        return redirect('/login')
    access = login_verified()
    if request.method == 'POST':
        newCategory = Category(name=request.form['name'])
        session.add(newCategory)
        session.commit()
        flash('A new category add in your catalog!')
        return redirect(url_for('home'))
    else:
        return render_template('new-category.html', access=access)

@app.route('/category/<int:category_id>/edit/', methods=['GET', 'POST'])
def editCategory(category_id):
    if 'username' not in login_session:
        return redirect('/login')
    access = login_verified()
    if request.method == 'POST':
        category = session.query(Category).filter_by(id=category_id).one();
        if category != []:
            name=request.form['name']
            category.name=name
            category.id=category.id
            session.add(category)
            session.commit()
            flash('Category has been edited!')
        return redirect(url_for('home'))
    else:
        category = session.query(Category).filter_by(id=category_id).one();
        return render_template('edit-category.html', category=category, access=access)


@app.route('/sport/<int:sport_id>/detail/', methods=['GET'])
def detailSport(sport_id):
    access = login_verified()
    sport = session.query(Sport).filter_by(id=sport_id).one();
    return render_template('detail-sport.html', sport=sport, access=access)

@app.route('/sport/<int:sport_id>/edit/', methods=['GET', 'POST'])
def editSportCategory(sport_id):
    if 'username' not in login_session:
        return redirect('/login')

    access = login_verified()
    if request.method == 'POST':
        sport = session.query(Sport).filter_by(id=sport_id).one();
        if sport != []:
            title = request.form['title']
            description = request.form['description']
            history = request.form['history']
            origin = request.form['origin']
            cat_id = sport.category.id
            sport = Sport(title=title, description=description, history=history, origin=origin, cat_id=cat_id)
            session.add(sport)
            session.commit()
            flash('Sport has been edited!')
        return redirect(url_for('home'))
    else:
        sport = session.query(Sport).filter_by(id=sport_id).one();
        return render_template('edit-sport.html', sport=sport, access=access)

@app.route('/category/<int:category_id>/item/', methods=['GET'])
def showSportFromCategory(category_id):
    access = login_verified()
    categories = session.query(Category).all()
    sports = session.query(Sport).filter_by(cat_id=category_id).order_by(Sport.id.desc()).all()
    rows = session.query(Sport).filter_by(cat_id=category_id).count()
    return render_template('home.html', categories=categories, sports=sports, rows=rows, access=access)

@app.route('/sport/<int:category_id>/item/', methods=['GET', 'POST'])
def newSportCategory(category_id):
    if 'username' not in login_session:
        return redirect('/login')
    access = login_verified()
    if request.method == 'POST':
        category = session.query(Category).filter_by(id=category_id).one();
        if category != []:
            title = request.form['title']
            description = request.form['description']
            history = request.form['history']
            origin = request.form['origin']
            cat_id = category.id

            sport = Sport(title=title,description=description,history=history,origin=origin,cat_id=cat_id)
            session.add(sport)
            session.commit()

            flash('A new sport add in your catalog!')
        return redirect(url_for('home'))
    else:
        category = session.query(Category).filter_by(id=category_id).one();
        return render_template('new-sport.html', category=category,access=access)

@app.route('/category/<int:category_id>/delete/', methods=['GET', 'POST'])
def deleteCategory(category_id):
    if 'username' not in login_session:
        return redirect('/login')
    access = login_verified()
    if request.method == 'POST':
        category = session.query(Category).filter_by(id=category_id).one();
        if category:
            session.delete(category)
            session.commit()
            flash('Category has been deleted!')
            return redirect(url_for('home'))

    else:
        category = session.query(Category).filter_by(id=category_id).one();
        return render_template('delete-category.html',category=category, access=access)

@app.route('/sport/<int:sport_id>/delete/', methods=['POST'])
def deleteSportCategory(sport_id):
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        sport= session.query(Sport).filter_by(id=sport_id).one();
        if sport:
            session.delete(sport)
            session.commit()
            flash('Sport has been deleted!')
            return redirect(url_for('home'))

@app.route('/category/catalog.json')
def catalog():
    if 'username' not in login_session:
        return redirect('/login')
    try:
        categories = session.query(Category).all()
        Categories=[]
        for category in categories:
            Categories.append(category.serialize)
        return jsonify(Categories=Categories)

    except (NoResultFound,MultipleResultsFound):
        return jsonify(error='No result Found!', code=404)

def createUser(login_session):
    newUser = User(name=login_session['username']
                   ,email=login_session['email']
                   ,picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id

def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user

def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None

if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)