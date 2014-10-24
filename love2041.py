# all the imports
import sqlite3, os, re
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


# sqlite uses this function to construct user dictionary
def user_dict_factory(cursor, row):
    fields_to_split = ['courses', 'favourite_bands', 'favourite_movies',
                       'favourite_TV_shows', 'favourite_books', 
                       'favourite_hobbies', 'hair_colours']
    user = {}
    for idx, col in enumerate(cursor.description):
        value = row[idx] if row[idx] else ''
        if col[0] in fields_to_split:
            user[col[0]] = value.split('|')
        else:
            user[col[0]] = value
    return user


# Set up current user and users if logged in
def set_up_users():
    g.db = sqlite3.connect(app.config['DATABASE'])
    g.db.row_factory = user_dict_factory

    # construct dictionary of users
    g.users = {}
    cur = g.db.execute('select * from users')
    for row in cur.fetchall():
        g.users[row['username'].lower()] = row

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
        username = session.get('username').lower()
        password = session.get('password')
        if username in g.users and \
            password == g.users[username]['password']:
            g.user = g.users[username]
            # users dict should only contain other users
            del g.users[username]

def login_required(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        set_up_users()
        if g.user:
            return func(*args, **kwargs)
        else:
            return redirect(url_for('login')) 
    return decorated_function



# On teardown exception go home
@app.teardown_request
def teardown_request(exception):
    redirect(url_for('home'))

# Root should redirect to browse if logged in
@app.route('/')
def home():
    return redirect(url_for('browse', page_num=1))


# Browse matches
@app.route('/page/<int:page_num>')
@login_required
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

# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        set_up_users()
        username = request.form['username'].lower()
        password = request.form['password']
        if username not in g.users:
            error = 'Invalid username or password'
        elif password != g.users[username]['password']:
            error = 'Invalid password or password'
        else:
            session['logged_in'] = True
            session['username'] = username
            session['password'] = password

            flash('You were logged in')

            return redirect(url_for('home'))
    return render_template('login.html', error=error)

# Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    if request.method == 'POST':
        pass
        # set_up_users()
        # username = request.form['username'].lower()
        # password = request.form['password']
        # if username not in g.users:
        #     error = 'Invalid username'
        # elif password != g.users[username]['password']:
        #     error = 'Invalid password'
        # else:
        #     session['logged_in'] = True
        #     session['username'] = username
        #     session['password'] = password

        #     flash('You were logged in')

        #     return redirect(url_for('home'))
    else:
        pass

    return render_template('register.html', error=error)

# Register
@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    error = None
    if request.method == 'POST':
        pass
        # set_up_users()
        # username = request.form['username'].lower()
        # password = request.form['password']
        # if username not in g.users:
        #     error = 'Invalid username'
        # elif password != g.users[username]['password']:
        #     error = 'Invalid password'
        # else:
        #     session['logged_in'] = True
        #     session['username'] = username
        #     session['password'] = password

        #     flash('You were logged in')

        #     return redirect(url_for('home'))
    else:
        pass

    return render_template('forgot.html', error=error)

# Logout
@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)
    session.pop('password', None)
    flash('You were logged out')
    return redirect(url_for('home'))

# Return user profile
@app.route('/profile_img/<username>')
def profile_img(username):
    # send_static_file will guess the correct MIME type
    path = os.path.join('profile', username, 'profile.jpg')
    if not os.path.isfile(os.path.join('static', 'profile', 
                                        username, 'profile.jpg')):
        path = 'profile.jpg'
    return app.send_static_file(path)


# Return search results
@app.route('/search/<term>')
@login_required
def search(term):
    if g.user:
        per_page = 12
        profiles = []
        for profile in g.users.values():
            if re.search(term, profile['username'], re.IGNORECASE):
                profiles.append(profile)
                if len(profiles) == per_page:
                    break
        return render_template('results.html', profiles=profiles)
    else:
        return render_template('login.html')


# Render custom.css since it requires urls to static files
@app.route('/custom')
def custom_css():
    return Response(render_template('custom.css'), mimetype='text/css')
    
if __name__ == '__main__':
    app.debug = True
    app.run()