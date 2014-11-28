import TDDS2.Message as Msg
from TDDS2.Utils import *
import struct

_handler = None

class Validator:
	def __init__(self):
		self._mpv = {}

	def reset(self):
		self.error = None

	def loadMpv(self,filename):
		with open(filename) as fh:
			for line in fh:
				line.rstrip("\n")
				(symbol,mpv) = line.split()
				self._mpv[symbol] = int(mpv)

	def isValid(self, msg):
		self.reset()
		if msg.key() in _handler:
			return _handler[msg.key()](self,msg)
		else:
			return True

	def _validShortTrade(self,trade):
		if not self._validLotSize(trade): return False
		if not self._validModifier(trade): return False
		#if not self._validPriceChangeInd(trade): return False
		return True
	
	def _validLongTrade(self,trade):
		if not self._validLotSize(trade): return False
		if not self._validModifier(trade): return False
		if not self._validAsof(trade): return False
		if not self._validLateModifier(trade): return False
		#if not self._validPriceChangeInd(trade): return False
		return True

	def _validLotSize(self,trade):
		roundlot = 100
		if trade.symbol in self._mpv:
			roundlot = self._mpv[trade.symbol]

		isOddlot  = True if trade.volume < roundlot else False
		isFlagged = True if trade.mod[3] == "I"     else False
		if isOddlot != isFlagged:
			self.error = "ERROR: INCONSISTENT ODDLOT (size=%d,mod=%s)" % (trade.volume, trade.mod)
			return False
		return True
		
	def _validModifier(self,trade):
		(b1,b2,b3,b4) = struct.unpack("cccc", trade.mod)
		if not (b1 in "@CNR"):
			self.error = "INVALID SALES CONDITION BYTE 1 <%s>" % (b1)
			return False
		if not (b2 in " "   ):
			self.error = "INVALID SALES CONDITION BYTE 1 <%s>" % (b2)
			return False
		if not (b3 in "TUZ "):
			self.error = "INVALID SALES CONDITION BYTE 1 <%s>" % (b3)
			return False
		if not (b4 in "IPW "):
			self.error = "INVALID SALES CONDITION BYTE 1 <%s>" % (b4)
			return False
		return True

	def _validPriceChangeInd(self,trade):
		if (trade.asof != ' ') and (int(trade.priceChangeInd) != 0):
			self.error = "ERROR: AS-OFS CANNOT UPDATE STATS" 
			return False
		if int(trade.priceChangeInd) != trade.updated:
			self.error = "ERROR: PRICE CHANGE IND: saw %s, need %s" % (trade.priceChangeInd, trade.updated)
			return False
		return True

	def _validAsof(self,trade):
		if not (trade.asof in "AR "):
			self.error = "ERROR: INVALID ASOF FLAG <%s>" % (trade.asof)
			return False
		isAsof = trade.header.date > trade.execDate
		isFlagged = trade.asof != ' '
		if isAsof != isFlagged:
			self.error = "ERROR: INVALID ASOF RptDate=<%s> ExecDate=<%s> Asof=<%s>" % (trade.header.date, trade.execDate, trade.asof)
			return False
		if isAsof and trade.priceChangeInd != "0":
			self.error = "ASOFs CANNOT UPDATE STATS"
			return False
		return True

	def _validLateModifier(self,trade):
		if trade.header.date != trade.execDate:
			return True
		
		if trade.mod[3] in 'PW':
			# ##############################################
			# Prior-Reference-Price and Average-Price trades
			# are not subject to auto-append logic
			# ##############################################
			return True

		recvTime = HHMMSSmmm2Millis(trade.header.time)
		execTime = HHMMSSmmm2Millis(trade.execTime)

		isFlagged = trade.mod[2] in "UZ"
		isLate = False
		if (execTime < PREOPEN_TIME):
			if ( recvTime >= PREOPEN_GRACE):
				isLate = True
		else:
			isLate = (recvTime-execTime) > LATEMILLIS

		if isLate and (not isFlagged):
			self.error = "ERROR: INVALID LATE CONDITION TimeDiff=%d RecvTime=%s ExecTime=%s Modifier=<%s>" % (
				recvTime-execTime,
				trade.header.time,
				trade.execTime,
				trade.mod)
			return False

		return True

_handler = {
	Msg.Trade_Short._CAT + Msg.Trade_Short._TYPE : Validator._validShortTrade,
	Msg.Trade_Long._CAT  + Msg.Trade_Long._TYPE  : Validator._validLongTrade,
	}
