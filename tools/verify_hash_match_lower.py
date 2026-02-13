import hashlib

password = "rodolfo"
salt = "3544fb4f07bb455c9ccd717e8b96a6bb"
expected_hash = "79e071d9d17e71119b339b1a367b2f8828a34186453d507c6e8c61d7d5fedd7d"

dk = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
actual_hash = dk.hex()

print(f"Password: {password}")
print(f"Hash Match: {actual_hash == expected_hash}")
