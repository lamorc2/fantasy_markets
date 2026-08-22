# These are wrappers for making API calls so the streamlit page just uses pretty functions
from decimal import Decimal
from flask import Flask, jsonify, request
from flask_cors import CORS
from entities import Fund, User, UserReference
from db_tools import DBHandler
from markupsafe import escape
import requests
import json
API_URL = os.environ.get("API_BASE_URL", "http://127.0.0.1:5000")

def loadAllUserRefs() -> list[UserReference]
	url = API_URL + "/users/api/allrefs"
	refs = []
	response = requests.get(url)
	response_list = json.loads(response)
	for ref_dict in response_list:
		user_id = ref_dict.get("id", "!MISSING!")
		name = ref_dict.get("display_name","!MISSING!")
		refs.append(UserReference(user_id=user_id,display_name=name))
	return refs
	#Calls API route that sends DB data, uses constructor to build Ref



