# all the imports
import sqlite3, os
from functools import wraps
from datetime import date
from flask import Flask, request, session, g, redirect, url_for, \
     abort, render_template, flash, jsonify, Response

# configuration
DATABASE = 'db/users.db'
DEBUG = True
SECRET_KEY = '\x98\x92Fn\xd3ko\xe3\x87We\x16\x01A}\xae\xaf1<"K-\x1a\xb9'
MAIL_FROM = "mail.geeklove@gmail.com"
MAIL_PASSWORD = "admingeek"


app = Flask(__name__)
app.config.from_object(__name__)


# construct user dictionary
def user_dict_factory(cursor, row):
    fields_to_split = ['courses', 'favourite_bands', 'favourite_movies',
                       'favourite_TV_shows', 'favourite_books', 
                       'favourite_hobbies', 'hair_colours']
    d = {}
    for idx, col in enumerate(cursor.description):
        value = row[idx] if row[idx] else ''
        if col[0] in fields_to_split:
            d[col[0]] = value.split('|')
        else:
            d[col[0]] = value
    return d




# def login_required(func):
#     @wraps(func)
#     def decorated_function(*args, **kwargs):
#         if g.user is None:
#             return redirect(url_for('login', next=request.url))
#         return f(*args, **kwargs)
#     return decorated_function


def connect_db():
    return sqlite3.connect(app.config['DATABASE'])


@app.before_request
def before_request():
    g.db = connect_db()
    g.db.row_factory = user_dict_factory

    # construct dictionary of users
    g.users = {}
    cur = g.db.execute('select * from users')
    for row in cur.fetchall():
        g.users[row['username']] = row

    # calculate ages
    today = date.today()
    for user in g.users.values():
        year, month, day = user['birthdate'].split('/')
        year = int(year)
        month = int(month)
        day = int(day) 
        age = today.year - year - ((today.month, today.day) < (month, day))
        user['age'] = age
        user['gender'] = user['gender'].capitalize()

    # set current user
    g.user = None;
    if session.get('logged_in'):

        username = session.get('username')
        password = session.get('password')
        if username in g.users and \
            password == g.users[username]['password']:
            g.user = g.users[username]



@app.teardown_request
def teardown_request(exception):
    redirect(url_for('home'))


@app.route('/')
def home():
    if g.user:
        profiles = g.users.values()[0:12]
        return render_template('browse.html', profiles=profiles)
    else:
        return render_template('login.html')

@app.route('/page/<int:page_num>')
def browse(page_num):
    if g.user:
        per_page = 12
        end = per_page * page_num       #slice start
        start = end - per_page          #slice end
        profiles = g.users.values()[start:end]
        num_users = len(g.users)
        num_pages = num_users/per_page

        next_num = page_num+1 if per_page * page_num < num_users else 0
        prev_num = page_num-1 if page_num > 1 else 0

        return render_template('browse.html', 
                                profiles=profiles, 
                                next_num=next_num, 
                                prev_num=prev_num)
    else:
        return render_template('login.html')




# @app.route('/')
# def show_entries():
#     cur = g.db.execute('select title, text from entries order by id desc')
#     entries = [dict(title=row[0], text=row[1]) for row in cur.fetchall()]
#     return render_template('show_entries.html', entries=entries)

# @app.route('/add', methods=['POST'])
# def add_entry():
#     if not session.get('logged_in'):
#         abort(401)
#     g.db.execute('insert into entries (title, text) values (?, ?)',
#                  [request.form['title'], request.form['text']])
#     g.db.commit()
#     flash('New entry was successfully posted')
#     return redirect(url_for('show_entries'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username not in g.users:
            error = 'Invalid username'
        elif password != g.users[username]['password']:
            error = 'Invalid password'
        else:
            session['logged_in'] = True
            session['username'] = username
            session['password'] = password

            flash('You were logged in')

            return redirect(url_for('home'))
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('home'))

@app.route('/profile_img/<username>')
def profile_img(username):
    # send_static_file will guess the correct MIME type
    path = os.path.join('profile', username, 'profile.jpg')
    if not os.path.isfile(os.path.join('static', 'profile', username, 'profile.jpg')):
        path = 'profile.jpg'
    return app.send_static_file(path)


# Render custom.css since it requires urls to static files
@app.route('/custom')
def custom_css():
    return Response(render_template('custom.css'), mimetype='text/css')
    
if __name__ == '__main__':
    app.debug = True
    app.run()