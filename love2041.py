# all the imports
import sqlite3, os, re, glob, smtplib, authenticate
from PIL import Image
from authenticate import generate_salt, generate_code, matched_code
from functools import wraps
from datetime import date
from flask import Flask, request, session, g, redirect, url_for, \
                 render_template, jsonify, Response
from werkzeug import secure_filename

# configuration
DATABASE = 'db/users.db'
DEBUG = True
SECRET_KEY = '\x98\x92Fn\xd3ko\xe3\x87We\x16\x01A}\xae\xaf1<"K-\x1a\xb9'
MAIL_FROM = "mail.geeklove@gmail.com"
MAIL_PASSWORD = "admingeek"
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])

app = Flask(__name__)
app.config.from_object(__name__)


# return age
def calcaulte_age(birthday):
    today = date.today()
    day, month, year = [int(num) for num in birthday.split('/')]
    return today.year - year - ((today.month, today.day) < (month, day))

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
    # for score %
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
                if data[key]:
                    data[key] = data[key].split('|')
                else:
                    data[key] = []
        # set up age
        self.age = calcaulte_age(self.birthday)



    # sugar test if field available
    def __contains__(self, key):
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
                msg = ('score += 2000  ','Gender preference match')
                breakdown.append(msg)

            if self.age_min <= user.age <= self.age_max:
                if self.pref_age:
                    score += 1200
                    msg = ('score += 1200  ','Age preference match')
                    breakdown.append(msg)
                else:
                    score += 1000
                    msg = ('score += 1200  ','Age rule half_plus_7 match')
                    breakdown.append(msg)
            elif user.age <= 14:
                breakdown.append(('score = 0     ','Age too young'))
                score = 0
            else:
                if user.age < self.age_min:
                    age_diff = self.age_min - user.age
                else:
                    age_diff = user.age - self.age_max
                age_diff_score = 1000 / (1.0 + (age_diff * 0.1))
                score += age_diff_score
                msg = ('score += %d' % age_diff_score,
                       'Age difference inverse calculation')
                breakdown.append(msg)

            if self.pref_weight and user.weight:
                if self.weight_min <= user.weight <= self.weight_max:
                    score += 300
                    msg = ('score += 300','Weight preference match')
                    breakdown.append(msg)

            if self.pref_height and user.height:
                if self.height_min <= user.height <= self.height_max:
                    score += 200
                    msg = ('score += 300','Height preference match')
                    breakdown.append(msg)

            if self.pref_hair and user.hair_colour:
                if user.hair_colour in self.hair_colours:
                    score += 100
                    msg = ('score += 100','Hair preference match')
                    breakdown.append(msg)

            if self.degree and self.degree == user.degree:
                score += 70
                breakdown.append(('score += 70','Degree match'))

            for key, rep in self.fields_msc_score:
                times = 0
                for value in self._data[key]:
                    if value and value in user._data[key]:
                        score += 20
                        times += 1
                if times == 1:
                    breakdown.append(('score += 20','%s match' % rep))
                elif times > 1:
                    msg = ('score += 20','%s match x %d' % (rep, times))
                    breakdown.append(msg)
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
        return users


# send an email to a user
def send_email(to_addr, subject, body):
    from_addr = app.config['MAIL_FROM']
    password =  app.config['MAIL_PASSWORD']
    server = 'smtp.gmail.com'
    port = 587
    session = smtplib.SMTP(server, port)        
    session.ehlo()
    session.starttls()
    session.login(from_addr, password)
    headers = [
        "From: " + from_addr,
        "Subject: " + subject,
        "To: " + to_addr,
        "MIME-Version: 1.0",
        "Content-Type: text/html"]
    headers = "\n".join(headers)
    session.sendmail(from_addr, [to_addr], headers + "\n\n" + body)
    session.quit()

# sqlite uses this function to construct user
def user_factory(cursor, row):
    data = {}
    for idx, col in enumerate(cursor.description):
        value = row[idx] if row[idx] else ''
        data[col[0]] = value
    return User(data)

# retrieve user from db matching username
def get_user(username):
    db = sqlite3.connect(app.config['DATABASE'])
    db.row_factory = user_factory
    query = "SELECT * FROM users WHERE username = ? COLLATE NOCASE"
    cur = db.execute(query, [username])
    user = cur.fetchone()
    return user

