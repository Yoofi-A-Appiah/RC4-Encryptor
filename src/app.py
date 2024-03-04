import base64
from datetime import timedelta
from flask import Flask, Response, g, redirect, request, jsonify, send_file, url_for
import os
from flask_jwt_extended import jwt_required, get_jwt_identity, JWTManager, create_access_token, verify_jwt_in_request

from src.config.dbconnect import initialize_db
from src.models.user_models import User_Model
from dotenv import load_dotenv
    
load_dotenv()

app = Flask(__name__)



jwt_secret = os.getenv("JWTSECRET")

mongo_uri = os.getenv("MONGODB_URI")

app.config["MONGO_URI"] = mongo_uri

initialize_db(app)

jwt = JWTManager(app)

app.config['JWT_SECRET_KEY'] = jwt_secret

app.config[3600] = timedelta(hours=1)

user_model = User_Model()

@app.route('/signup', methods=['POST'])
def signup():
    username = request.form.get('username')
    password = request.form.get('password')
    return user_model.signup(username,password)

# Login endpoint
@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    return user_model.login(username,password)

@app.route('/logout', methods=['GET'])
def logout():
    response = Response()
    # Clear the authentication token from the client's browser
    response.delete_cookie('access_token_cookie')
    return response


@app.before_request
def check_login_status():
    g.logged_in = False  # Initialize logged_in as False by default
    g.is_admin = False   # Initialize is_admin as False by default

    if 'access_token_cookie' in request.cookies:
        try:
            verify_jwt_in_request(locations=['cookies'])
            g.logged_in = True
            current_user = get_jwt_identity()
            if current_user == "admin":
                g.is_admin = True
        except Exception as e:
            print(f"JWT Verification Error: {e}")


# Function to initialize the RC4 state with a given key
def init_rc4(key):
    # Decode key bytes to string
    key_str = key.decode('utf-8')
    
    # Encode key string to ASCII representation
    key_ascii = [ord(char) for char in key_str]
    
    S = list(range(256))
    j = 0
    for i in range(256):
        j = (j + S[i] + key_ascii[i % len(key)]) % 256
        S[i], S[j] = S[j], S[i]
    return S



# Function to encrypt plaintext using RC4
def encrypt_file(filename, content, key):
    print("setting key")
    S = init_rc4(key)
    i = 0
    j = 0
    ciphertext = bytearray()
    for char in content:
        i = (i + 1) % 256
        j = (j + S[i]) % 256
        S[i], S[j] = S[j], S[i]
        k = S[(S[i] + S[j]) % 256]
        ciphertext.append(char ^ k)
    encrypted_filename = filename + '.enc'
    with open(encrypted_filename, 'wb' ) as f:
        f.write(ciphertext)
    return ciphertext, encrypted_filename

# Function to decrypt ciphertext using RC4
def decrypt_file(filename, content, key):
    S = init_rc4(key)
    i = 0
    j = 0
    plaintext = bytearray()
    for char in content:
        i = (i + 1) % 256
        j = (j + S[i]) % 256
        S[i], S[j] = S[j], S[i]
        k = S[(S[i] + S[j]) % 256]
        plaintext.append(char ^ k)
    decrypted_filename = filename.replace('.enc', '')
    with open(decrypted_filename, 'wb' ) as f:
        f.write(plaintext)
    return plaintext, decrypted_filename

from flask import send_file, make_response, jsonify

from flask import send_file, make_response

@app.route('/encrypt-file', methods=['POST'])
def encrypt_file_route():
    print('Encrypt file')
    file = request.files['file']
    key = request.form['key']
    filename = file.filename
    file_content = file.read()
    encrypted_content, encrypted_filename = encrypt_file(filename, file_content, key.encode())
    response = make_response(send_file(encrypted_filename, as_attachment=True))
    response.headers['Content-Disposition'] = f'attachment; filename="{encrypted_filename}"'
    response.headers['Content-Type'] = 'application/octet-stream'
    #os.remove(filename)
    return response,200

@app.route('/decrypt-file', methods=['POST'])
def decrypt_file_route():
    file = request.files['file']
    key = request.form['key']
    filename = file.filename
    file_content = file.read()
    decrypted_content, decrypted_filename = decrypt_file(filename, file_content, key.encode())
    response = make_response(send_file(decrypted_filename, as_attachment=True))
    #os.remove(filename)
    response.status_code = 200
    return response



if __name__ == '__main__':

    app.run(debug=True)
