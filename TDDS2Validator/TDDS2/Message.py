import struct
import abc
import TDDS2.Statistics
from TDDS2.Utils import *

# #####################################################################
# Base utilities common to all messages
# #####################################################################
class Header():
	def parse(self,line):
		(self.catType,
		self.sessionID,
		self.retransReq,
		self.seqno,
		self.origID,
		self.date,
		self.time) = struct.unpack("2sc2s8s2s8s9s", line[0:HEADER_SIZE])

class _Message(object):
	__metaclass__ = abc.ABCMeta

	def msgCat(self):  return self._CAT
	def msgType(self): return self._TYPE
	def key(self):     return self._CAT + self._TYPE

	def parse(self,line):
		self.header = Header()
		self.header.parse(line)
		self._parse(line)

	@abc.abstractmethod
	def _parse(self,line):
		pass

# #####################################################################
# Control Messages - consist of just a header
#    C I - Start Of Day
#    C J - End of Day
#    C O - Market Session Open
#    C C - Market Session Close
#    C K - End of Retransmission Requests
#    C Z - End of Transmissions
#    C T - Line Integrity
#    C L - Sequence Number Reset
#    C X - End of Trade Reporting
# #####################################################################
class _Control(_Message):
	"""Control messages consist of simply a header"""
	_CAT = "C"
	def _parse(self,line):
		pass

class Cntrl_StartOfDay(_Control):          _TYPE = "I"
class Cntrl_EndOfDay(_Control):            _TYPE = "J"
class Cntrl_MarketSessionOpen(_Control):   _TYPE = "O"
class Cntrl_MarketSessionClose(_Control):  _TYPE = "C"
class Cntrl_EndOfRetransReq(_Control):     _TYPE = "K"
class Cntrl_EndOfTrans(_Control):          _TYPE = "Z"
class Cntrl_LineIntegrity(_Control):       _TYPE = "T"
class Cntrl_SeqnoReset(_Control):          _TYPE = "L"
class Cntrl_EndOfTrades(_Control):         _TYPE = "X"

# #####################################################################
# Admin Messages
#    A A - General Administrative Message (Free-Form Text)
#    A 2 - Closing Trade Summary
#    A H - Trading Action (Security)
#    A M - Trading Action (Extraordinary Market)
# #####################################################################
class _Admin(_Message):
	_CAT = "A"

class Admin_GeneralAdmin(_Admin):
	_TYPE = "A"
	def _parse(self,line):
		self.text = line[HEADER:]
		
class Admin_ClosingTradeSummary(_Admin):
	_TYPE = "2"
	def _parse(self,line):
		(
		self.symbol,
		hiDenom,
		hiPrice,
		loDenom,
		loPrice,
		self.closeMktCntr,
		closeDenom,
		closePrice,
		netDenom,
		netPrice,
		netDirection,
		self.currency,
		self.totalVolume
		) = struct.unpack_from("14s1s12s1s12s1s1s12sx1s12s1s3s11s",line,HEADER_SIZE)

		self.hiPrice    = LongPrice(hiDenom,    hiPrice)
		self.loPrice    = LongPrice(loDenom,    loPrice)
		self.closePrice = LongPrice(closeDenom, closePrice)
		self.netPrice   = LongPrice(netDenom,   netPrice) 

class Admin_TradingAction(_Admin):
	_TYPE = "H"
	def _parse(self,line):
		(
		self.symbol,
		self.action,
		self.date,
		self.time,
		self.reason
		) = struct.unpack_from("14s1s8s9s6s",line,HEADER_SIZE)

class Admin_EMC(_Admin):
	_TYPE = "M"
	def _parse(self,line):
		(
		self.action,
		self.date,
		self.time,
		self.reason
		) = struct.unpack_from("1a8a9a6s",line,HEADER_SIZE)

# #####################################################################
# Trade Messages
#    T 5 - Short Form Trade
#    T 6 - Long  Form Trade
#    T 7 - Trade Cancel/Error
#    T 8 - Trade Correction
# #####################################################################
class _Trade(_Message):
	_CAT = "T"	
	def setEligibilities(self):
		self.eligible_hilo = True	
		self.eligible_last = True
		self.eligible_vol  = True
		(b1,b2,b3,b4) = struct.unpack("cccc", self.mod)

		if b1 != '@':
			self.eligible_hilo = False
			self.eligible_last = False

		if (b3 == 'Z') and (self.symbol in TDDS2.Statistics._last):
			self.elgible_last = False

		if (b3 == 'T') or (b3 == 'U'):
			self.eligible_hilo = False
			self.eligible_last = False

		if (b4 == 'I') or (b4 == 'W'):
			self.eligible_hilo = False
			self.eligible_last = False

		if (b4 == 'P') and (self.symbol in TDDS2.Statistics._last):
			self.elgible_last = False

