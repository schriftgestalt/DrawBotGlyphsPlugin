#!/usr/bin/env python
# encoding: utf-8

import objc
import sys, os, re
from objc import super

from Foundation import NSLog, NSString, NSUTF8StringEncoding
from AppKit import NSApplication, NSDocumentController, NSDocument, NSMenuItem

GlyphsPluginProtocol = objc.protocolNamed("GlyphsPlugin")


	def init(self):
		"""
		You can add an observer like in the example.
		Do all initializing here.
		"""
		self = super(DrawBotDocument, self).init()
		self.text = ""
		return self
	
	def loadPlugin(self):
		mainMenu = NSApplication.sharedApplication().mainMenu()
		s = objc.selector(self.newDocument, signature='v@:')
		newMenuItem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("New Drawbot", s, "")
		newMenuItem.setTarget_(self)
		mainMenu.itemAtIndex_(1).submenu().insertItem_atIndex_(newMenuItem, 1)
	
	def makeWindowControllers(self):
		from DrawBotWindow import GlyphsDrawBotController
		WindowController = GlyphsDrawBotController.alloc().init()
		self.addWindowController_(WindowController)
		
	def newDocument(self):
		newDoc = DrawBotDocument.alloc().init()
		NSDocumentController.sharedDocumentController().addDocument_(newDoc)
		newDoc.makeWindowControllers()
		newDoc.showWindows()
	
	def windowController(self):
		return self.windowControllers()[0]
	
	# def __del__(self):
	# 	"""
	# 	Remove all observers you added in init().
	# 	"""
	# 	pass
	
	def title(self):
		return "DrawBot"
	
	def interfaceVersion(self):
		"""
		Distinguishes the API version the plugin was built for. 
		Return 1.
		"""
		return 1

	def dataRepresentationOfType_(self, aType):
		if len(self.text) > 0:
			return NSString.stringWithString_(self.text).dataUsingEncoding_(NSUTF8StringEncoding)
		else:
			NSdata.data()
	
	def loadDataRepresentation_ofType_(self, data, aType):
		self.text = NSString.alloc().initWithData_encoding_(data, NSUTF8StringEncoding)
		return True
	
	def writableTypes(self):
		return ["public.python-script"]
	
	def isNativeType_(self, aType):
		return "public.python-script" == aType
		
	def autosavesInPlace(self):
		return False
	
	def autosavesDrafts(self):
		return True
	
	def font(self):
		return None
