"""
This file is to abstract actual SQL interactions away from the game code. 

# Postgres handles python Decimal
# SQLite does not

"""
import os
from decimal import Decimal
from enums import Side
DATABASE_URL = os.environ.get('DATABASE_URL')
SQLITE_PATH = "fantasy_markets.db"
if DATABASE_URL:
    import psycopg2
    import psycopg2.extras
    PH = '%s'  # Postgres placeholder
else:
    import sqlite3
    PH = '?'   # SQLite placeholder
class DBHandler:

	@staticmethod
	def fetchone(conn, sql, params=()):
	    """Unified fetchone that always returns a dict-like row."""
	    sql = sql.replace('?', PH)

	    if DATABASE_URL:
	        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
	        cur.execute(sql, params)
	        row = cur.fetchone()
	    else:
	        row = conn.execute(sql, params).fetchone()
	    return dict(row) if row is not None else None

	@staticmethod
	def fetchall(conn, sql, params=()):
	    """Unified fetchall that always returns a list of dict-like rows."""
	    sql = sql.replace('?', PH)
	    if DATABASE_URL:
	        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
	        cur.execute(sql, params)
	        return [dict(r) for r in cur.fetchall()]
	    else:
	        return [dict(r) for r in conn.execute(sql, params).fetchall()]

	@staticmethod
	def get_db():
		if DATABASE_URL:
		    conn = psycopg2.connect(DATABASE_URL)
		    conn.autocommit = False
		    return conn
		else:
		    conn = sqlite3.connect(SQLITE_PATH)
		    conn.row_factory = sqlite3.Row
		    return conn


	@staticmethod
	def execute(conn, sql, params=()):
	    """Unified execute."""
	    DATABASE_URL = os.environ.get('DATABASE_URL')
	    
	    if PH == '?':
	    	params = tuple(
		        str(p) if isinstance(p, Decimal) else p
		        for p in (params if isinstance(params, (tuple, list)) else (params,))
		    )
	    else:
	    	sql = sql.replace('?', PH)

	    if DATABASE_URL:
	        cur = conn.cursor()
	        cur.execute(sql, params)
	        return cur
	    else:

	        return conn.execute(sql, params)

	@staticmethod
	def _getLeagueIDsByCommissionerID(user_id: int):
		#for testing should not be used
		conn = DBHandler.get_db()
		sql = ''' SELECT id FROM leagues
		WHERE commissioner_id = ?
		'''
		params = (user_id,)
		out = DBHandler.fetchone(conn,sql,params)
		return out["id"]


	@staticmethod
	def getLoginUserByUsername(username: str):
		conn = DBHandler.get_db()
		sql = '''SELECT * FROM users WHERE username = ?'''
		params = (username,)
		return DBHandler.fetchone(conn,sql,params)

	@staticmethod
	def isFund(fund_id: int) -> bool:
		conn = DBHandler.get_db()
		sql =''' SELECT EXISTS (
		    SELECT 1 
		    FROM funds
		    WHERE id = ?
		) '''
		params = (fund_id,)
		return bool(DBHandler.fetchone(conn,sql,params))

	@staticmethod
	def getPosition(*, fund_id: int, ticker: str) -> int:
		conn = DBHandler.get_db()
		sql = ''' SELECT shares FROM positions
		WHERE fund_id = ? AND ticker = ?
		'''
		params = (fund_id,ticker)
		output = DBHandler.fetchone(conn,sql,params)
		return output["shares"]
		#return number of shares owned

	@staticmethod
	def getFund(fund_id: int):
		conn = DBHandler.get_db()
		sql = ''' SELECT * FROM funds
		WHERE id = ?
		'''
		params = (fund_id,)
		return DBHandler.fetchone(conn,sql,params)

	@staticmethod
	def getUserFunds(user_id: int):
		conn = DBHandler.get_db()
		sql = ''' SELECT id,name,user_id  FROM funds
			WHERE user_id = ?
			'''
		params = (user_id,)
		return DBHandler.fetchall(conn,sql,params)

	@staticmethod
	def getUserLeagueRefs(user_id : int) -> list[dict]:
		conn = DBHandler.get_db()
		sql = ''' SELECT league_id  FROM league_members
			WHERE user_id = ?
			'''
		params = (user_id,)
		rows = DBHandler.fetchall(conn,sql,params)
		ref_dicts = []
		for row in rows:
			ref_dicts.append(DBHandler.getLeagueRef(row["league_id"]))
		return ref_dicts
		
	@staticmethod
	def getAllUsersByRef():
		conn = DBHandler.get_db()
		sql = ''' SELECT * FROM users
			WHERE is_active = 1
		'''
		return DBHandler.fetchall(conn,sql)

	@staticmethod
	def getUser(user_id: int):
		conn = DBHandler.get_db()
		sql = ''' SELECT id, username, display_name, email, is_active FROM users
		WHERE id = ?
		'''
		params = (user_id,)
		return DBHandler.fetchone(conn,sql,params)


	@staticmethod
	def getUserByEmail(email: str):
		conn = DBHandler.get_db()
		sql = ''' SELECT id, username, display_name, email, is_active FROM users
		WHERE email = ?
		'''
		params = (email,)
		return DBHandler.fetchone(conn,sql,params)

	@staticmethod
	def getLeague(league_id: int) -> dict:
		conn = DBHandler.get_db()
		sql = ''' SELECT * FROM leagues
		WHERE id = ?
		'''
		params = (league_id,)
		return DBHandler.fetchone(conn,sql,params)

	@staticmethod
	def getLeagueRef(league_id:  int):
		conn = DBHandler.get_db()
		sql = ''' SELECT id, name FROM leagues
		WHERE id = ?
		'''
		params = (league_id,)
		return DBHandler.fetchone(conn,sql,params)

	@staticmethod
	def savePosition(*, fund_id: int, ticker: str, shares: int):
		conn = DBHandler.get_db()
		sql = ''' UPDATE positions
		SET shares = ?
		WHERE fund_id = ? AND ticker = ?
		'''
		params = (shares,fund_id,ticker)
		DBHandler.execute(conn,sql,params)
		conn.commit()

	

	@staticmethod
	def saveOrAddPosition(*, fund_id: int, ticker: str, new_shares: int):
		conn = DBHandler.get_db()
		sql = ''' INSERT INTO positions (fund_id, ticker, shares) VALUES (?,?,?) 
		ON CONFLICT(fund_id,ticker) DO UPDATE SET shares = excluded.shares
		'''
		params = (fund_id, ticker, shares)
		DBHandler.execute(conn,sql,params)
		conn.commit()


	@staticmethod
	def addTrade(*, 
			fund_id: int, 
			user_id: int,
			ticker: str, 
			side: Side, 
			shares: int, price: int, 
			trade_value: Decimal
		):

		conn = DBHandler.get_db()
		sql = ''' INSERT INTO trades (fund_id, acted_by_user_id, ticker, side, shares, price, notional) VALUES (?,?,?,?,?,?,?)
		'''
		params = (fund_id,user_id,ticker,side,shares,price,trade_value)
		DBHandler.execute(conn,sql,params)
		conn.commit()

	@staticmethod
	def addUser(*, username: str, display_name: str, email: str, password_hash: str, is_active: int):
		conn = DBHandler.get_db()
		sql = ''' INSERT INTO users (username,display_name,email,password_hash,is_active) VALUES (?,?,?,?,?)
		'''
		params = (username,display_name,email,password_hash,is_active)
		DBHandler.execute(conn,sql,params)
		conn.commit()

	@staticmethod
	def addLeague(*,name: str, 
			commissioner_id: int, 
			mode: str='H2H', 
			start_money: int, 
			max_funds: int, 
			period_start: str, 
			period_end: str
		):
		conn = DBHandler.get_db()
		sql = ''' INSERT INTO leagues (name,commissioner_id ,mode,start_money,max_funds, period_start, period_end) VALUES (?,?,?,?,?,?,?) RETURNING id
		'''
		params = (name,commissioner_id ,mode,start_money,max_funds, period_start, period_end)
		cur = DBHandler.execute(conn,sql,params)
		row = cur.fetchone()
		conn.commit()
		if row is None:
			return None
		return row["id"] if isinstance(row, dict) or hasattr(row, "keys") else row[0]


	@staticmethod
	def addFund(*,
			league_id: int, 
			user_id: int, 
			name: str, 
			logo_url: str="", 
			cash: Decimal
		):
		conn = DBHandler.get_db()
		sql = ''' INSERT INTO funds (league_id, user_id, name, logo_url, cash) VALUES (?,?,?,?,?)
		'''
		params = (league_id,user_id,name,logo_url,cash)
		DBHandler.execute(conn,sql,params)
		conn.commit()

	@staticmethod
	def canAddUser(league_id: int) -> bool:
		conn = DBHandler.get_db()
		sql = '''SELECT COUNT(*) AS n
			FROM league_members
			WHERE league_id = ?
			'''

		params = (league_id,)
		out = DBHandler.fetchone(conn,sql,params)
		num = out["n"]
		sql2 = '''SELECT max_funds from leagues
			WHERE id = ?
			'''
		out2 = DBHandler.fetchone(conn,sql2,params)
		if out2 == None:
			raise ValueError(f"No League found for league_id: {league_id}")
		_max = out2["max_funds"]
		return _max > num


	@staticmethod
	def getPortfolio(fund_id: int):
		conn = DBHandler.get_db()
		sql = '''SELECT ticker, shares FROM positions
		WHERE fund_id = ?
		'''
		params = (fund_id,)
		return DBHandler.fetchall(conn,sql,params)




	@staticmethod
	def getStartCash(league_id:int) -> int:
		conn = DBHandler.get_db()
		sql = '''SELECT start_money FROM leagues
			WHERE id = ?
			'''

		params = (league_id,)
		out = DBHandler.fetchone(conn,sql,params)
		return out["start_money"]

	@staticmethod
	def updateFundWallet(*, fund_id: int, new_wallet: Decimal) -> None:
		conn = DBHandler.get_db()
		sql = ''' UPDATE funds
		SET cash = ?
		WHERE id = ?
		'''
		params = (new_wallet,fund_id)
		DBHandler.execute(conn,sql,params)
		conn.commit()
		#just change wallet value in row


	@staticmethod
	def saveUser(user: object) -> None:
		from entities import User
		email = user.getEmail()
		display_name = user.getDisplayName()
		userID = user.getID()
		username = user.getUsername()
		if user.isActive():
			active = 1
		else:
			active = 0
		conn = DBHandler.get_db()
		sql = ''' UPDATE users
		SET email = ?, display_name = ?, username = ?, is_active = ?
		WHERE id = ?
		'''
		params = (email,display_name,username,active,userID)
		DBHandler.execute(conn,sql,params)
		conn.commit()
		#rewrite entire user row minus password hash

	@staticmethod
	def addUserToLeagueMembers(*,user_id: int, league_id: int) -> None:
		conn = DBHandler.get_db()
		sql = ''' INSERT INTO league_members (user_id, league_id) VALUES (?, ?)
		'''
		params = (user_id,league_id)
		DBHandler.execute(conn,sql,params)
		conn.commit()

	@staticmethod
	def getUserRef(user_id: int):
		conn = DBHandler.get_db()
		sql = ''' SELECT id,display_name FROM users
			WHERE id = ?
		'''
		params = (user_id,)
		return DBHandler.fetchone(conn,sql,params)

	@staticmethod
	def removeUserFromLeague(*,user_id: int, league_id: int) -> None:
		conn = DBHandler.get_db()
		sql = ''' DELETE FROM league_members WHERE user_id = ? AND league_id = ?
		'''
		params = (user_id,league_id)
		DBHandler.execute(conn,sql,params)
		conn.commit()


	@staticmethod
	def getUserFund(*, user_id: int, league_id: int) -> dict:
		conn = DBHandler.get_db()
		sql = ''' SELECT * FROM funds 
			WHERE user_id = ? AND league_id = ?
		'''
		params = (user_id, league_id)
		#handle fund creation outside of DB handlers
		return DBHandler.fetchone(conn,sql,params)

	@staticmethod
	def getAllUserIDs():
		conn = DBHandler.get_db()
		if DATABASE_URL:
			sql = ''' SELECT json_agg(id) FROM users
				WHERE is_active = 1
				'''
		else: 
			sql = ''' SELECT json_group_array(id) FROM users
				WHERE is_active = 1
				'''

		out = DBHandler.fetchone(conn,sql)
		return out["id"]

	@staticmethod
	def getAllUserRefs():
		conn = DBHandler.get_db()
	
		sql = ''' SELECT id, display_name FROM users
			WHERE is_active = 1
			'''

		return DBHandler.fetchall(conn,sql)

	@staticmethod
	def getUsersLeagues(user_id: int):
		conn = DBHandler.get_db()
		sql = ''' SELECT league_id FROM league_members
		WHERE user_id = ?
		'''
		params = (user_id,)
		return DBHandler.fetchall(conn,sql,params)
	@staticmethod
	def getUserByUsername(username: str):
		conn = DBHandler.get_db()
		sql = ''' SELECT id, username, display_name, email, is_active FROM users
		WHERE username = ?
		'''
		params = (username,)
		return DBHandler.fetchone(conn,sql,params)


	@staticmethod
	def getUserIDByUsername(username: str):
		conn = DBHandler.get_db()
		sql = ''' SELECT id FROM users
		WHERE username = ?
		'''
		params = (username,)
		row = DBHandler.fetchone(conn,sql,params)
		return row["id"]

	@staticmethod
	def getLeaderboard(league_id: int):
		conn = DBHandler.get_db()
		sql = ''' SELECT id, user_id, name, logo_url, cash FROM funds
		WHERE league_id = ?
		ORDER BY cash DESC
		'''
		params = (league_id,)
		return DBHandler.fetchall(conn,sql,params)

	@staticmethod
	def init_db():
		conn = DBHandler.get_db()
		DATABASE_URL = os.environ.get('DATABASE_URL')
		# SQLite uses TEXT, PostgreSQL uses Decimal

		if DATABASE_URL:
			DBHandler.execute(conn, '''PRAGMA foreign_keys = ON''')
			DBHandler.execute(conn, '''CREATE TABLE IF NOT EXISTS users (
			    id SERIAL PRIMARY KEY,
			    username TEXT NOT NULL UNIQUE,
			    display_name TEXT NOT NULL,
			    email TEXT NOT NULL UNIQUE,
			    password_hash TEXT NOT NULL,
			    is_active INTEGER NOT NULL DEFAULT 1
			)''')
			DBHandler.execute(conn, '''CREATE TABLE IF NOT EXISTS leagues (
			    id SERIAL PRIMARY KEY,
			    name TEXT NOT NULL,
			    commissioner_id INTEGER NOT NULL,
			    mode TEXT NOT NULL CHECK (mode IN ('H2H', 'Quarterly', 'Yearly')),
			    start_money INTEGER NOT NULL,
			    max_funds INTEGER NOT NULL,
			    period_start TEXT,
			    period_end TEXT,
			    FOREIGN KEY (commissioner_id) REFERENCES users(id)
				)
			''')
			DBHandler.execute(conn, '''CREATE TABLE IF NOT EXISTS funds (
			    id SERIAL PRIMARY KEY,
			    user_id INTEGER NOT NULL,
			    league_id INTEGER NOT NULL,
			    name TEXT NOT NULL,
			    logo_url TEXT,
			    cash DECIMAL NOT NULL,
			    FOREIGN KEY (league_id) REFERENCES leagues(id),
			    FOREIGN KEY (user_id) REFERENCES users(id),
			    UNIQUE (league_id, user_id)
				
				)
			''')
			DBHandler.execute(conn, '''CREATE TABLE IF NOT EXISTS positions (
			    fund_id INTEGER NOT NULL,
			    ticker TEXT NOT NULL,
			    shares DECIMAL NOT NULL,
			    PRIMARY KEY (fund_id, ticker),
			    FOREIGN KEY (fund_id) REFERENCES funds(id)
				)

			''')

			DBHandler.execute(conn, '''CREATE TABLE IF NOT EXISTS trades (
			    id SERIAL PRIMARY KEY,
			    fund_id INTEGER NOT NULL,
			    acted_by_user_id INTEGER NOT NULL,
			    ticker TEXT NOT NULL,
			    side TEXT NOT NULL CHECK (side IN ('buy', 'sell')),
			    shares DECIMAL NOT NULL,
			    price DECIMAL NOT NULL,
			    notional DECIMAL NOT NULL,
			    created_at TEXT NOT NULL DEFAULT (datetime('now')),
			    FOREIGN KEY (fund_id) REFERENCES funds(id),
			    FOREIGN KEY (acted_by_user_id) REFERENCES users(id)
				)
			''')
			DBHandler.execute(conn, '''CREATE TABLE IF NOT EXISTS league_members (
			    user_id INTEGER NOT NULL,
			    league_id INTEGER NOT NULL,
			    PRIMARY KEY (user_id,league_id),
			    FOREIGN KEY (user_id) REFERENCES users(id),
			    FOREIGN KEY (league_id) REFERENCES leagues(id)
			)''')
			conn.commit()
		else:
			DBHandler.execute(conn, '''PRAGMA foreign_keys = ON''')
			DBHandler.execute(conn, '''CREATE TABLE IF NOT EXISTS users (
			    id INTEGER PRIMARY KEY AUTOINCREMENT,
			    username TEXT NOT NULL UNIQUE,
			    display_name TEXT NOT NULL,
			    email TEXT NOT NULL UNIQUE,
			    password_hash TEXT NOT NULL,
			    is_active INTEGER NOT NULL DEFAULT 1
			)''')
			DBHandler.execute(conn, '''CREATE TABLE IF NOT EXISTS leagues (
			    id INTEGER PRIMARY KEY AUTOINCREMENT,
			    name TEXT NOT NULL,
			    commissioner_id INTEGER NOT NULL,
			    mode TEXT NOT NULL CHECK (mode IN ('H2H', 'Quarterly', 'Yearly')),
			    start_money INTEGER NOT NULL,
			    max_funds INTEGER NOT NULL,
			    period_start TEXT,
			    period_end TEXT,
			    FOREIGN KEY (commissioner_id) REFERENCES users(id)
				)
			''')
			DBHandler.execute(conn, '''CREATE TABLE IF NOT EXISTS funds (
			    id INTEGER PRIMARY KEY AUTOINCREMENT,
			    user_id INTEGER NOT NULL, 
			    league_id INTEGER NOT NULL,
			    name TEXT NOT NULL,
			    logo_url TEXT,
			    cash TEXT NOT NULL,
			    FOREIGN KEY (league_id) REFERENCES leagues(id),
			    FOREIGN KEY (user_id) REFERENCES users(id),
			    UNIQUE (league_id,user_id)
				)
			''')
			DBHandler.execute(conn, '''CREATE TABLE IF NOT EXISTS positions (
			    fund_id INTEGER NOT NULL,
			    ticker TEXT NOT NULL,
			    shares TEXT NOT NULL,
			    PRIMARY KEY (fund_id, ticker),
			    FOREIGN KEY (fund_id) REFERENCES funds(id)
				)

			''')

			DBHandler.execute(conn, '''CREATE TABLE IF NOT EXISTS trades (
			    id INTEGER PRIMARY KEY AUTOINCREMENT,
			    fund_id INTEGER NOT NULL,
			    acted_by_user_id INTEGER NOT NULL,
			    ticker TEXT NOT NULL,
			    side TEXT NOT NULL CHECK (side IN ('buy', 'sell')),
			    shares TEXT NOT NULL,
			    price TEXT NOT NULL,
			    notional TEXT NOT NULL,
			    created_at TEXT NOT NULL DEFAULT (datetime('now')),
			    FOREIGN KEY (fund_id) REFERENCES funds(id),
			    FOREIGN KEY (acted_by_user_id) REFERENCES users(id)
				)
			''')
			DBHandler.execute(conn, '''CREATE TABLE IF NOT EXISTS league_members (
			    user_id INTEGER NOT NULL,
			    league_id INTEGER NOT NULL,
			    PRIMARY KEY (user_id,league_id),
			    FOREIGN KEY (user_id) REFERENCES users(id),
			    FOREIGN KEY (league_id) REFERENCES leagues(id)
			)''')
			conn.commit()
