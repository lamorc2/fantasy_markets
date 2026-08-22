import db_tools as db
from entities import User, Fund, League
from flask import jsonify
from datetime import datetime
from prettytable import PrettyTable, from_db_cursor
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
	db.DBHandler.addLeague(name="Test League",commissioner_id=user_id, mode='H2H', start_money=50_000, max_funds=8, period_start=datetime.now(),period_end=datetime.now())
	print("======== INSERTED TEST LEAGUE ========")

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
	connection.close()

if __name__ == "__main__":
	main()