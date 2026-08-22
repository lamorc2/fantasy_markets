
from werkzeug.security import check_password_hash, generate_password_hash



def hash_pw(pw):
    return generate_password_hash(str(pw or ''),method='pbkdf2')

def check_pw(pw, stored):
    if not stored:
        return False
    stored = str(stored)
    if stored.startswith(('pbkdf2:', 'scrypt:', 'argon2:')):
        return check_password_hash(stored, pw or '')
    return hashlib.sha256((pw or '').encode()).hexdigest() == stored