# retrieve user from db matching email
def get_user_by_email(email):
    db = sqlite3.connect(app.config['DATABASE'])
    db.row_factory = user_factory
    query = "SELECT * FROM users WHERE email = ? COLLATE NOCASE"
    cur = db.execute(query, [email])
    user = cur.fetchone()
    return user

# get all the current matches in order of score
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

# get user files relative to static folder
def get_user_files(username, pattern='*'):
    prevdir = os.getcwd()
    os.chdir('static')
    path = os.path.join('profile', username, pattern)
    files = glob.glob(path) or []
    os.chdir(prevdir)
    return files


def validate_fullname(fullname, error):
    if not fullname:
        error['fullname'] = 'You can\'t leave this empty.'


def validate_username(username, error):
    m = re.match(r'^[a-z0-9]{6,30}$', username, re.IGNORECASE)
    if not username:
        error['username'] = 'You can\'t leave this empty.'
    elif len(username) < 6 or len(username) > 30:
        error['username'] = 'Please use between 6 and 30 characters.'
    elif not m:
        error['username'] = 'Only letters and numbers allowed.'
    elif get_user(username):
        error['username'] = 'Username taken.'

def validate_password(password, error):
    if not password:
        error['password'] = 'You can\'t leave this empty.'
    elif len(password) < 8:
        error['password'] = 'Use at least 8 characters'


def validate_birthday(birthday, error):
    DMY_RE = r'^(0[1-9]|[12][0-9]|3[01])/(0[1-9]|1[012])/(\d\d\d\d)$'
    m = re.match(DMY_RE, birthday)
    if not birthday:
        error['birthday'] = 'You can\'t leave this empty.'
    elif not m:
        error['birthday'] = 'Please provide a valid date'
    else:
        age = calcaulte_age(birthday)
        if age < 0:
            error['birthday'] = 'Are you from the future?'
        elif age < 14:
            error['birthday'] = 'Go play outside you crazy kid.'
        elif age > 500:
            error['birthday'] = 'A wild pokemon has appeared o_O'
        elif age > 120:
            error['birthday'] = 'Turtles dont usually date.'


def validate_email(email, error):
    EMAIL_RE = r'^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,4}$'
    m = re.match(EMAIL_RE, email, re.IGNORECASE)
    if not email:
        error['email'] = 'You can\'t leave this empty.'
    elif not m:
        error['email'] = 'Please provide a valid email.'

def validate_gender(gender, error):
    if not gender:
        error['gender'] = 'Please select a gender.'



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


# return true if file has an allowed extension
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

# decorator getting the list of uploaded files
def file_loader(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        files = []
        if request.method == 'POST':
            # file_count = len(request.files)
            files = request.files.getlist("files") or []
            files = [f for f in files if allowed_file(f.filename)]
                    
        return func(files, *args, **kwargs)
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
def browse(page_num, msg_username=''):
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
                            prev_num=prev_num,
                            msg_username=msg_username)


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
        elif user.status == 'UNVERIFIED':
            error = 'Please verify your email first.'
        else:
            # set a new random token
            update_user(user, {'token':generate_salt()})
            session['logged_in'] = True
            session['username'] = username
            session['token'] = user.token
            return redirect(url_for('home'))
    return render_template('login.html', error=error)

# Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    error = {}
    verify = False
    if request.method == 'POST':
        # Validate form
        f = request.form

        fullname = f['fullname']
        validate_fullname(fullname, error)

        username = f['username']
        validate_username(username, error)

        password = f['password']
        validate_password(password, error)

        birthday = f['birthday']
        validate_birthday(birthday, error)

        email = f['email']
        validate_email(email, error)
        if get_user_by_email(email):
            error['email'] = 'Email address already registered.'

        gender = request.form.get('gender', '')
        validate_gender(gender, error)

        # Create account if all checks out :D!
        if not error:
            verify = True

            # Define the new account
            token = generate_salt() #random token used in verification
            account = {}
            account['status']       = 'UNVERIFIED'
            account['token']        = token
            account['password']     = generate_code(password)
            account['name']         = fullname
            account['email']        = email
            account['username']     = username
            account['gender']       = gender
            account['birthday']     = birthday
            account['pref_gender']  = 'Female' if gender == 'Male' else 'Male'          

            # Add account to db
            db = sqlite3.connect(app.config['DATABASE'])
            fields = account.keys()
            query = 'INSERT INTO users (' + ', '.join(fields) + ') VALUES (' 
            query += ', '.join([ '?' for i in range(len(fields))]) + ')'
            values = [account[field] for field in fields]
            db.execute(query, values)
            db.commit()
            db.close()

            # Send verification email
            subject = 'Confirm your Geek Love account'
            url = url_for('verify', username=username, token=token, _external=True)
            body = render_template('confirmEmail.html', account=account, url=url)
            send_email(email, subject, body)

    return render_template('register.html', error=error, verify=verify)

