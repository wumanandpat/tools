#!/usr/bin/env python
import sys
import fileinput
import TDDS2.Message
import TDDS2.Validator

if __name__ == "__main__":
	validator = TDDS2.Validator.Validator()
	validator.loadMpv("odd_roundlots.txt")

	for line in fileinput.input():
		line = line.rstrip("\n")
		msg = TDDS2.Message.createMessage(line)
		
		if not validator.isValid(msg):
			print "[%s] %s" % (line,validator.error)
