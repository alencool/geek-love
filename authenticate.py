#
#  authenticate.py
#  Some useful code generating and checking functions used in 
#  authentication of passwords.
#
#  Created by Alen Bou-Haidar on 15/10/14, edited 15/10/14
#

import uuid
import hashlib

# generate a random number identifier
def generate_salt():
    return uuid.uuid4().hex

# take plain string, and optional salt and generate a secure code
def generate_code(plain, salt=None):
    if not salt: salt = generate_salt()
    hashed = hashlib.sha256(salt.encode() + plain.encode()).hexdigest()
    return  hashed + ':' + salt

# returns true if we can match plain text to a code
def matched_code(plain, code):
    hashed, salt = code.split(':')
    return code == generate_code(plain, salt)