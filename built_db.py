#
#  built_db.py
#  Script to scrape data from provide profiles and generate a database.
#  Also tries to deal with erroneous data.
#
#  Created by Alen Bou-Haidar on 17/10/14, edited 25/10/14
#

import os,re, sqlite3, authenticate

DMY_RE = r'^(0[1-9]|[12][0-9]|3[01])/(0[1-9]|1[012])/((19|20)\d\d)$'
YMD_RE = r'^((19|20)\d\d)/(0[1-9]|1[012])/(0[1-9]|[12][0-9]|3[01])$'


# return a standardised date in YMD format
def standardise_birthdate(birthdate):
    # check if birthdate doesnt match standard format already
    
    m = re.match(DMY_RE, birthdate)
    if not m:
        m = re.match(YMD_RE, birthdate)
        if m:
            # birthdate is in YMD format
            year, month, day  = m.group(1), m.group(3), m.group(4)
        else:
            # non valid birthdate, set default
            day, month, year = '01', '01', '1914'
        birthdate = day + '/' + month + '/' + year
    return birthdate

# return a list of immediate subdirectories
def get_immediate_subdirectories(a_dir):
    return [name for name in os.listdir(a_dir)
            if os.path.isdir(os.path.join(a_dir, name))]

# set up path and users list
path = os.path.dirname(os.path.realpath(__file__))
path = os.path.join(path, 'static', 'profile')
users = get_immediate_subdirectories(path)


accounts = []       # all 380 user accounts
for user in users:
    profile_path = os.path.join(path, user, 'profile.txt')
    preference_path = os.path.join(path, user, 'preferences.txt')

    category = ''   # outer category name
    field = ''      # field name
    account = {}

    for filename in (preference_path, profile_path):

        # find all fields inside preferences
        with open(filename) as F:
            for line in F:
                m = re.match(r'^\t*(\w+):$', line)
                if m and m.group(1).lower() in ('min', 'max'):
                    field = category + '_' + m.group(1).lower()
                elif m:
                    category = m.group(1).lower()
                    field = category
                    if (filename == preference_path) and \
                       (field == 'gender'):
                       field = 'pref_gender';
                else:
                    if category in ('height', 'weight'):
                        line = line.replace('kg', '').replace('m', '')
                    if field in account:
                        account[field] += "|" + line.strip()
                    else:
                        account[field] = line.strip()

    # attempt to fix weird birthdates
    account['birthday'] = standardise_birthdate(account['birthdate'])
    del account['birthdate']

    # code password for security
    account['password'] = authenticate.generate_code(account['password'])

    # for convenience capitilize genders
    if 'pref_gender' in account:
        account['pref_gender'] = account['pref_gender'].capitalize()
    account['gender'] = account['gender'].capitalize()

    # user is obviously active
    account['status'] = 'ACTIVE';
    accounts.append(account)

#create database
db = sqlite3.connect('db/users.db')

# drop old table
db.execute('drop table if exists users')

# Create table
db.execute('''create table users (
    id   INTEGER PRIMARY KEY,
    token              TEXT,
    status              TEXT,
    password            TEXT,
    name                TEXT,
    courses             TEXT,
    email               TEXT,
    username            TEXT,
    quote               TEXT,
    height              REAL,
    gender              TEXT,
    degree              TEXT,
    favourite_bands     TEXT,
    favourite_movies    TEXT,
    favourite_TV_shows  TEXT,
    favourite_books     TEXT,
    favourite_hobbies   TEXT,
    hair_colour         TEXT,
    weight              REAL,
    birthday            TEXT, 
    hair_colours        TEXT,
    pref_gender         TEXT,
    age_min             INTEGER,
    age_max             INTEGER,
    height_min          REAL,
    height_max          REAL,
    weight_min          REAL,
    weight_max          REAL)''')

# Insert accounts
for account in accounts:
    fields = account.keys()
    query = 'INSERT INTO users (' + ', '.join(fields) + ') VALUES (' 
    query += ', '.join([ '?' for i in range(len(fields))]) + ')'
    values = [account[field] for field in fields]
    db.execute(query, values)

# Save (commit) the changes
db.commit()
db.close()
