import db_tools as db
from entities import User, Fund, League
from flask import jsonify
from datetime import datetime
from prettytable import PrettyTable, from_db_cursor
from decimal import Decimal


def main():
	conn = db.DBHandler.get_db()
	cursor = conn.cursor()
	print("\n===== users =====\n")
	# Run a query and load it into PrettyTable directly from the cursor
	table = from_db_cursor(cursor.execute("SELECT * FROM users"))

	# Print the pretty output
	print(table)
	table = from_db_cursor(cursor.execute("SELECT * FROM leagues"))
	print("\n===== leagues =====\n")
	print(table)
	table = from_db_cursor(cursor.execute("SELECT * FROM funds"))
	print("\n===== funds =====\n")
	print(table)
	table = from_db_cursor(cursor.execute("SELECT * FROM league_members"))
	print("\n===== league_members =====\n")
	print(table)
	table = from_db_cursor(cursor.execute("SELECT * FROM positions"))
	print("\n===== positions =====\n")
	print(table)
	conn.close()


if __name__ == "__main__":
	main()