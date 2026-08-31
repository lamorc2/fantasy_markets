# These are wrappers for making API calls so the streamlit page just uses pretty functions
from decimal import Decimal
from flask import Flask, jsonify, request
from flask_cors import CORS
from entities import Fund, User, UserReference, League, LeagueReference
from db_tools import DBHandler
from markupsafe import escape
import requests
import json
import os
from auth_helpers import hash_pw, check_pw
API_URL = os.environ.get("API_BASE_URL", "http://127.0.0.1:5000")

def loadAllUserRefs() -> list[UserReference]:
	url = API_URL + "/users/api/get/allrefs"
	refs = []
	response = requests.get(url)
	response_list = response.json()
	for ref_dict in response_list:
		user_id = ref_dict.get("id", "!MISSING!")
		name = ref_dict.get("display_name","!MISSING!")
		refs.append(UserReference(user_id=user_id,display_name=name))
	return refs
	#Calls API route that sends DB data, uses constructor to build Ref

def loadFullUserDict(user_id: int):
	if not isinstance(user_id,int):
		raise ValueError
	url = API_URL + f"/users/api/get/{user_id}"
	
	response = requests.get(url)
	response_dict= response.json()
	return response_dict

def getUserFunds(user_id: int):
	if not isinstance(user_id,int):
		raise ValueError
	url = API_URL + f"/users/api/get/fund_ids"
	payload = {"id":user_id}
	response = requests.get(url,json=payload)
	response_dict = response.json()
	return response_dict

def createUser(*,username: str, display_name: str, email: str, password: str):
	url = API_URL + "/users/api/post/createUser"
	payload = {"username":username,"display_name":display_name,"email":email,"password":password}
	response = requests.post(url,json=payload)
	
	if response.status_code != 200:
		if response.json():
			response_json = response.json()
			message = response_json.get("message",None)
			if message:
				raise RuntimeError(f"Error! status_code={response.status_code} message={message}")
		raise RuntimeError(f"Error! status_code={response.status_code}")
	response_json = response.json()
	if not response_json:
		raise RuntimeError(f"Error! No JSON from Response. status_code={response.status_code}")
	user_id = response_json.get("id",None)
	if user_id is None:
		raise TypeError(f"No id in response. Response: {str(response_json)}")
	return user_id 



def login(*,username: str, password: str) -> (bool, int):
	url = API_URL + "/users/api/login"
	payload = {"username":username,"password":password}
	response = requests.post(url,json=payload)
	if response.status_code == 202:
		r_json = response.json()
		if r_json:
			user_id = r_json.get("id",None)
			if user_id:
				return (True, user_id)
		raise ValueError("No ID Returned, Successful Login")
	elif response.status_code == 401:
		return (False, 0)
	else:
		r_json = response.json()
		if r_json:
			raise ValueError(f"Bad request. status_code={response.status_code} message={r_json.get('message','')}")

def getUserLeagues(user_id:int):
	url = API_URL + "/leagues/api/get/user_leagues"
	payload = {"id":user_id}
	response = requests.get(url,json=payload)
	if response.status_code != 200:
		try:
			data = response.json()
			err = data["message"]
			raise RuntimeError(f"Error: status_code={response.status_code}, message={str(err)}")
		except Exception as e:
			raise RuntimeError(f"Error: status_code={response.status_code} err={str(e)}")

	data = response.json()
	if not data:
		return []
	return data
	#TODO: finish


def getLeaderboard(league_id: int):
	url = API_URL + "/league/api/get/leaderboard"
	payload = {"league_id": league_id}
	response = requests.get(url,json=payload)
	if response.status_code == 200:
		data = response.json()
		if not data:
			return []
		return data['output']
	else:
		data = response.json()
		if not data:
			raise RuntimeError(f"Error: status_code={response.status_code}")
		raise RuntimeError(f"Error: status_code={response.status_code}, err={str(data)}")


def getTickerData(ticker: str):
	pass

def getUserFund(*,league_id: int, user_id: int) -> Fund:
	url = API_URL + "/funds/api/get/user_fund"
	payload = {"league_id":league_id, "user_id": user_id}
	response = requests.get(url,json=payload)
	if response.status_code == 200:
		out_dict = response.json()
		if not out_dict:
			raise RuntimeError(f"Error: No JSON dict response from /funds/api/get/user_fund, status_code={response.status_code}")
		try:
			fund_dict = out_dict["output"]
		except KeyError as err:
			raise RuntimeError("Error: No output on JSON response")
		if not fund_dict:
			raise RuntimeError(f"Error: No output JSON response from /funds/api/get/user_fund, status_code={response.status_code}")
	else:
		code = response.status_code
		json = response.json()
		if not json:
			raise RuntimeError(f"Error: status_code={code}")
		try:
			msg = json["message"]
		except Exception as e:
			raise RuntimeError(f"Error: status_code={code}")
		raise RuntimeError(f"Error: status_code={code}, err={msg}")

	try:
		name = fund_dict['name']
		fund_id = fund_dict["id"]
		logo_url = fund_dict["logo_url"]
		cash = fund_dict["cash"]
	except KeyError as err:
		raise RuntimeError(f"Error: Bad Response, JSON missing key. status_code={response.status_code}, err={str(err)} json={str(fund_dict)}")
	except Exception as e:
		raise RuntimeError(f"Error: str{e}")
	user_fund = Fund(league_id=league_id,user_id=user_id,fund_name=name,fund_id=fund_id,logo_url=logo_url,cash=cash)
	return user_fund

def getPortfolio(fund_id: int):
	url = API_URL + "/funds/api/get_portfolio"
	payload = {'fund_id':fund_id}
	response = requests.get(url,json=payload)
	if response.status_code != 200:
		raise RuntimeError(f"Err: status_code={response.status_code}")
		#TODO: error handling stuff
	data = response.json()
	if not data:
		raise RuntimeError(f"Err: No JSON status_code={response.status_code}")
	try:
		output = data["output"]
	except KeyError:
		raise RuntimeError(f"Err: No output in response JSON status_code={response.status_code}")

	return output #should be a dict right?





