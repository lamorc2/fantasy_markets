import streamlit as st
import pandas as pd
import internal_api_helpers as api
import os
from entities import User, UserReference, Fund, FundReference, League, LeagueReference
from enum import Enum

class Page(str, Enum):
	Home = "Home"
	Fund = "Fund"
	League = "League"
	Ticker = "Ticker"
	Trade = "Trade"

class Subpage(str, Enum): #easy sessions tate variable to track sub pages for fund, ticker
	FundOverview = "FOver"
	FundPortfolio = "FPort"
	TickerSelect = "TSel"
	TickerOverview = "TOver"


def league_label(ref) -> str:
	return ref["name"]

def st_login(user_id: int):
	st.session_state["auth_key"] = 'y'
	st.session_state["user_id"] = user_id
	st.session_state["page"] = Page.Home


def st_logout():
	keys = ["auth_key","user_id", "league_id","league_name","ticker_cache"]
	for key in keys:
		st.session_state.pop(key,None)


def load_league(league_id: int, name:str):
	user_id = st.session_state.get('user_id',None)
	if not user_id:
		raise RuntimeError("Error: No user_id")
	fund = api.getUserFund(user_id=st.session_state['user_id'], league_id=league_id)
	if not fund:
		raise RuntimeError("Error: Could not load fund")
	st.session_state["league_id"] = league_id
	st.session_state["league_name"] = name
	st.session_state["page"] = Page.League
	st.session_state["fund_id"] = fund.id


def login_page() -> bool:
	username = st.text_input("Username:", placeholder="user")
	password = st.text_input("Password:", placeholder="****")
	if st.button("Login"):
		try:
			success = api.login(username=username,password=password)
		except Exception as e:
			st.warning(f"Error: {e}")
			return False
		if success[0]:
			st_login(success[1])
			return True
		else:
			st.warning("Login Failed! Username/Password not recognized!")
			return False
	return False


def create_user_page():
	username = st.text_input("Username:", placeholder="user")
	display_name = st.text_input("Display Name:", placeholder="Jim Doe")
	email = st.text_input("Email:", placeholder="your_email@gmail.com")
	password = st.text_input("Password:", placeholder="****")
	if st.button("Create New User"):
		try:
			new_id = api.createUser(username=username, display_name=display_name, email=email, password=password)
		except Exception as e:
			st.warning(f"Error! {str(e)}")
			return
		st.session_state.pop("creating_user",None)
		st_login(new_id)
		st.rerun()
	if st.button("Back To Login"):
		st.session_state.pop("creating_user",None)
		st.rerun()


def user_home_page() -> bool:
	st.header("=== HOME ===")
	try:
		leagues = api.getUserLeagues(st.session_state["user_id"])
		st.dataframe(pd.DataFrame(leagues),hide_index=True)
	except Exception as e:
		st.warning(f"Error: {str(e)}")
		return False
	if not leagues:
		return False
	selected_league = st.selectbox("League:", leagues, index=0, format_func=league_label)
	if st.button("Load League"):
		if not selected_league:
			st.warning("No League Selected")
			return False
		load_league(selected_league["id"],selected_league["name"])
		return True


def league_page() -> bool:
	name = st.session_state.get("league_name","!ERR_NO_NAME!")
	st.header(f"League: {name}")
	#TODO: display a leaderboard. Make a function to generate leaderboard

	st.write("Leaderboard:")
	data = api.getLeaderboard(st.session_state.get("league_id",""))
	st.dataframe(pd.DataFrame(data))
	if st.button("My Fund"):
		st.session_state["page"] = Page.Fund
		return True
	if st.button("Ticker View"):
		st.session_state["page"] = Page.Ticker
		return True
	return False
	#use session state


def fund_page():
	if "subpage" not in st.session_state:
		st.session_state["subpage"] = Subpage.FundOverview
	user_id = st.session_state.get("user_id",None)
	league_id = st.session_state.get("league_id",None)
	if not user_id and not league_id:
		st.error("Error: League/User ID not found")
		return False
	user_fund = api.getUserFund(user_id=user_id,league_id=league_id)
	st.header(f"Fund: {user_fund.name}")
	st.write(f"Cash: ${user_fund.cash}")
	st.write(f"Portfolio:")
	portfolio = api.getPortfolio(fund_id=user_fund.id)
	if not portfolio:
		st.write("No Stocks Owned")
	else:
		#TODO: add the stock API to the backend function to calculate value
		portfolio_df = pd.DataFrame(portfolio)
		st.dataframe(portfolio_df, hide_index=True)

@st.dialog("Buy Stock")
def buy_stock(price: float, owned: float, ticker: str):
	
	round_price = round(price, 2)
	round_owned = round(owned, 4)
	current_value = round(round_price * round_owned, 2)
	st.write("Purchase Stock?")
	st.write(f"Price: {round_price:.2f}")
	st.write(f"Owned: {round_owned:.2f} Shares")
	st.write(f"Value: ${current_value}")
	amnt = st.number_input("# to buy:")
	if amnt:
		new_shares = round(owned + amnt,4)
		new_value = round(new_shares * price,2)
	else:
		new_shares = owned
		new_value = current_value
	out1 = str(new_shares)
	st.write(f"After Purchase:")
	st.write(f"Owned: {new_shares:.2f} shares")
	st.write(f"Value: ${new_value:.2f}")
	col1, col2 = st.columns(2)
	with col1:
		if st.button("Cancel"):
			st.rerun()
	with col2:
		if st.button("Purchase"):
			if amnt <= 0.0:
				st.warning("Err: Cannot buy 0 shares")
			try:
				fund_id = st.session_state["fund_id"]
				api.buyTicker(ticker=ticker,fund_id=fund_id,amount=amnt,price=round_price)
				st.rerun()
			except ValueError as e:
				st.warning("Error: Not Enough $$")
			except Exception as err:
				st.error(f"Error: Failed to purchase stock. err={err}")

