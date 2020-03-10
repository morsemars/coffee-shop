import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS, cross_origin
import sys

from .database.models import db_drop_and_create_all, setup_db, Drink, db
from .auth.auth import AuthError, requires_auth

print(Flask)

app = Flask(__name__)
setup_db(app)

CORS(app,resources={r"/*": {"origins": "http://localhost:8100"}})
  
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,PATCH,DELETE,OPTIONS')
    return response

'''
@TODO uncomment the following line to initialize the datbase
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
'''
#db_drop_and_create_all()

## ROUTES
@app.route('/drinks')
def get_drinks():

    drinks = Drink.query.all()

    return jsonify({
        "success": True,
        "drinks": [drink.short() for drink in drinks]
    })

@app.route('/drinks-detail')
@cross_origin()
@requires_auth('get:drinks-detail')
def get_drinks_detail(jwt):
    drinks = Drink.query.all()

    return jsonify({
        "success": True,
        "drinks": [drink.long() for drink in drinks]
    })

@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def add_drink(jwt):
    
    data = request.get_json()

    newDrink = Drink(
       title = data.get("title"),
       recipe = json.dumps(data.get("recipe"))
    )

    isSuccessful = True

    try:
        newID = newDrink.insert()
    except:
        db.session.rollback()
        isSuccessful = False
    finally:
        if isSuccessful:
            return jsonify({
                "success": isSuccessful,
                "drinks": [newDrink.long()]
            })
        else:
            abort(422)

@app.route('/drinks/<id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def update_drink(jwt, id):
    
    data = request.get_json()
    drink = Drink.query.filter_by(id=id).one_or_none()

    if drink is None:
        abort(404)

    drink.title = data.get("title")
    drink.recipe = json.dumps(data.get("recipe"))

    isSuccessful = True

    try:
        drink.update()
    except:
        db.session.rollback()
        isSuccessful = False
    finally:

        if isSuccessful:
            return jsonify({
                "success": True,
                "drinks": [drink.long()]
            })
        else:
            abort(422)
    
    return jsonify({
        "success": True,
        "drinks": []
    })

@app.route('/drinks/<id>', methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drink(jwt, id):
   
    drink = Drink.query.filter_by(id=id).one_or_none()

    if drink is None:
        abort(404)

    isSuccessful = True

    try:
        drink.delete()
    except:
        db.session.rollback()
        isSuccessful = False
    finally:

        if isSuccessful:
            return jsonify({
                "success": True,
                "delete": id
            })
        else:
            abort(422)


## Error Handling
'''
Example error handling for unprocessable entity
'''
@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
                    "success": False, 
                    "error": 422,
                    "message": "unprocessable"
                    }), 422

@app.errorhandler(404)
def page_not_found(error):
    return jsonify({
                    "success": False, 
                    "error": 404,
                    "message": "resource not found"
                    }), 404

@app.errorhandler(AuthError)
def missing_permissions(error):
    print(error.error, error.status_code)
    return jsonify({
                    "success": False, 
                    "error": error.status_code,
                    "message": error.error['description']
                    }), error.status_code