# Verify a users new account
@app.route('/verify/<username>/<token>')
def verify(username, token):
    user = get_user(username)
    if user and user.token == token:
        update_user(user, {'status':'ACTIVE'})
        return render_template('verify.html', user=user)
    else:
        return redirect(url_for('home'))


# Forgot Password
@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    error = {}
    sent = False
    if request.method == 'POST':
        # Validate form
        f = request.form

        email = f['email']
        validate_email(email, error)

        user = get_user_by_email(email)
        if not user:
            error['email'] = 'No user registered with this email.'

        # Send email with unique link
        if not error:
            token = generate_salt()
            update_user(user, {'token':token})            
            username = user.username
            email = user.email

            # Send verification email
            subject = 'Password reset for Geek Love account'
            url = url_for('reset', username=username, token=token, _external=True)
            body = render_template('resetEmail.html', account=user, url=url)
            send_email(email, subject, body)
            sent = True

    return render_template('forgot.html', error=error, sent=sent)


#TODO ------ ------ ------ ------ ------ ------ ------ ------ ------ ------ ------ ------ ------ ------ ------ ------ ------ ------ ------ ------ ------ ------

# Reset a users password
@app.route('/reset/<username>/<token>', methods=['GET', 'POST'])
def reset(username, token):
    user = get_user(username)
    if user and user.token == token:
        error = {}
        changed = False
        if request.method == 'POST':
            # Validate form
            f = request.form
            password = f['password']
            validate_password(password, error)

            if not error:
                password = generate_code(password)
                update_user(user, {'password': password})
                changed = True

        return render_template('reset.html', user=user, error=error, changed=changed)
    else:
        return redirect(url_for('home'))


# Logout
@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)
    session.pop('token', None)
    return redirect(url_for('home'))


# Return search results
@app.route('/search/<term>')
@login_required
def search(term):
    per_page = 12
    profiles = []
    matches = get_matches()
    for profile in matches:
        if re.search(term, profile.username, re.IGNORECASE):
            profiles.append(profile)
            if len(profiles) == per_page:
                break
    return render_template('results.html', profiles=profiles)

    

# Return user profile
@app.route('/profile_img/<username>')
def profile_img(username):
    # send_static_file will guess the correct MIME type
    prevdir = os.getcwd()
    os.chdir('static')
    
    path = os.path.join('profile', username, 'profile.jpg')
    if not os.path.isfile(path):
        path = 'profile.jpg'
    os.chdir(prevdir)
    return app.send_static_file(path)


# quote
#     <i>Italic</i>, <b>Bold</b> and <u>Underline</u> supported.

# Return inner html for profile
@app.route('/profile/<username>')
@login_required
def profile(username):
    profile = get_user(username)
    if profile:
        # masonary layout works best with longest columns
        # being layed out first, so sort all the favourites by length
        favs = [ 
            {'title': 'Favourite bands',    'data': profile.favourite_bands},
            {'title': 'Favourite movies',   'data': profile.favourite_movies},
            {'title': 'Favourite TV shows', 'data': profile.favourite_TV_shows},
            {'title': 'Favourite books',    'data': profile.favourite_books},
            {'title': 'Favourite hobbies',  'data': profile.favourite_hobbies}
        ]
        favs = sorted(favs, key=lambda fav: len(fav['data']), reverse=True)

        # score user
        g.user.setup_prefs()
        g.user.score_user(profile)

        return render_template('profile.html', profile=profile, favs=favs)
    else:
        redirect(url_for('home'))


@app.route('/msg/<username>', methods=["GET","POST"])
@login_required
def open_profile(username):
    return browse(page_num=1, msg_username=username)

