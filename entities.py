from api import MassiveAPI
from decimal import Decimal

class BaseEntity:
	def __init__(entityID: int):
		self.id = entityID

class EntityReference:
	def __init__(entityID: int):
		self.id = entityID


class FundReference(EntityReference):
	"""
	Fields:
		id
		name
		user_id
	"""
	def __init__(*, fund_id: int, name: str, user_id: int):
		self.id = fund_id
		self.name = name
		self.user_id = user_id

class UserReference(EntityReference):
	"""
	Fields:
		id
		display_name
	"""
	def __init__(*,user_id: int, display_name: str):
		self.id = user_id
		self.display_name = display_name

	@staticmethod
	def byID(user_id: int):
		from db_tools import DBHandler
		out = DBHandler.getUserRef(user_id)
		return UserReference(user_id=out["id"],display_name=out["display_name"])

class League(BaseEntity):
	"""
	Attributes:
		id
		name
		commissioner_id
		mode
		start_money
		max_funds
		period_start
		period_end
	"""
	def __init__(self, *, league_id: int, name: str, comm_id: int, mode: str, start_money: int, max_funds: int, period_start: str, period_end: str):
		self.id = league_id
		self.name = name
		self.commissioner_id = comm_id
		self.mode = mode
		self.start_money = start_money
		self.max_funds = max_funds
		self.period_end = period_end
		self.period_start = period_start

	def addUser(self, user_id: int):
		"""
		Add to leaguemembers SQL, create a default fund in league associated with user
		"""
		league_id = self.id
		from db_tools import DBHandler
		if not DBHandler.canAddUser(league_id):
			raise ValueError("Too many users in League.")
		start_money = DBHandler.getStartCash(league_id)
		if not start_money:
			raise ValueError("No Start Money Field")
		Fund.addFund(user_id=user_id,league_id=league_id, start_cash=start_money)
		DBHandler.addUserToLeagueMembers(user_id=user_id, league_id=league_id)
		#TODO: finish this. initialize in fund in DB, then add user to league members
		


class Fund(BaseEntity):
	"""
	Attributes:
		id
		league_id
		user_id
		name
		logo_url
		cash

	"""
	def __init__(self, *, 
			league_id: int, 
			user_id: int, 
			fund_name: str, 
			fund_id: int, 
			cash: Decimal, 
			logo_url: str
		):

		self.id = fund_id
		self.user_id = user_id
		self.name = fund_name
		self.league_id = league_id
		self.cash = cash
		self.logo_url = logo_url


	def save(self) -> None:
		pass
		#TODO: Implement DB persistence call here.


	def getName(self) -> str:
		return self.name


	def getID(self) -> int:
		return self.id


	def getUserID(self) -> int:
		return self.user_id

	def getLeagueID(self) -> int:
		return self.league_id

	def getCash(self) -> Decimal:
		return self.cash



	@staticmethod
	def loadFundByID(fund_id: int):
		from db_tools import DBHandler
		out = DBHandler.getFund(fund_id)
		cash = out["cash"]
		if isinstance(out["cash"], str):
			cash = Decimal(out["cash"])
		
			
		return Fund(
			league_id=out["league_id"], 
			user_id=out["user_id"], 
			fund_name=out["name"], 
			fund_id=out["id"], 
			cash=cash, 
			logo_url=out["logo_url"]
		)
		#TODO: add SQL request handler? load fund object by ID?


	def toReference(self) -> FundReference:
		#TODO: is a reference supposed to be single instance or just hold ID/wtv
		return FundReference(self)


	def buyTickerByShares(self, *, ticker: str, amnt: int) -> None:
		"""
		Always wrap calls in try/except blocks. Errors will be reasons trade failed
		amnt = $ in USD to purchase, not number of shares
		ticker: ticker in all caps.
		"""
		if len(ticker) > 5 or len(ticker) == 0:
			raise ValueError(f"Invalid Ticker: {ticker}")
		
		try:
			price = MassiveAPI.getSharePrice(ticker.upper())
		except Exception as err:
			raise RuntimeError(f"API Error: {err}")

		buy_price = price * amnt
		owned_shares = self.portfolio.get(ticker,None)
		if buy_price > self.wallet:
			raise ValueError(f"Insufficient Funds to make trade. Wallet: {str(self.wallet)} - Trade: {str(buy_price)}")
		if not owned_shares:
			self.portfolio[ticker] = amnt
		else:
			self.portfolio[ticker] += amnt
		self.wallet -= buy_price
		self.save()


	def buyTickerByPrice(self, *, ticker: str, amnt: int) -> None:
		"""
		Always wrap calls in try/except blocks. Errors will be reasons trade failed
		amnt = $ in USD to purchase, not number of shares
		ticker: ticker in all caps.
		"""
		if len(ticker) > 5 or len(ticker) == 0:
			raise ValueError(f"Invalid Ticker: {ticker}")
		if amnt > self.wallet:
			raise ValueError(f"Insufficient Funds to make trade. Wallet: {str(self.wallet)} - Trade: {str(amnt)}")
		try:
			price = MassiveAPI.getSharePrice(ticker.upper())
		except Exception as err:
			raise RuntimeError(f"API Error: {err}")
		num_of_shares = amnt / price
		owned_shares = self.portfolio.get(ticker,None)
		if not owned_shares:
			self.portfolio[ticker] = num_of_shares
		else:
			self.portfolio[ticker] += num_of_shares
		self.wallet -= amnt
		self.save()


	def sellTickerByShares(self, *, ticker: str, amnt: int) -> None:
		"""
		Always wrap calls in try/except blocks. Errors will be reasons trade failed
		amnt = number of shares to sell
		ticker: ticker in all caps.
		"""
		if len(ticker) > 5 or len(ticker) == 0:
			raise ValueError(f"Invalid Ticker: {ticker}")
		try:
			price = MassiveAPI.getSharePrice(ticker.upper())
		except Exception as err:
			raise RuntimeError(f"API Error: {err}")
		owned_shares = self.portfolio.get(ticker,None)
		if not owned_shares:
			raise ValueError(f"No shares owned for {ticker}")
		if owned_shares < amnt:
			raise ValueError(f"Insufficient Shares - Owned: {str(owned_shares)}, Selling: {str(amnt)}")
		sale_amnt = amnt * price
		self.portfolio[ticker] -= amnt
		self.wallet += sale_amnt
		self.save()


	def sellTickerByDollars(self,*,ticker:str,amnt:int) -> None:
		"""
		Always wrap calls in try/except blocks. Errors will be reasons trade failed
		amnt = $ amnt to sell not number of shares to sell
		ticker: ticker in all caps.
		"""
		if len(ticker) > 5 or len(ticker) == 0:
			raise ValueError(f"Invalid Ticker: {ticker}")
		try:
			price = MassiveAPI.getSharePrice(ticker.upper())
		except Exception as err:
			raise RuntimeError(f"API Error: {err}")
		owned_shares = self.portfolio.get(ticker,None)
		if not owned_shares:
			raise ValueError(f"No shares owned for {ticker}")
		selling_shares = amnt / price
		if selling_shares > owned_shares:
			raise ValueError(f"Insufficient Shares - Owned: {str(owned_shares)}, Selling: {selling_shares}")

		self.portfolio[ticker] -= selling_shares
		self.wallet += amnt
		self.save()

	@staticmethod
	def addFund(*, user_id: int, league_id: int, start_cash: Decimal, name: str="XYZ Fund", logo_url=""):
		from db_tools import DBHandler
		DBHandler.addFund(league_id=league_id,user_id=user_id, cash=start_cash,name=name, logo_url=logo_url)




