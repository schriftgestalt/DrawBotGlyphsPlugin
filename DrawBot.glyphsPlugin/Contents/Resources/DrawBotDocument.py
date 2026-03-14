from __future__ import print_function
import objc
import sys
import os
from objc import super

from Foundation import NSString, NSUTF8StringEncoding, NSData
from AppKit import NSDocumentController, NSDocument

from GlyphsApp import Glyphs, FILE_MENU, NSMenuItem
from GlyphsApp.plugins import GeneralPlugin


class DrawBotPlugin(GeneralPlugin):

	@objc.python_method
	def settings(self):
		self.name = Glyphs.localize({'en': 'DrawBot'})

	@objc.python_method
	def start(self):
		newMenuItem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("New Drawbot", self.newDocument_, "")
		newMenuItem.setTarget_(self)
		Glyphs.menu[FILE_MENU].insert(1, newMenuItem)
		sys.path.append(os.path.dirname(__file__))

	def newDocument_(self, sender):
		newDoc = DrawBotDocument.new()
		NSDocumentController.sharedDocumentController().addDocument_(newDoc)
		newDoc.makeWindowControllers()
		newDoc.showWindows()


class DrawBotDocument(NSDocument):

	def init(self):
		"""
		You can add an observer like in the example.
		Do all initializing here.
		"""
		self = super().init()
		self._text = ""
		return self

	def text(self):
		return self._text

	def setText_(self, text):
		self._text = text

	def makeWindowControllers(self):
		from DrawBotWindow import GlyphsDrawBotController
		WindowController = GlyphsDrawBotController.alloc().init()
		self.addWindowController_(WindowController)

	def windowController(self):
		return self.windowControllers()[0]

	# def __del__(self):
	# 	"""
	# 	Remove all observers you added in init().
	# 	"""
	# 	pass

	def dataRepresentationOfType_(self, aType):
		if self._text and len(self._text) > 0:
			return NSString.stringWithString_(self._text).dataUsingEncoding_(NSUTF8StringEncoding)
		else:
			NSData.data()

	def loadDataRepresentation_ofType_(self, data, aType):
		self.setText_(NSString.alloc().initWithData_encoding_(data, NSUTF8StringEncoding))
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
