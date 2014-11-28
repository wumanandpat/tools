from TDDS2.Utils import *

_last = {}
_high = {}
_low  = {}
_vol  = {}
_last_mktctr = {}


def setHigh(symbol,price):
	_high[symbol] = price
def setLow (symbol,price):
	_low[symbol]  = price
def setLast(symbol,price):
	_last[symbol] = price
def setLast_Mktctr(symbol,pid):
	_last_mktctr[symbol] = pid
def setVol(symbol,volume):
	_vol[symbol] = volume

def updateStats(trade):
	updated = 0

	if trade.eligible_hilo:
		if not(trade.symbol in _low) or (trade.price < _low[trade.symbol]):
			_low[trade.symbol] = trade.price
			updated |= PRICECHANGEIND_LO

		if not(trade.symbol in _high) or (trade.price > _high[trade.symbol]):
			_high[trade.symbol] = trade.price
			updated |= PRICECHANGEIND_HIGH

	if trade.eligible_last:
		if not(trade.symbol in _last) or (trade.price != _last[trade.symbol]):
			_last[trade.symbol] = trade.price
			_last_mktctr[trade.symbol] = trade.header.origID
			updated |= PRICECHANGEIND_LAST

	if trade.eligible_vol:
		if trade.symbol in _vol:
			_vol[trade.symbol] += trade.volume
		else:
			_vol[trade.symbol]  = trade.volume

	return updated
