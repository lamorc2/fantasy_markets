"""
This file is to abstract actual SQL interactions away from the game code. 

# Postgres handles python Decimal
# SQLite does not

"""
import os
from decimal import Decimal
from enums import Side
DATABASE_URL = os.environ.get('DATABASE_URL')

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
	        return cur.fetchone()
	    else:
	        return conn.execute(sql, params).fetchone()

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
	def getPosition(*, fund_id: int, ticker: str) -> int:
		conn = DBHandler.get_db()
		sql = ''' SELECT shares FROM positions
		WHERE id = ? AND ticker = ?
		'''
		params = tuple(fund_id,ticker)
		output = DBHandler.fetchone(conn,sql,params)
		return output["shares"]
		#return number of shares owned

	@staticmethod
	def getFund(fund_id: int) -> dict:
		conn = DBHandler.get_db()
		sql = ''' SELECT * FROM users
		WHERE id = ?
		'''
		params = tuple(fund_id,)
		return DBHandler.fetchone(conn,sql,params)

	@staticmethod
	def getUser(user_id: int) -> dict | None:
		conn = DBHandler.get_db()
		sql = ''' SELECT id, username, display_name, email, is_active FROM users
		WHERE id = ?
		'''
		params = tuple(user_id,)
		return DBHandler.fetchone(conn,sql,params)

	@staticmethod
	def getUserByEmail(email: str) -> dict | None:
		conn = DBHandler.get_db()
		sql = ''' SELECT id, username, display_name, email, is_active FROM users
		WHERE email = ?
		'''
		params = tuple(email,)
		return DBHandler.fetchone(conn,sql,params)

	@staticmethod
	def getLeague(league_id: int) -> dict:
		conn = DBHandler.get_db()
		sql = ''' SELECT * FROM leagues
		WHERE id = ?
		'''
		params = tuple(league_id,)
		return DBHandler.fetchone(conn,sql,params)

	@staticmethod
	def savePosition(*, fund_id: int, ticker: str, shares: int):
		conn = DBHandler.get_db()
		sql = ''' UPDATE positions
		SET shares = ?
		WHERE fund_id = ? AND ticker = ?
		'''
		params = tuple(shares,fund_id,ticker)
		DBHandler.execute(conn,sql,params)
		conn.commit()


	@staticmethod
	def addTrade(*, 
			fund_id: int, 
			user_id: int,
			ticker: str, 
			side: Side, 
			shares: str, price: str, 
			trade_value: str
		):

		conn = DBHandler.get_db()
		sql = ''' INSERT INTO trades (fund_id, acted_by_user_id, ticker, side, shares, price, notional) VALUES (?,?,?,?,?,?,?)
		'''
		params = tuple(fund_id,user_id,ticker,side,shares,price,trade_value)
		DBHandler.execute(conn,sql,params)
		conn.commit()


	@staticmethod
	def addFund(*,
			league_id: int, 
			user_id: int, 
			name: str, 
			logo_url: str="", 
			cash: Decimal
		):
		conn = DBHandler.get_db()
		sql = ''' INSERT INTO funds (league_id, user_id, name, logo_url, cash) VALUES (?,?,?,?,?,?)
		'''
		params = tuple(league_id,user_id,name,logo_url,cash)
		DBHandler.execute(conn,sql,params)
		conn.commit()

	@staticmethod
	def canAddUser(league_id: int) -> bool:
		conn = DBHandler.get_db()
		sql = '''SELECT COUNT(*) AS n
			FROM league_members
			WHERE league_id = ?
			'''

		params = tuple(league_id,)
		out = DBHandler.fetchone(conn,sql,params)
		num = out["n"]
		sql2 = '''SELECT max_funds from leagues
			WHERE league_id = ?
			'''
		out2 = DBHandler.fetchone(conn,sql2,params)
		if out2 == None:
			raise ValueError(f"No League found for league_id: {league_id}")
		_max = out["max_funds"]
		return _max > num


	

	@staticmethod
	def getStartCash(league_id:int) -> int:
		conn = DBHandler.get_db()
		sql = '''SELECT start_money
			WHERE league_id = ?
			'''

		params = tuple(league_id,)
		out = DBHandler.fetchone(conn,sql,params)
		return out["start_money"]

	@staticmethod
	def updateFundWallet(*, fund_id: int, new_wallet: Decimal) -> None:
		conn = DBHandler.get_db()
		sql = ''' UPDATE funds
		SET cash = ?
		WHERE id = ?
		'''
		params = tuple(fund_id,new_wallet)
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
		sql = ''' UPDATE positions
		SET email = ?, display_name = ?, username = ?, is_active = ?
		WHERE id = ?
		'''
		params = tuple(email,display_name,username,active,userID)
		DBHandler.execute(conn,sql,params)
		conn.commit()
		#rewrite entire user row minus password hash

	@staticmethod
	def addUserToLeagueMembers(*,user_id: int, league_id: int) -> None:
		conn = DBHandler.get_db()
		sql = ''' INSERT INTO league_members (user_id, league_id) VALUES (?, ?)
		'''
		params = tuple(user_id,league_id)
		DBHandler.execute(conn,sql,params)
		conn.commit()


	@staticmethod
	def removeUserFromLeague(*,user_id: int, league_id: int) -> None:
		conn = DBHandler.get_db()
		sql = ''' DELETE FROM league_members WHERE user_id = ? AND league_id = ?
		'''
		params = tuple(user_id,league_id)
		DBHandler.execute(conn,sql,params)
		conn.commit()


	@staticmethod
	def getUserFund(*, user_id: int, league_id: int) -> dict:
		conn = DBHandler.get_db()
		sql = ''' SELECT * FROM funds 
			WHERE user_id = ? AND league_id = ?
		'''
		params = tuple(user_id, league_id)
		#handle fund creation outside of DB handlers
		return DBHandler.fetchone(conn,sql,params)


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
			    UNIQUE (league_id, name)
				
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
			    id SERIAL PRIMARY KEY,
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
			    PRIMARY KEY (user_id,league_id)
			    FOREIGN KEY (user_id) REFERENCES users(id)
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
			    acronym TEXT,
			    logo_url TEXT,
			    cash TEXT NOT NULL,
			    FOREIGN KEY (league_id) REFERENCES leagues(id),
			    FOREIGN KEY (user_id) REFERENCES users(id),
			    UNIQUE (league_id)
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
			conn.commit()
