from sqlalchemy.orm.exc import NoResultFound\
    , MultipleResultsFound\
    , ConcurrentModificationError\
    , FlushError

from sqlalchemy.orm.exc import NoResultFound\
    , MultipleResultsFound\
    , ConcurrentModificationError\
    , FlushError

from engine import *

from flask import \
    Flask\
    , render_template\
    , jsonify\
    , request\
    , flash\
    , redirect\
    , url_for

app = Flask(__name__)

@app.route('/')
@app.route('/categories')
def home():
    categories = session.query(Category).all()
    sports = session.query(Sport).order_by(Sport.id.desc()).limit(5).all()
    return render_template('home.html', categories=categories, sports=sports)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/login')
def login():
    return render_template('login.html')


@app.route('/category/new/', methods=['GET', 'POST'])
def newCategory():
    if request.method == 'POST':
        newCategory = Category(name=request.form['name'])
        session.add(newCategory)
        session.commit()
        flash('A new category add in your catalog!')
        return redirect(url_for('home'))
    else:
        return render_template('new-category.html')


@app.route('/category/<int:category_id>/edit/', methods=['GET', 'POST'])
def editCategory(category_id):
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
        return render_template('edit-category.html', category=category)


@app.route('/sport/<int:sport_id>/detail/', methods=['GET'])
def detailSport(sport_id):
    sport = session.query(Sport).filter_by(id=sport_id).one();
    return render_template('detail-sport.html', sport=sport)

@app.route('/sport/<int:sport_id>/edit/', methods=['GET', 'POST'])
def editSportCategory(sport_id):
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
        return render_template('edit-sport.html', sport=sport)

@app.route('/category/<int:category_id>/item/', methods=['GET'])
def showSportFromCategory(category_id):
    categories = session.query(Category).all()
    sports = session.query(Sport).filter_by(cat_id=category_id).order_by(Sport.id.desc()).all()

    return render_template('home.html', categories=categories, sports=sports)

@app.route('/category/<int:category_id>/item/', methods=['GET', 'POST'])
def newSportCategory(category_id):
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
        return render_template('new-sport.html', category=category)

@app.route('/category/<int:category_id>/delete/', methods=['GET', 'POST'])
def deleteCategory(category_id):
    if request.method == 'POST':
        category = session.query(Category).filter_by(id=category_id).one();
        if category:
            session.delete(category)
            session.commit()
            flash('Category has been deleted!')
            return redirect(url_for('home'))

    else:
        category = session.query(Category).filter_by(id=category_id).one();
        return render_template('delete-category.html',category=category)

@app.route('/sport/<int:sport_id>/delete/', methods=['POST'])
def deleteSportCategory(sport_id):
    if request.method == 'POST':
        sport= session.query(Sport).filter_by(id=sport_id).one();
        if sport:
            session.delete(sport)
            session.commit()
            flash('Sport has been deleted!')
            return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)