class User(BaseEntity):
	"""
	Attributes:
		username : str
		display_name : str
		email : str
		id: int
		active : bool

	# Registering New User:
		make separate helper that adds user row to table with set password hash and new userID
		init object from DB to autofill ID
	"""
	def __init__(self, *, 
			username: str, 
			display_name: str, 
			email_addr: str, 
			user_id: int, 
			is_active: int
		):
		self.username = username
		self.display_name = display_name
		self.email = email_addr
		self.id = user_id
		self.active = bool(is_active)


	def save(self) -> None:
		from db_tools import DBHandler
		try:
			DBHandler.saveUser(self)
		except Exception as e:
			raise RuntimeError(f"Persistence Failure: Failed to save UserID: {self.getID()}")

	@staticmethod
	def loadUserByID(userID: str):
		from db_tools import DBHandler
		user_dict = DBHandler.getUser(userID)
		if not user_dict:
			raise ValueError(f"No User found. ID: {str(userID)}")
		return User(username = user_dict["username"], 
			display_name = user_dict["display_name"], 
			email_addr= user_dict["email"],
			user_id = user_dict["id"],
			is_active = user_dict["is_active"],
			)

	def loadUserByEmail(email: str):
		from db_tools import DBHandler
		user_dict = DBHandler.getUserByEmail(email)
		if not user_dict:
			raise ValueError(f"No User found. Email: {email}")
		return User(username = user_dict["username"], 
			display_name = user_dict["display_name"], 
			email_addr= user_dict["email"],
			user_id = user_dict["id"],
			is_active = user_dict["is_active"],
			)		

	def getDisplayName(self) -> str:
		return self.display_name

	def getEmail(self) -> str:
		return self.email

	def getID(self) -> int:
		return self.id

	def getUsername(self) -> str:
		return self.username

	def isActive(self) -> bool:
		return self.active

	def addToLeague(self, league_id: int):
		"""
		Add to leaguemembers SQL, create a default fund in league associated with user
		"""
		from db_tools import DBHandler
		if not DBHandler.canAddUser(league_id):
			raise ValueError("Too many users in League.")
		start_money = DBHandler.getStartCash(league_id)
		Fund.addFund(user_id=self.id,league_id=league_id, start_cash=start_money)
		DBHandler.addUserToLeagueMembers(user_id=self.id, league_id=league_id)
		#TODO: finish this. initialize in fund in DB, then add user to league members
		
	@staticmethod
	def newUser(*, username: str, display_name: str, email: str, password: str, is_active: int=1):
		from auth_helpers import hash_pw
		from db_tools import DBHandler
		password_hash = hash_pw(password)
		DBHandler.addUser(username=username,display_name=display_name,email=email,password_hash=password_hash,is_active=is_active)



