from datetime import datetime
import random
from bson import ObjectId, json_util
from flask import Response, jsonify, make_response, redirect, url_for
from flask_jwt_extended import create_access_token
from ..config.dbconnect import mongo
from bson.errors import InvalidId
from werkzeug.security import generate_password_hash, check_password_hash


class User_Model:
    def __init__(self):
        self.mongo = mongo
    
    def signup(self,username,password):
        users_collection = mongo.db.users
    
        if users_collection.find_one({'username': username}):
            return jsonify({'message': 'Username already exists'}), 400

        hashed_password = generate_password_hash(password)
        users_collection.insert_one({'username': username, 'password': hashed_password})
        return jsonify({'message': 'User registered successfully'}), 201
    
    def login(self, username, password):
        users_collection = mongo.db.users
        user = users_collection.find_one({'username': username})
        
        if user and check_password_hash(user['password'], password):
            # Create JWT token or session token
            access_token = create_access_token(identity=username)
            response = jsonify({'access_token': access_token})
            response.status_code = 200
            return response
        else:
            return jsonify({'message': 'Invalid credentials'}), 401