from sqlalchemy.orm.exc import NoResultFound\
    , MultipleResultsFound

from engine import *
from flask import session as login_session
import random
import string
from functools import wraps

from flask import Flask, render_template, jsonify, request, g, flash\
    , redirect\
    , url_for

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)

ERROR_PERMISSION = "You don't have permission to do this"
MESSAGE_ERROR = 'error'
MESSAGE_INFO = 'info'
MESSAGE_WARNING= 'warning'
MESSAGE_SUCCESS= 'success'

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Sport Catalog Application"

def login_permission(id_permission):
    """Verified if user has permission to modifiel data
    :return: user
    """
    user_id = getUserID(login_session['email'])
    if (user_id == id_permission):
        return user_id
    else:
        return None

def login_verified():
    """Verified if user is login and then return User"""
    access_token = login_session.get('access_token')
    if access_token == None:
        return None
    else:
        user = getUser(login_session['email'])
        if access_token and user.id:
            return user
    return False

def login_required(f):
    """Verified with user is login login_session"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in login_session:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def home():
    categories = session.query(Category).all()
    sports = session.query(Sport).order_by(Sport.id.desc()).limit(5).all()
    user = login_verified()
    return render_template('home.html', categories=categories, sports=sports, rows=-1, user=user)

@app.route('/about')
def about():
    user = login_verified()
    return render_template('about.html',user=user)

@app.route('/login')
def login():
    access = None
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state, access=access)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token and connect by google account
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
        response = make_response(json.dumps('Current user is already connected.'),200)
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
    flash("you are now logged in as %s" % login_session['username'], MESSAGE_INFO)

    """
    Verifild if use has login add on database, with don't create a one
    """
    user_id=getUserID(login_session['email'])
    if user_id==None:
        createUser(login_session)

    return output


@app.route('/gdisconnect')
def logout():
    """ Validate with has user login and dicconnect from google account"""
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
            flash("you are now disconnected", MESSAGE_WARNING)

        else:
            response = make_response(json.dumps('Failed to revoke token for given user.', 400))
            response.headers['Content-Type'] = 'application/json'
            flash("Failed to revoke token for given user", MESSAGE_ERROR)
            return redirect(url_for('home'))
    else:
        flash("Failed to revoke token for given user", MESSAGE_ERROR)
        return redirect(url_for('home'))

    return redirect(url_for('home'))

@app.route('/category/new/', methods=['GET', 'POST'])
@login_required
def newCategory():
    """
    Verifild with use has login and able to create a new category
    """
    user = login_verified()

    if request.method == 'POST':
        user_id = getUserID(login_session['email'])
        newCategory = Category(name=request.form['name'])
        newCategory.user_id =user_id
        session.add(newCategory)
        session.commit()
        flash('A new category add in your catalog!', MESSAGE_SUCCESS)
        return redirect(url_for('home'))
    else:
        return render_template('new-category.html', user=user)



@app.route('/category/<int:category_id>/edit/', methods=['GET', 'POST'])
@login_required
def editCategory(category_id):
    """
    Verifild if user has login and able to create a new category
    """
    user = login_verified()
    if request.method == 'POST':
        category = session.query(Category).filter_by(id=category_id).one()
        # Verifield if user has permission to edit the category
        user_id = login_permission(category.user_id)
        if user_id != None:
            if category != []:
                name=request.form['name']
                category.name=name
                category.user_id = user_id
                category.id=category.id
                session.add(category)
                session.commit()
                flash('Category has been edited!', MESSAGE_INFO)
            return redirect(url_for('home'))
        else:
            flash(ERROR_PERMISSION, MESSAGE_ERROR)
            return redirect(url_for('home'))
    else:
        category = session.query(Category).filter_by(id=category_id).one()
        return render_template('edit-category.html', category=category, user=user)


@app.route('/sport/<int:sport_id>/detail/', methods=['GET'])
def detailSport(sport_id):
    user = login_verified()
    sport = session.query(Sport).filter_by(id=sport_id).one()
    return render_template('detail-sport.html', sport=sport, user=user)

@app.route('/sport/<int:sport_id>/edit/', methods=['GET', 'POST'])
@login_required
def editSportCategory(sport_id):
    """
      Verifild with user has login 
    """
    access = login_verified()
    if request.method == 'POST':
        sport = session.query(Sport).filter_by(id=sport_id).one()
        """Verifield if user has permission to edit the item from category"""
        user_id = login_permission(sport.user_id)
        if user_id != None:

            if sport != []:
                title = request.form['title']
                description = request.form['description']
                history = request.form['history']
                origin = request.form['origin']
                cat_id = sport.category.id
                sport = Sport(title=title, description=description, history=history, origin=origin, cat_id=cat_id)
                sport.user_id = user_id
                session.add(sport)
                session.commit()
                flash('Sport has been edited!',MESSAGE_WARNING)
            return redirect(url_for('home'))
        else:
            flash(ERROR_PERMISSION, MESSAGE_ERROR)
            return redirect(url_for('home'))
    else:
        sport = session.query(Sport).filter_by(id=sport_id).one()
        return render_template('edit-sport.html', sport=sport, access=access)

@app.route('/category/<int:category_id>/item/', methods=['GET'])
def showSportFromCategory(category_id):
    user = login_verified()
    categories = session.query(Category).all()
    sports = session.query(Sport).filter_by(cat_id=category_id).order_by(Sport.id.desc()).all()
    rows = session.query(Sport).filter_by(cat_id=category_id).count()
    return render_template('home.html', categories=categories, sports=sports, rows=rows, user=user)

@app.route('/sport/<int:category_id>/item/', methods=['GET', 'POST'])
@login_required
def newSportCategory(category_id):
    user = login_verified()
    if request.method == 'POST':
        category = session.query(Category).filter_by(id=category_id).one()
        """Verifield if user has permission to create a new item to category"""
        user_id = getUserID(login_session['email'])
        if category != []:
            title = request.form['title']
            description = request.form['description']
            history = request.form['history']
            origin = request.form['origin']
            cat_id = category.id
            sport = Sport(title=title,description=description,history=history,origin=origin,cat_id=cat_id, user_id=user_id)
            session.add(sport)
            session.commit()

            flash('A new sport add in your catalog!', MESSAGE_SUCCESS)
        return redirect(url_for('home'))
    else:
        category = session.query(Category).filter_by(id=category_id).one()
        return render_template('new-sport.html', category=category,user=user)

@app.route('/category/<int:category_id>/delete/', methods=['GET', 'POST'])
@login_required
def deleteCategory(category_id):
    user = login_verified()
    if request.method == 'POST':
        category = session.query(Category).filter_by(id=category_id).one()
        """Verifield if user has permission to delete category"""
        user_id = login_permission(category.user_id)
        if user_id != None:
            if category:
                session.delete(category)
                session.commit()
                flash('Category has been deleted!', MESSAGE_ERROR)
                return redirect(url_for('home'))
        else:
            flash(ERROR_PERMISSION, MESSAGE_ERROR)
            return redirect(url_for('home'))
    else:
        category = session.query(Category).filter_by(id=category_id).one()
        return render_template('delete-category.html',category=category, user=user)

@app.route('/sport/<int:sport_id>/delete/', methods=['POST'])
@login_required
def deleteSportCategory(sport_id):
    if request.method == 'POST':
        sport= session.query(Sport).filter_by(id=sport_id).one()
        """Verifield if user has permission to delete item """
        user_id = login_permission(sport.user_id)
        if user_id != None:
            if sport:
                session.delete(sport)
                session.commit()
                flash('Sport has been deleted!', MESSAGE_ERROR)
                return redirect(url_for('home'))
        else:
            flash(ERROR_PERMISSION, MESSAGE_ERROR)
            return redirect(url_for('home'))

@app.route('/category/catalog/JSON')
@login_required
def catalog_all():
    """
    Methodo retorn a list with all category and your item 
    :return json list of catalog: 
    """
    try:
        categories = session.query(Category).all()
        Categories=[]
        for category in categories:
            Categories.append(category.serialize)
        return jsonify(Categories=Categories)

    except (NoResultFound,MultipleResultsFound):
        return jsonify(error='No result Found!', code=404)

@app.route('/category/<int:category_id>/catalog/JSON')
@login_required
def catalog(category_id):
    """
    Methodo retorn a list item and you category 
    :return json list of item: 
    """
    try:
        categories = session.query(Category).filter_by(id=category_id).all()
        Categories=[]
        for category in categories:
            Categories.append(category.serialize)
        return jsonify(Categories=Categories)

    except (NoResultFound,MultipleResultsFound):
        return jsonify(error='No result Found!', code=404)

def createUser(login_session):
    """
    Create a new user
    :param login_session: 
    :return user_id: 
    """
    newUser = User(name=login_session['username']
                   ,email=login_session['email']
                   ,picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id

def getUserInfo(user_id):
    """
    Retorn user by user_id
    :param user_id: 
    :return: 
    """
    user = session.query(User).filter_by(id=user_id).one()
    return user

def getUserID(email):
    """
    Retorn user_id by email
    :param email: 
    :return user_id: 
    """
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None

def getUser(email):
    """
    Retorn user by email
    :param email: 
    :return user: 
    """
    try:
        user = session.query(User).filter_by(email=email).one()
        return user
    except:
        return None

if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='localhost', port=5000)