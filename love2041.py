# all the imports
import sqlite3, os, re, authenticate
from authenticate import generate_salt, generate_code, matched_code
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


# Abstract view of a user
class User(object):
    fields_to_split = ['courses', 'favourite_bands', 'favourite_movies',
                       'favourite_TV_shows', 'favourite_books', 
                       'favourite_hobbies', 'hair_colours']
    fields_msc_score = [['favourite_bands',     'Favourite band'],
                        ['favourite_movies',    'Favourite movie'],
                        ['favourite_TV_shows',  'Favourite TV show'],
                        ['favourite_books',     'Favourite book'],
                        ['favourite_hobbies',   'Favourite hobby'],
                        ['courses',             'Course']]
    colours =  ['rgb(230,  40, 40)', # 10 
                'rgb(230,  50, 40)', # 20 
                'rgb(235,  65, 35)', # 30 
                'rgb(245, 130, 40)', # 40 
                'rgb(250, 160, 40)', # 50 
                'rgb(255, 210, 45)', # 60 
                'rgb(250, 230, 40)', # 70 
                'rgb(215, 225, 50)', # 80 
                'rgb(170, 200, 40)', # 90 
                'rgb(150, 180, 40)'] #100 

    def __init__(self, data):
        self._data = data
        for key in data:
            if key in self.fields_to_split:
                data[key] = data[key].split('|')

        # set up age
        today = date.today()
        year, month, day = [int(num) for num in self.birthdate.split('/')]
        self.age = today.year - year - ((today.month, today.day) < (month, day))


    # sugar test if field available
    def __contains__(self, key):
        print key
        return (key in self._data)

    # sugar to get a field
    def __getattr__(self, key):
        if key == '_data':
            return object.__getattr__(self, key)
        elif key in self._data:
            return self._data[key]
        else:
            return ''

    def __cmp__(self, user):
        if not user or user.score < self.score:
            return -1
        elif self.score > user.score:
            return 1
        else:
            return 0

    # sugar to set a field 
    def __setattr__(self, key, value):
        if key in getattr(self,'_data', []):
            self._data[key] = value
        else:
            object.__setattr__(self, key, value)

    # setup our user preferences
    def setup_prefs(self):
        # set if we have a prefered age
        self.pref_age = True if self.age_min or self.age_max else False
        
        if not self.age_min:
            if self.age > 14:
                self.age_min = (self.age / 2) + 7 
            else:
                self.age_min = self.age

        if not self.age_max:
            if self.age > 14:
                self.age_max = (self.age - 7) * 2
            else:
                self.age_max = self.age

        self.age_avg = (self.age_max + self.age_min)/2

        # set if we have a prefered weight
        if self.weight_min or self.weight_max:
            self.pref_weight = True 
            self.weight_min = self.weight_min or 0
            self.weight_max = self.weight_max or 1000
        else:
            self.pref_weight = False

        # set if we have a prefered height
        if self.height_min or self.height_max:
            self.pref_height = True
            self.height_min = self.height_min or 0
            self.height_max = self.height_max or 10
        else:
            self.pref_height = False

        # set if we have prefered hair colours
        self.pref_hair = True if self.hair_colours else False


    def score_user(self, user):
            score = 0
            breakdown = []  # list of breakdown messages

            if self.pref_gender == user.gender:
                score += 2000
                msg = 'score += 2000  *Gender preference match'
                breakdown.append(msg)

            if self.age_min <= user.age <= self.age_max:
                if self.pref_age:
                    score += 1200
                    msg = 'score += 1200  *Age preference match'
                    breakdown.append(msg)
                else:
                    score += 1000
                    msg = 'score += 1200  *Age rule half_plus_7 match'
                    breakdown.append(msg)
            elif user.age <= 14:
                breakdown.append('score = 0  *Age too young')
                score = 0
            else:
                if user.age < self.age_min:
                    age_diff = self.age_min - user.age
                else:
                    age_diff = user.age - self.age_max
                age_diff_score = 1000 / (1.0 + (age_diff * 0.1))
                score += age_diff_score
                msg = 'score += %d  *Age difference inverse calculation'
                breakdown.append(msg % age_diff_score)

            if self.pref_weight and user.weight:
                if self.weight_min <= user.weight <= self.weight_max:
                    score += 300
                    msg = 'score += 300  *Weight preference match'
                    breakdown.append(msg)

            if self.pref_height and user.height:
                if self.height_min <= user.height <= self.height_max:
                    score += 200
                    msg = 'score += 300  *Height preference match'
                    breakdown.append(msg)

            if self.pref_hair and user.hair_colour:
                if user.hair_colour in self.hair_colours:
                    score += 100
                    msg = 'score += 100  *Hair preference match'
                    breakdown.append(msg)

            if self.degree and self.degree == user.degree:
                score += 70
                breakdown.append('score += 70  *Degree match')

            for key, rep in self.fields_msc_score:
                for value in self._data[key]:
                    times = 0
                    if value and value in user._data[key]:
                        score += 20
                        times += 1
                    if times == 1:
                        breakdown.append('score += 20  *%s match' % rep)
                    elif times > 1:
                        msg = 'score += 20  *%s match x %d'
                        breakdown.append(msg % rep, times)
            user.breakdown = breakdown
            user.score = int(score)


    # returns a list of users ordered by score
    def sort_by_score(self, users=[]) :
        if users:
            total = 0
            self.setup_prefs()

            # calculate scores for each user
            for user in users:
                self.score_user(user)
                total += user.score

            # sort by score
            users = sorted(users)
            
            # calculate scaled scores for each user
            self.top_score = users[0].score
            for user in users:
                user.scaled_score = int((user.score * 1.0
                                        /self.top_score)*100)
                colour_index = int((user.scaled_score - 0.1)/10)
                user.colour = self.colours[colour_index]
                print user.score, user.scaled_score, user.colour
        return users

