from decimal import Decimal
from flask import Flask, jsonify, request, session
from flask_cors import CORS
from entities import Fund, User
from db_tools import DBHandler
from markupsafe import escape
import json
import os
from auth_helpers import check_pw, hash_pw
from functools import wraps
from api import MassiveAPI
app = Flask(__name__)
app.secret_key = os.environ.get('APP_SECRET_KEY') or b'_5#y2L"F4Q8z\n\xec]/'
CORS(app)
DBHandler.init_db()
#TODO: add login required wrapper before hosting!!!
DEBUG_MODE = app.secret_key == b'_5#y2L"F4Q8z\n\xec]/'
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if DEBUG_MODE:
            return f(*args, **kwargs)
        if 'user_id' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated



@app.route("/users/api/get/<int:user_id>", methods=['GET'])
@login_required
def load_user(user_id: int):
	return jsonify(dict(DBHandler.getUser(user_id)))


@app.route("/users/api/allids", methods=['GET'])
@login_required
def get_all_user_ids():
	ids = DBHandler.getAllUserIDs()
	return jsonify(ids)
	#TODO: disable before hosting


@app.route("/users/api/get/allrefs", methods=['GET'])
@login_required
def get_all_user_refs():
	refs = DBHandler.getAllUserRefs()
	return jsonify(refs)

@app.route("/trades/api/<ticker>/buy", methods=['POST'])
@login_required
def buy_ticker(ticker):
	request_data = request.get_json()
	if not request_data:
		return 400
	fund_id = request_data.get("fund_id",None)
	user_id = session["user_id"]
	league_id = request_data.get("league_id",None)
	shares_float = request_data.get("shares", None)
	price_float = request_data.get("shares", None)
	if not user_id or not league_id or not shares_float:
		return jsonify({'success':False}),400
	if not DBHandler.isFund(fund_id):
		#TODO: add error return body
		return jsonify({'success':False}),404

	shares = Decimal(str(shares_float))
	price = Decimal(str(price_float))
	try:
		Fund.buyTickerByShares(fund_id=fund_id,user_id=user_id,ticker=ticker,amnt=shares,price=price)
	except Exception:
		return jsonify({'success':False}), 500

@app.route("/tickers/api/get/<ticker>", methods=["GET"])
@login_required
def get_ticker_price(ticker):
	try:
		price = MassiveAPI.getSharePrice(ticker)
	except ValueError:
		return jsonify({'success':False, 'message': "Ticker Not Found"}), 404
	except Exception:
		return jsonify({'success':False}), 500
	return jsonify({'success':True,'ticker':ticker,'price':price}), 200


@app.route("/users/api/login", methods=['POST'])
@app.route("/leagues/api/login", methods=['POST'])
def login():
	request_data = request.get_json()
	if not request_data:
		return 400
	password = request_data.get("password", None)
	username = request_data.get("username", None)
	if not password or not username:
		return 400

	user_dict = DBHandler.getLoginUserByUsername(username)
	user = User.buildUserFromDict(user_dict)
	if not check_pw(password, user.password_hash):
		return 401
	session["user_id"] = user.id
	session["username"] = username
	if DEBUG_MODE:
		return jsonify({'success':True,"id":user.id}), 202
	return 202

@app.route('/api/logout', methods=['POST'])
def api_logout():
	session.clear()
	return jsonify({'success':True}), 200


@app.route("/users/api/post/createUser", methods=["POST"])
def addUser():
	request_data = request.get_json()
	if not request_data:
		return jsonify({'success':False}), 400
	username = request_data.get("username", None)
	display_name = request_data.get("display_name", None)
	email = request_data.get("email", None)
	password = request_data.get("password", None)
	if not username or not display_name or not email or not password:
		return jsonify({'success':False}), 400
	try:
		password_hash = hash_pw(password)
		DBHandler.addUser(username=username, display_name=display_name, email=email, password_hash=password_hash, is_active=1)
	except Exception as e:
		return jsonify({'success':False,'message':str(e)}), 500
	if DEBUG_MODE:
		try:
			user_id = DBHandler.getUserIDByUsername(username)
		except Exception as e:
			return jsonify({'success':False,'message':str(e)}), 500
		return jsonify({'success':True,"id":user_id}), 200
	return jsonify({'success':True}), 200
	#TODO: add email verification before DB call 

@app.route('/users/api/get/fund_ids', methods=["GET"])
@login_required
def get_user_funds():
	'''
	Returns Dict for FundReference: id, name, user_id
	'''
	if DEBUG_MODE: # don't have working session wrapper for streamlit
		request_data = request.get_json()
		user_id = request_data["id"]
	else:
		user_id = session["user_id"]
	return jsonify(DBHandler.getUserFunds(user_id)), 200


@app.route('/leagues/api/get/user_leagues', methods=["GET"])
@login_required
def get_user_leagues():
	if DEBUG_MODE: # don't have working session wrapper for streamlit
		try:
			request_data = request.get_json()
			user_id = request_data["id"]
		except Exception as e:
			return {'success':False,'message':str(e)}, 500
		if not request_data:
			return 400
		
	else:
		user_id = session["user_id"]

	return jsonify(DBHandler.getUserLeagueRefs(user_id)), 200


@app.route('/league/api/get/leaderboard', methods=["GET"])
@login_required
def get_leaderboard():
	request_data = request.get_json()
	if not request_data:
		return jsonify({'success':False}), 400
	league_id = request_data["league_id"]
	if not league_id:
		return jsonify({'success':False}), 400
	funds_output = DBHandler.getLeaderboard(league_id)
	output_rows = []
	for row in funds_output:
		user = DBHandler.getUserRef(row["user_id"])
		new_row = {'fund_name': row["name"],'fund_id': row["id"], 
			'user_name':user["display_name"], 'user_id': user["id"],
			'logo_url': row["logo_url"], 'cash': row["cash"]
		}
		output_rows.append(new_row)
	return jsonify({'success':True, 'output':output_rows}),200
	#TODO: create function loop to total VALUE for each fund, not just cash
	
	#returns fund_id, fund_name, logo_url, cash, user_name, user_id


@app.route('/funds/api/get/user_fund', methods=["GET"])
@login_required
def get_user_fund():
	request_data = request.get_json()
	if not request_data:
		return jsonify({'success':False}), 400
	league_id = request_data["league_id"]
	user_id = request_data["user_id"]
	fund = DBHandler.getUserFund(user_id=user_id,league_id=league_id)
	return jsonify({'success':True,'output':fund}), 200


@app.route('/funds/api/get_portfolio',methods=['GET'])
@login_required
def get_portfolio():
	request_data = request.get_json()
	if not request_data:
		return jsonify({'success':False}), 400
	fund_id = request_data["fund_id"]
	if not fund_id:
		return jsonify({'success':False}), 400
	try:
		output_rows = DBHandler.getPortfolio(fund_id=fund_id)
	except Exception as err:
		#TODO: sanitize error output before prod
		return jsonify({'success':False}), 500

	return jsonify({'success':True,'output':output_rows}), 200