@app.route('/msg_user', methods=["GET","POST"])
@login_required
def msg_user():
    if request.method == 'POST':
        recipient = request.form['recipient']        
        msg = request.form['msg']
        user = get_user(recipient)
        if user:
            email = user.email
            subject = 'Geek Love new message!'
            url =  url_for('open_profile', username=g.user.username, _external=True)

            body = render_template('msgEmail.html', from_user = g.user, to_user=user, url=url, msg=msg)
            send_email(email, subject, body)

    return '<em>message sent</em>'




# Return inner html for profile photos
@app.route('/photos/<username>')
@login_required
def photos(username):

    prevdir = os.getcwd()
    os.chdir('static')
    path = os.path.join('profile', username, 'photo*.jpg')
    urls = [ url_for('static', filename=filename ) for filename in glob.glob(path)]
    os.chdir(prevdir)
    return render_template('photos.html', urls=urls)

# Resize images to be square 250x250
def resize_image(filename):
    img = Image.open(filename)
    width, height = img.size

    if width > height:
       diff = width - height
       left = int(diff/2)
       upper = 0
       right = height + left
       lower = height
    else:
       diff = height - width
       left = 0
       upper = int(diff/2)
       right = width
       lower = width + upper

    img = img.crop((left, upper, right, lower))
    img.thumbnail(250, Image.ANTIALIAS)
    img.save(filename)



# Return inner html for potentially added photos
@app.route('/upload_photos', methods=["GET","POST"])
@login_required
@file_loader
def upload_photos(files):
    for file in files:
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    return 'hello'


# Return inner html for potentially added profile picture
@app.route('/upload_profile_pic', methods=["GET","POST"])
@login_required
@file_loader
def upload_profile_pic(files):
    for file in files:
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    return 'hello'



    


# # Return inner html for potentially added photos
# @app.route('/upload_photos', methods=["GET","POST"])
# @login_required
# def upload_photos(files):
#     if request.method == 'POST':
        
#         print 'what what', len(request.files)
#         uploaded_files = request.files.getlist("files")

#         for pic in uploaded_files:
#             print pic.filename
#         # file = request.files['0'];
#         # file = request.files['file']

#         # if file: #and allowed_file(file.filename):
#         #     print file
#         #     filename = secure_filename(file.filename)
#         #     file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
#     #         return redirect(url_for('uploaded_file',
#     #                                 filename=filename))


#     # uploaded_files = request.files.getlist("files")
#     # print 'gettting files'
#     # print uploaded_files

#     return '<b>hello</b>'


#     # return render_template('my_photos.html', urls=urls)

# load fields as html forms
@app.route('/aboutme/load/<kind>', methods=["GET","POST"])
@login_required
def aboutme_load(kind):
    if kind == 'skeleton':
        # Structure of the modal
        return render_template('meSkeleton.html', me=g.user)
    elif kind == 'head':
        # Head of the modal
        return render_template('meHead.html', me=g.user, error={})

    elif kind == 'about':
        # about tab contents
        favs = [ 
            {'title': 'Favourite bands',    'data': g.user.favourite_bands,     'name': 'favourite_bands'},
            {'title': 'Favourite movies',   'data': g.user.favourite_movies,    'name': 'favourite_movies'},
            {'title': 'Favourite TV shows', 'data': g.user.favourite_TV_shows,  'name': 'favourite_TV_shows'},
            {'title': 'Favourite books',    'data': g.user.favourite_books,     'name': 'favourite_books'},
            {'title': 'Favourite hobbies',  'data': g.user.favourite_hobbies,   'name': 'favourite_hobbies'},
        ]
        favs = sorted(favs, key=lambda fav: len(fav['data']), reverse=True)

        return render_template('meAbout.html', me=g.user, error={}, favs=favs)

    elif kind == 'photos':
        # photos tab contents
        files = get_user_files(g.user.username, 'photo*.jpg')

        urls = [ url_for('static', filename=filename ) for filename in files]

        return render_template('mePhotos.html', urls=urls)

    elif kind == 'preferences':
        # preferences tab contents
        return render_template('mePreferences.html', me=g.user, error={})
    else:
        return '<b>helloow</b>'


# Check fields and return html with error messages if required
@app.route('/aboutme/check/<kind>', methods=["GET","POST"])
@login_required
def about_me_check(kind):
    pass


# save fields, updating current user
@app.route('/aboutme/save/<kind>', methods=["GET","POST"])
@login_required
def about_me_load(kind):
    pass




if __name__ == '__main__':
    app.debug = True
    app.run()