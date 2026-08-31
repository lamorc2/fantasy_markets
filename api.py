import json
from enums import Methods
#_NYSE_URL = "https://api.developer.nyse.com/client/top/"

class APIHandler():

	def makeRequest():
		pass

	def POST():
		pass

	def GET():
		pass



class MassiveAPI(APIHandler):
	@staticmethod
	def getAllTickers():
		path = "/v3/reference/tickers"
		method = Methods.GET

	@staticmethod
	def getTickerOverview(ticker: str):
		path = ""
		method = Methods.GET
	@staticmethod
	def getSharePrice(ticker: str):
		pass
		#TODO: add this, raise ticker DNE as ValueError, any API issue as anything else

""" 
NYSE api needs firm or contract

class NYSEAPI(APIHandler):

	def requestAuthToken():
		
		URL: https://api.developer.nyse.com/client/top/
		Method:POST /oauth/token

		Headers:
			Authorization : Basic VE9QLUFQSS0wMTp0b3BhcGktY2xpZW50LXNlY3JldDE=
			Content-Type : application/x-www-form-urlencoded

		Parameters:
			Name	Type	Description
			grant_type	String	The grant type (e.g., password, refresh_token).
			username	String	The user's username (required for password grant type).
			password	String	The user's password (required for password grant type).
			refresh_token	String	The refresh token (required for refresh_token grant type).
		
		url = _NYSE_URL
		request = "POST /oauth/token"
		headers = []
		auth_header = 

"""