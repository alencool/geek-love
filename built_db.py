import os,re, sqlite3

def get_immediate_subdirectories(a_dir):
    return [name for name in os.listdir(a_dir)
            if os.path.isdir(os.path.join(a_dir, name))]

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


    account['status'] = 'ACTIVE';
    accounts.append(account)

#create database
db = sqlite3.connect('db/users.db')

# drop old table
db.execute('drop table if exists users')

# Create table
db.execute('''create table users (
    id   INTEGER PRIMARY KEY,
    status              TEXT,
    name                TEXT,
    password            TEXT,
    courses             TEXT,
    email               TEXT,
    username            TEXT,
    height              REAL,
    gender              TEXT,
    favourite_bands     TEXT,
    favourite_movies    TEXT,
    favourite_TV_shows  TEXT,
    degree              TEXT,
    favourite_books     TEXT,
    favourite_hobbies   TEXT,
    hair_colour         TEXT,
    weight              REAL,
    birthdate           TEXT, 
    hair_colours        TEXT,
    pref_gender         TEXT,
    age_min             INTEGER,
    age_max             INTEGER,
    height_min          REAL,
    height_max          REAL,
    weight_min          REAL,
    weight_max          REAL)''')


# Insert a accounts
for a in accounts:
    fields = a.keys()
    query = 'INSERT INTO users (' + ', '.join(fields) + ') VALUES (' 
    query += ', '.join([ '?' for i in range(len(fields))]) + ')'
    values = [a[field] for field in fields]
    db.execute(query, values)

# Save (commit) the changes
db.commit()
db.close()
