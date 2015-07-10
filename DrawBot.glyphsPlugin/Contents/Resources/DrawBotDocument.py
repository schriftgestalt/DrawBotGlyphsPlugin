#!/usr/bin/env python
# encoding: utf-8

import objc
from Foundation import *
from AppKit import *
import sys, os, re

from DrawBotWindow import GlyphsDrawBotController

MainBundle = NSBundle.mainBundle()
path = MainBundle.bundlePath() + "/Contents/Scripts"
if not path in sys.path:
	sys.path.append( path )

import GlyphsApp

GlyphsPluginProtocol = objc.protocolNamed( "GlyphsPlugin" )

class DrawBotDocument ( NSDocument, GlyphsPluginProtocol ):
	
	def init( self ):
		"""
		You can add an observer like in the example.
		Do all initializing here.
		"""
		self.text = ""
		self = super(DrawBotDocument, self).init()
		return self
	
	def loadPlugin(self):
		mainMenu = NSApplication.sharedApplication().mainMenu()
		s = objc.selector(self.newDocument,signature='v@:')
		newMenuItem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("New Drawbot", s, "" )
		newMenuItem.setTarget_(self)
		mainMenu.itemAtIndex_(1).submenu().insertItem_atIndex_(newMenuItem, 1)
	
	def makeWindowControllers(self):
		WindowController = GlyphsDrawBotController.alloc().init()
		self.addWindowController_(WindowController)
		
	def newDocument(self):
		newDoc = NSDocumentController.sharedDocumentController().makeUntitledDocumentOfType_error_("public.python-script", None)
		newDoc = newDoc[0]
		NSDocumentController.sharedDocumentController().addDocument_(newDoc)
		newDoc.makeWindowControllers()
		newDoc.showWindows()
	
	def windowController(self):
		return self.windowControllers()[0]
	
	def __del__(self):
		"""
		Remove all observers you added in init().
		"""
	
	def title(self):
		return "DrawBot"
	
	def interfaceVersion(self):
		"""
		Distinguishes the API version the plugin was built for. 
		Return 1.
		"""
		try:
			return 1
		except Exception as e:
			self.logToConsole( "interfaceVersion: %s" % str(e) )
	
	def logToConsole(self, message):
		"""
		The variable 'message' will be passed to Console.app.
		Use self.logToConsole( "bla bla" ) for debugging.
		"""
		myLog = "%s:\n%s" % ( self.__class__.__name__, message )
		NSLog( myLog )
	
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
