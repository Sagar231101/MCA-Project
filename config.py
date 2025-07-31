# import secrets
# print(secrets.token_hex(32))

# from werkzeug.security import generate_password_hash
# print(generate_password_hash('your_new_admin_password'))
# Example output: pbkdf2:sha256:150000$xxxxxx$yyyyyy
from werkzeug.security import generate_password_hash
my_password = 'superadminpass' # Use the password for your superadmin account
hashed_password = generate_password_hash(my_password)
print(hashed_password)