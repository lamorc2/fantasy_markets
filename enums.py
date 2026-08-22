from enum import Enum


class LeagueMode(str, Enum):
	H2H = "H2H"
	Yearly = "Yearly"
	Quarterly = "Quarterly"

class Methods(str, Enum):
	GET = "GET"
	POST = "POST"

class Side(str, Enum):
	SELL = "sell"
	BUY = "buy"
