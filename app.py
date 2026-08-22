from decimal import Decimal
from flask import Flask, jsonify, request, session
from flask_cors import CORS
from entities import Fund, User
from db_tools import DBHandler
from markupsafe import escape

app = Flask(__name__)
CORS(app)
DBHandler.init_db()
#TODO: add login required wrapper before hosting!!!
@app.route("/users/api/allids", methods=['GET'])
def get_all_user_ids():
	ids = DBHandler.getAllUserIDs()
	return jsonify(ids)

@app.route("/users/api/allrefs", methods=['GET'])
def get_all_user_refs():
	refs = DBHandler.getAllUserRefs()
	return jsonify(refs)