@st.dialog("Sell Stock")
def sell_stock(price: float, owned: float, ticker: str):

	round_price = round(float(price), 2)
	round_owned = round(float(owned), 4)
	current_value = round(round_price * round_owned, 2)
	st.write("Sell Stock?")
	st.write(f"Price: {round_price:.2f}")
	st.write(f"Owned: {round_owned:.2f} Shares")
	st.write(f"Value: ${current_value}")
	amnt = st.number_input("# to sell:")
	if amnt:
		new_shares = round(round_owned - amnt,4)
		new_value = round(new_shares * round_price,2)
	else:
		new_shares = float(owned)
		new_value = float(current_value)
	
	st.write(f"After Purchase:")
	st.write(f"Owned: {new_shares:.2f} shares")
	st.write(f"Value: ${new_value:.2f}")
	col1, col2 = st.columns(2)
	with col1:
		if st.button("Cancel"):
			st.rerun()
	with col2:
		if st.button("Purchase"):
			if float(amnt) <= 0.0:
				st.warning("Err: Cannot sell 0 shares")
			if float(amnt) > round_owned:
				st.warning("Err: Too many shares.")
			else:
				try:
					fund_id = st.session_state["fund_id"]
					api.sellTicker(ticker=ticker,fund_id=fund_id,amount=amnt,price=round_price)
					#TODO: make backend sell
					st.rerun()
				except ValueError as e:
					st.warning("Error: Not Enough $$")
				except Exception as err:
					st.error(f"Error: Failed to purchase stock. err={err}")

	
	

def ticker_page():
	'''
	

	c
	Current price

	d
	Change

	dp
	Percent change

	h
	High price of the day

	l
	Low price of the day

	o
	Open price of the day

	pc
	Previous close price
	'''
	st.header("Ticker:")
	data = None
	ticker = st.text_input("Ticker: (Max 5 Chars)", placeholder='AAPL').strip().upper()
	cached_ticker = "ticker_cache" in st.session_state and st.session_state.get("ticker_cache",None) is not None
	if st.button("Load"):
		if not ticker:	
			st.warning("Error: No Ticker")
			return False
		if len(ticker) > 5:
			st.warning("Error: Ticker too long")
			return False
		try:
			fund_id = st.session_state.get("fund_id",None)
			if not fund_id:
				st.error("Err: No fund_id")
				return False
			data = api.getTickerData(ticker=ticker, fund_id=fund_id)
			data["ticker"] = ticker
			st.session_state["ticker_cache"] = data
		except KeyError as err:
			st.error(f"KeyError: Could not fetch ticker data {e}")
		except Exception as e:
			st.error(f"Could not fetch ticker data {e}")

	if cached_ticker:
		data = st.session_state.get("ticker_cache",None)

	if data:
		current = data['c']
		change = data['d']
		percent = data['dp']
		day_high = data['h']
		day_low = data['l']
		open_price = data['o']
		last_close = data['pc']
		owned = data['owned']
		ticker = data["ticker"]
		st.header(f"Ticker: {ticker}")
		st.write(f"Owned Shares: {owned}")
		st.write(f"Current Price: {current}")
		st.write(f"Change: {change} ({percent}%)")
		st.write(f"Today's High: {day_high}")
		st.write(f"Today's Low: {day_low}")
		st.write(f"Open: {open_price}")
		st.write(f"Last Close: {last_close}")
		col1, col2 = st.columns(2)
		with col1:
			if st.button("Buy"): 
				buy_stock(price=current, owned=owned, ticker=ticker)
		with col2:
			if st.button("Sell"):
				sell_stock(price=current,owned=owned,ticker=ticker)
				#TODO: add sell functions


	return False

def main():
	logged_in = "auth_key" in st.session_state
	if not logged_in:
		creating_user = "creating_user" in st.session_state
		if not creating_user:
			if st.button("New User?"):
				st.session_state["creating_user"] = 'y'
				st.rerun()
			if login_page():
				st.rerun()
			return
		else:
			create_user_page()
			return
	else:
		col1, col2, col3 = st.columns(3)
		with col1:
			if st.button("Logout"):
				st_logout()
				st.rerun()
		with col2:
			if st.session_state["page"] != Page.Home and st.button("User Home"):
				st.session_state["page"] = Page.Home
				st.session_state.pop("league_id",None)
				st.rerun()
		with col3:
			if "league_id" in st.session_state and st.session_state["page"] != Page.League and st.button("League Page"):
				st.session_state["page"] = Page.League
				st.rerun()
	landing_page = st.session_state["page"]
	if landing_page == Page.Home:
		if user_home_page():
			st.rerun()
	elif landing_page == Page.League:
		if league_page():
			st.rerun()
	elif landing_page == Page.Fund:
		if fund_page():
			st.rerun()
	elif landing_page == Page.Ticker:
		if ticker_page():
			st.rerun()

if __name__ == "__main__":
	main()