class Trade_Short(_Trade):
	_TYPE = "5"
	def _parse(self,line):
		(
		self.symbol,
		self.mod,
		denom,
		price,
		self.volume,
		self.priceChangeInd
		) = struct.unpack_from("5s1s1s6s6s1s",line,HEADER_SIZE)

		self.symbol = self.symbol.strip()
		self.mod    = shortToLongModifier[self.mod]
		self.price  = ShortPrice(denom,price)
		self.volume = int(self.volume)
		self.asof = ' '

		self.setEligibilities()
		self.updated = TDDS2.Statistics.updateStats(self)

class Trade_Long(_Trade):
	_TYPE = "6"
	def _parse(self,line):
		(
		self.symbol,
		self.origDate,
		self.volume,
		denom,
		price,
		self.currency,
		self.asof,
		self.execDate,
		self.execTime,
		self.mod,
		self.sellersDays,
		self.priceChangeInd
		) = struct.unpack_from("14s8s8s1s12s3s1s8s9s4s2s1s",line,HEADER_SIZE)

		self.symbol = self.symbol.strip()
		self.price = LongPrice(denom,price)
		self.volume = int(self.volume)

		self.setEligibilities()
		self.updated = TDDS2.Statistics.updateStats(self)

class Trade_Cancel(_Trade):
	_TYPE = "7"
	def _parse(self,line):
		(
		self.symbol,
		self.origDate,
		self.origSeqno,
		self.function,
		self.volume,
		denom,
		price,
		self.currency,
		self.asof,
		self.execDate,
		self.execTime,
		self.mod,
		self.sellersDays,
		hiDenom,
		hiPrice,
		loDenom,
		loPrice,
		lastDenom,
		lastPrice,
		self.lastMktCntr,
		self.totalVolume,
		self.priceChangeInd
		) = struct.unpack_from("14s8s8s1s8s1s12s3s1s9s8s4s2s1s12s1s12s1s12s1s11s1s ", line, HEADER_SIZE)

		self.symbol      = self.symbol.rstrip()
		self.volume      = int(self.volume)
		self.price       = LongPrice(denom,price)
		self.hiPrice     = LongPrice(hiDenom,  hiPrice)
		self.loPrice     = LongPrice(loDenom,  loPrice)
		self.lastPrice   = LongPrice(lastDenom,lastPrice)
		self.totalVolume = int(self.totalVolume)

		if self.header.date == self.execDate:
			TDDS2.Statistics.setHigh(self.symbol, self.hiPrice)
			TDDS2.Statistics.setLo[self.symbol] = self.loPrice
			TDDS2.Statistics.setLast[self.symbol] = self.lastPrice
			TDDS2.Statistics.setLast_mktctr[self.symbol] = self.lastMktCntr
			TDDS2.Statistics.setVol[self.symbol] = self.totalVolume	

class Trade_Correct(_Trade):
	_TYPE = "8"
	def _parse(self,line):
		(
		self.symbol,
		self.origDate,
		self.origSeqno,
		self.function,
		self.origVolume,
		origDenom,
		origPrice,
		self.origCurrency,
		self.origAsof,
		self.origExecDate,
		self.origExecTime,
		self.origMod,
		self.origSellersDays,
		self.volume,
		denom,
		price,
		self.currency,
		self.asof,
		self.execDate,
		self.execTime,
		self.mod,
		self.sellersDays,
		hiDenom,
		hiPrice,
		loDenom,
		loPrice,
		lastDenom,
		lastPrice,
		self.lastMktCntr,
		self.totalVolume,
		self.priceChangeInd
		) = struct.unpack_from("14s8s8s1s8s1s12s3s1s8s9s4s2s8s1s12s3s1s8s9s4s2s1s12s1s12s1s12s1s11s1s",line,HEADER_SIZE)

		self.origPrice = LongPrice(origDenom, origPrice)
		self.price     = LongPrice(denom,     price)
		self.hiPrice   = LongPrice(hiDenom,   hiPrice)
		self.loPrice   = LongPrice(loDenom,   loPrice)
		self.lastPrice = LongPrice(lastDenom, lastPrice)

		self.setEligibilities()
		self.updated = TDDS2.Statistics.updateStats(self)

_msgFactory = {}
def _registerMessage(klass):
	key = klass._CAT + klass._TYPE
	_msgFactory[key] = klass
_registerMessage(Cntrl_StartOfDay)
_registerMessage(Cntrl_EndOfDay)
_registerMessage(Cntrl_MarketSessionOpen)
_registerMessage(Cntrl_MarketSessionClose)
_registerMessage(Cntrl_EndOfRetransReq)
_registerMessage(Cntrl_EndOfTrans)
_registerMessage(Cntrl_LineIntegrity)
_registerMessage(Cntrl_SeqnoReset)
_registerMessage(Cntrl_EndOfTrades)
_registerMessage(Trade_Short)
_registerMessage(Trade_Long)
_registerMessage(Trade_Cancel)
_registerMessage(Trade_Correct)
_registerMessage(Admin_GeneralAdmin)
_registerMessage(Admin_ClosingTradeSummary)
_registerMessage(Admin_TradingAction)
_registerMessage(Admin_EMC)

def createMessage(line):
	key = line[0:2]
	msg = None
	if key in _msgFactory:
		msg = _msgFactory[key]()
		msg.parse(line)
	return msg	
