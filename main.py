import db_tools as db
from entities import User, Fund, League
from flask import jsonify
from datetime import datetime
from prettytable import PrettyTable, from_db_cursor
from decimal import Decimal
def main():
	print("initializing...")
	db.DBHandler.init_db()
	print("======== INITIALIZED DB =======")
	try:
		User.newUser(username="lamorc2",display_name="Connor LaMora",email="lamorc2@rpi.edu",password="test")
	except Exception as e:
		print(e)
	print("======== ADDED 1 TEST USER =======")
	for i in [1,2,3,4,5,6,7,8,9,10]:
		try:
			User.newUser(username=f"test{str(i)}",display_name=f"Connor {str(i)}",email=f"{str(i)}@fake.com",password=f"test{str(i)}")
		except Exception as e:
			print(e)
	print("======== INSERTED ALL TEST USERS =======")
	test_user = User.loadUserByEmail("lamorc2@rpi.edu")
	user_id = test_user.getID()
	League.newLeague(name="Test League",commissioner_id=user_id, mode='H2H', start_money=50_000, max_funds=8, period_start=datetime.now(),period_end=datetime.now())
	print("======== INSERTED TEST LEAGUE ========")
	try:
		test_fail_fund = Fund.addFund(user_id=1,league_id=1,start_cash=Decimal("20000.15"),name=f"LAMORC FUND",logo_url="")
	except Exception as e:
		print(f"Fund Failed to Add : {e}")
	print("====== FAIL FUND ATTEMPTED =====")
	#league_id = db.DBHandler._getLeagueIDByCommissionerID(user_id=user_id)
	for i in [1,2,3,4,5,6,7,8,9,10]:
		try:
			test_user = User.loadUserByUsername(f"test{i}")
			test_fund = Fund.addFund(user_id=test_user.id, league_id=1,start_cash=Decimal("20000.15"), name=f"TEST FUND{i}",logo_url="")
			#db.DBHandler.addTrade(fund_id=test_fund.id,user_id=test_user.id,ticker=f"TAP",shares=)
		except Exception as e:
			print(f"Fund Failed to Add : {e}")
	from prettytable import PrettyTable

	# Connect to your .db file
	conn = db.DBHandler.get_db()
	cursor = conn.cursor()

	# Run a query and load it into PrettyTable directly from the cursor
	table = from_db_cursor(cursor.execute("SELECT * FROM users"))

	# Print the pretty output
	print(table)
	table = from_db_cursor(cursor.execute("SELECT * FROM leagues"))
	print(table)
	table = from_db_cursor(cursor.execute("SELECT * FROM funds"))
	print(table)
	table = from_db_cursor(cursor.execute("SELECT * FROM league_members"))
	print(table)
	table = from_db_cursor(cursor.execute("SELECT * FROM positions"))
	print(table)
	conn.close()


if __name__ == "__main__":
	main()