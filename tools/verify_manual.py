import hashlib

def verify(password, salt, stored_hash):
    dk = hashlib.pbkdf2_hmac(
        'sha256', 
        password.encode('utf-8'), 
        salt.encode('utf-8'), 
        100_000
    )
    return dk.hex() == stored_hash

salt = "f7ffca0a55d5a6e846946d51445aa2cd"
stored = "7dddd38c28209301975a76569a935498b2619969a391ecf6361e3183638f957a"

print(f"Testing 'RODOLFO': {verify('RODOLFO', salt, stored)}")
print(f"Testing 'rodolfo': {verify('rodolfo', salt, stored)}")
