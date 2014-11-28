#!/usr/bin/env python
import struct

HEADER_SIZE = 32
PRICECHANGEIND_LAST = 1
PRICECHANGEIND_LO   = 2
PRICECHANGEIND_HIGH = 4
LATEMILLIS = 10000

shortPriceFormat = {
	'A' : "5s1s",
	'B' : "4s2s",
	'C' : "3s3s",
	'D' : "2s4s",
	'E' : "1s5s",
	'F' : "0s5s"
	 };

longPriceFormat = {
	'A' : "11s1s",
	'B' : "10s2s",
	'C' : "9s3s",
	'D' : "8s4s",
	'E' : "7s5s",
	'F' : "6s6s",
	'G' : "5s7s",
	'H' : "4s8s",
	'I' : "12s0s"
	}

shortToLongModifier = {
	'@' : '@   ',
	'C' : 'C   ',
	'N' : 'N   ',
	'T' : '@ T ',
	'U' : '@ U ',
	'Z' : '@ Z ',
	'I' : '@  I',
	'P' : '@  P',
	'W' : '@  W',
	}

def HHMMSSmmm2Millis(HHMMSSmmm):
	(HH,MM,SS,mmm) = struct.unpack("2s2s2s3s",HHMMSSmmm)
	return int(mmm) + 1000 * ( int(SS) + 60*int(MM) + 3600*int(HH) )

PREOPEN_TIME  = HHMMSSmmm2Millis("080000000")
PREOPEN_GRACE = HHMMSSmmm2Millis("081500000")

def ShortPrice(denom,price):
	(dol,cents) = struct.unpack( shortPriceFormat[denom], price)
	return float( "%s.%s" % (dol,cents) )

def LongPrice(denom,price):
	(dol,cents) = struct.unpack( longPriceFormat[denom], price)
	return float( "%s.%s" % (dol,cents) )

