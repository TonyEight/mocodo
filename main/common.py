#!/usr/bin/env python
# encoding: utf-8

import codecs
import time
import tables
import os

try:
	import json
except ImportError:
	import simplejson as json

version = "1.4.2"

class Common:
	
	def __init__(self, params):
		self.params = params
		s = os.path.splitext(self.params["output"])[0]
		self.params["baseOutputName"] = s[:s.rindex("-")]
	
	def timeStamp(self):
		return "Generated by Mocodo %s on %s" % (version,time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime()))
	
	def loadInputFile(self):
		encodings = (self.params["encoding"] if type(self.params["encoding"]) is list else [self.params["encoding"]])
		for encoding in encodings:
			try:
				self.encoding = encoding
				return codecs.open(self.params["input"],encoding=encoding).read().split("\n")
			except UnicodeDecodeError:
				pass
	
	def loadStyle(self):
		style = {}
		style.update(json.loads(codecs.open("colors/%s.json" % self.params["colors"],"r","utf8").read()))
		style.update(json.loads(codecs.open("shapes/%s.json" % self.params["shapes"],"r","utf8").read()))
		style.update({"attraction":self.params["attraction"]})
		return style
	
	def dumpOutputFile(self,result):
		codecs.open(self.params["output"],"w",encoding="utf8").write(result)
		print "Output file %s successfully generated." % self.params["output"]
	
	def dumpMldFiles(self, mcd):
		names = (self.params["table"] if type(self.params["table"]) is list else [self.params["table"]])
		mldFormats = []
		for name in names:
			try:
				mldFormats.append(json.loads(open("tables/%s.json" % name).read()))
			except:
				print "Problem with format %s" % name
		t = tables.Tables(mcd)
		try:
			t.processAll()
			for mldFormat in mldFormats:
				text = t.getText(mldFormat)
				name = "%s.%s" % (self.params["baseOutputName"],mldFormat["extension"])
				codecs.open(name,"w",encoding="utf8").write(text)
				print "Output file %s successfully generated." % name
		except:
			print "Problem during MLD generation."
	
	def prettyDict(self,name,l):
		if l:
			s = "%-"+str(max(len(k) for (k,_) in l)+3)+"s"
			return ["%s = {\n\t%s\n}" % (name,"\n\t".join(["%s: %s," % (s % ("u'%s'" % k),("%4d" % v if type(v) is int else ("% .2f" % v if type(v) is float else repr(v)))) for (k,v) in l]))]
		return []
	
	def dumpGeoFile(self,d):
		try:
			name = "%s-geo.json" % self.params["baseOutputName"]
			open(name,"w").write(json.dumps(d))
			print "Output file %s successfully generated." % name
		except IOError:
			print "Unable to generate file %s!" % name
	
	def processGeometry(self,mcd,style):
		l = [
			("size",(mcd.w,mcd.h)),
			("cx",[(box.name,box.x+box.w/2) for row in mcd.ordering for box in row]),
			("cy",[(box.name,box.y+box.h/2) for row in mcd.ordering for box in row]),
			("k",[(leg.identifier(),leg.value()) for row in mcd.ordering for box in row for leg in box.legs]),
			("t",[(leg.identifier(),0.5) for row in mcd.ordering for box in row for leg in box.legs if leg.arrow]),
			("colors",[((c,style[c]) if style[c] else (c,None)) for c in sorted(style.keys()) if c.endswith("Color")]),
		]
		if self.params["extract"]:
			self.dumpGeoFile(dict(l))
			result = ["""try:\n\timport json\nexcept ImportError:\n\timport simplejson as json\n\ngeo = json.loads(open("%s-geo.json").read())""" % self.params["baseOutputName"]]
			result.append("""(width,height) = geo.pop("size")""")
			result.append("""for (name,l) in geo.iteritems(): globals()[name] = dict(l)""")
		else:
			result = ["(width,height) = (%s,%s)" % l[0][1]]
			for (k,v) in l[1:]:
				result.extend(self.prettyDict(k,v))
		return result


		