# sqlite uses this function to construct user
def user_factory(cursor, row):
    data = {}
    for idx, col in enumerate(cursor.description):
        value = row[idx] if row[idx] else ''
        data[col[0]] = value
    return User(data)

# retrieve user from db
def get_user(username):
    db = sqlite3.connect(app.config['DATABASE'])
    db.row_factory = user_factory
    query = "SELECT * FROM users WHERE username = ? COLLATE NOCASE"
    cur = db.execute(query, [username])
    user = cur.fetchone()
    return user

def get_matches():
    db = sqlite3.connect(app.config['DATABASE'])
    db.row_factory = user_factory

    # construct dictionary of users
    query = 'SELECT * FROM users WHERE status = ? AND id != ?'
    cur = db.execute(query, ['ACTIVE', g.user.id])
    users = cur.fetchall()
    if users:
        users = g.user.sort_by_score(users)
    return users


# decorator to enfore session requirement
def login_required(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        g.user = None
        if session.get('logged_in'):
            username = session.get('username').lower()
            token = session.get('token')
            user = get_user(username)
            if user and user.token == token:
                g.user = user
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
    matches = get_matches()
    
    per_page = 12
    end = per_page * page_num       #slice start
    start = end - per_page          #slice end
    profiles = matches[start:end]
    
    num_users = len(matches)
    num_pages = num_users/per_page

    next_num = page_num+1 if per_page * page_num < num_users else 0
    prev_num = page_num-1 if page_num > 1 else 0

    return render_template('browse.html', 
                            profiles=profiles, 
                            next_num=next_num, 
                            prev_num=prev_num)


# takes a user dict and fields dict then updates db and user dict
def update_user(user, data):
    db = sqlite3.connect(app.config['DATABASE'])
    fields = data.keys()
    values = [data[key] for key in fields]
    values.append(user.id)
    query = ', '.join([ field + ' = ?' for field in fields])
    query = 'UPDATE users SET ' + query + ' WHERE id = ?'
    db.execute(query, values)
    db.commit()
    db.close()
    for key in data:
        user._data[key] = data[key]

# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username'].lower()
        password = request.form['password']
        user = get_user(username)
        if not user:
            error = 'Invalid username or password'
        elif not matched_code(password, user.password):
            error = 'Invalid password or password'
        else:
            # set a new random token
            update_user(user, {'token':generate_salt()})
            session['logged_in'] = True
            session['username'] = username
            session['token'] = user.token
            return redirect(url_for('home'))
    return render_template('login.html', error=error)

#TODO
# Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    if request.method == 'POST':
        pass
    else:
        pass

    return render_template('register.html', error=error)

#TODO
# Reset Password
@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    error = None
    if request.method == 'POST':
        pass
    else:
        pass

    return render_template('forgot.html', error=error)

# Logout
@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)
    session.pop('token', None)
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
        matches = get_matches()
        for profile in matches:
            if re.search(term, profile.username, re.IGNORECASE):
                profiles.append(profile)
                if len(profiles) == per_page:
                    break
        return render_template('results.html', profiles=profiles)
    else:
        return render_template('login.html')
    
if __name__ == '__main__':
    app.debug = True
    app.run()