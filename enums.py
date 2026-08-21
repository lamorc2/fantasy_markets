from enum import StrEnum

class enum LeagueMode(StrEnum):
	LeagueMode.H2H = "H2H",
	LeagueMode.Yearly = "Yearly",
	LeagueMode.Quarterly = "Quarterly",

class enum Methods(StrEnum):
	Methods.GET = "GET"
	Methods.POST = "POST"

class enum Side(StrEnum):
	Side.SELL = 'sell'
	Side.BUY = 'buy'