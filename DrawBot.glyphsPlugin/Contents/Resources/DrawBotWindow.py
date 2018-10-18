#from __future__ import absolute_import

import AppKit
from vanilla import *
import vanilla.dialogs

from drawBot.ui.codeEditor import CodeEditor, OutPutEditor
from drawBot.ui.drawView import DrawView, ThumbnailView

from drawBot.scriptTools import ScriptRunner, CallbackRunner, StdOutput
#from drawBot.scriptTools import _Helper # for ScriptRunner
from drawBot.drawBotDrawingTools import _drawBotDrawingTool
from drawBot.context.drawBotContext import DrawBotContext
from drawBot.misc import getDefault, setDefault, warnings

from drawBot.ui.splitView import SplitView

from objc import super
from AppKit import NSWindowController, NSToolbarFlexibleSpaceItemIdentifier, NSToolbarSpaceItemIdentifier, NSContinuouslyUpdatesValueBindingOption, NSImage, NSString, NSShadow, NSFont, NSFontAttributeName, NSForegroundColorAttributeName, NSShadowAttributeName, NSDocumentController, NSBezierPath

from Foundation import NSUserDefaults

from objectsGS import CurrentFont, CurrentGlyph
from GlyphsApp import GetSaveFile

import sys, os
import traceback

from drawBot.context.baseContext import BezierPath

sys.path.append(os.path.dirname(__file__))

def drawGlyph(glyph):
	BezierPath = glyph._layer.bezierPath
	if BezierPath != None:
		BezierPath = BezierPath.copy()
	else:
		BezierPath = NSBezierPath.bezierPath()
	OpenBezierPath = glyph._layer.openBezierPath
	if OpenBezierPath:
		BezierPath.appendBezierPath_(OpenBezierPath)
	for currComponent in glyph._layer.components:
		BezierPath.appendBezierPath_(currComponent.bezierPath)
	_drawBotDrawingTool.drawPath(BezierPath)

_drawBotDrawingTool.drawGlyph = drawGlyph

class GSBezierPathDraw(BezierPath):

	def addGlyph(self, glyph):
		BezierPath = glyph._layer.bezierPath()
		if BezierPath != None:
			BezierPath = BezierPath.copy()
		else:
			BezierPath = NSBezierPath.bezierPath()
		for currComponent in glyph._layer.components:
			BezierPath.appendBezierPath_(currComponent.bezierPath())
		self.getNSBezierPath().appendBezierPath_(BezierPath)

_drawBotDrawingTool._bezierPathClass = GSBezierPathDraw

class GlyphsDrawBotController(NSWindowController):

	"""
	The controller for a DrawBot window.
	"""

	windowAutoSaveName = "DrawBotController"

	def init(self):
		self = super(GlyphsDrawBotController, self).init()
		document = None
		#print "GlyphsDrawBotController.init"
		# make a window
		self.w = Window((400, 400), "DrawBot", minSize=(200, 200), textured=False)
		# setting previously stored frames, if any
		self.w.getNSWindow().setFrameUsingName_(self.windowAutoSaveName)
		_NSWindow = self.w.getNSWindow()
		self.setWindow_(_NSWindow)
		_NSWindow.setDelegate_(self)
		_NSWindow.setContentBorderThickness_forEdge_(27, 1)
		try:
			# on 10.7+ full screen support
			self.w.getNSWindow().setCollectionBehavior_(128)  # NSWindowCollectionBehaviorFullScreenPrimary
		except:
			pass

		# the code editor
		self.codeView = CodeEditor((0, 0, -0, -0))
		self.codeView.getNSTextView().bind_toObject_withKeyPath_options_("value", self, "document.text", {NSContinuouslyUpdatesValueBindingOption:True})
		scrollview = self.codeView.getNSTextView().enclosingScrollView()
		scrollview.setBorderType_(0)
		
		# the output view (will catch all stdout and stderr)
		self.outPutView = OutPutEditor((0, 0, -0, -0), readOnly=True)
		scrollview = self.outPutView.getNSTextView().enclosingScrollView()
		scrollview.setBorderType_(0)
		
		# the view to draw in
		self.drawView = DrawView((0, 0, -0, -0))
		pdfView = self.drawView.getNSView()
		view = pdfView.documentView()
		# the view with all thumbnails
		self.thumbnails = ThumbnailView((0, 0, -0, -0))
		# connect the thumbnail view with the draw view
		self.thumbnails.setDrawView(self.drawView)

		# collect all code text view in a splitview
		paneDescriptors = [
			dict(view=self.codeView, identifier="codeView", minSize=50, canCollapse=False),
			dict(view=self.outPutView, identifier="outPutView", size=100, minSize=50, canCollapse=False),
		]
		self.codeSplit = SplitView((0, 0, -0, -0), paneDescriptors, isVertical=False)

		# collect the draw scroll view and the code split view in a splitview
		paneDescriptors = [
			dict(view=self.thumbnails, identifier="thumbnails", minSize=100, size=100, maxSize=100),
			dict(view=self.drawView, identifier="drawView", minSize=50),
			dict(view=self.codeSplit, identifier="codeSplit", minSize=50, canCollapse=False),
		]
		self.w.split = SplitView((0, 0, -0, -27), paneDescriptors)
		
		self.w.runButton = Button((-67, -24, 50, 20), "Run", callback=self.runButtonAction)
		self.w.runButton.bind("\r", ["command"])
		self.w.runButton._nsObject.setToolTip_(u"Run the script (cmd+\u23CE)")
		
		self.w.clearButton = Button((-135, -24, 58, 20), "Clear", callback=self.clearButtonAction)
		self.w.clearButton.bind("k", ["command"])
		self.w.clearButton._nsObject.setToolTip_(u"Clear Log (cmd+K)")
		
		# get the real size of the window
		windowX, windowY, windowWidth, windowHeight = self.w.getPosSize()
		# set the split view dividers at a specific position based on the window size
		self.w.split.setDividerPosition(0, 0)
		self.w.split.setDividerPosition(1, windowWidth * .6)
		self.w.split.setDividerPosition(1, windowWidth * .6)
		self.codeSplit.setDividerPosition(0, windowHeight * .7)
		
		return self

	def __del__(self):
		self.codeView.getNSTextView().unbind_("value")
	
	def runCode(self, liveCoding=False):
		# get the code
		try:
			code = self.code()
			#print "__runCode 1", code
			# get the path of the document (will be None for an untitled document)
			path = None
			try:
				path = self.document().fileURL().path()
			except:
				pass
			#print "__runCode 2", path
			# reset the internal warning system
			warnings.resetWarnings()
			# reset the drawing tool
			_drawBotDrawingTool.newDrawing()
			# create a namespace
			namespace = {} # DrawBotNamespace(_drawBotDrawingTool, _drawBotDrawingTool._magicVariables)
			# add the tool callbacks in the name space
			_drawBotDrawingTool._addToNamespace(namespace)
			# when enabled clear the output text view
			if getDefault("DrawBotClearOutput", True):
				self.outPutView.clear()
			# create a new std output, catching all print statements and tracebacks
			self.output = []
	
			liveOutput = None
			#if getDefault("DrawButLiveUpdateStdoutStderr", False):
			liveOutput = self.outPutView
			
			self.stdout = StdOutput(self.output, outputView=liveOutput)
			self.stderr = StdOutput(self.output, isError=True, outputView=liveOutput)
			sys.argv = [path]
			# warnings should show the warnings
			warnings.shouldShowWarnings = True
			# run the code
			ScriptRunner(code, path, namespace=namespace, stdout=self.stdout, stderr=self.stderr)
			# warnings should stop posting them
			warnings.shouldShowWarnings = False
			# set context, only when the panes are visible
			#print "__set context"
			if self.w.split.isPaneVisible("drawView") or self.w.split.isPaneVisible("thumbnails"):
				#print "__drawView"
				def createContext(context):
					# draw the tool in to the context
					_drawBotDrawingTool._drawInContext(context)
				# create a context to draw in
				context = DrawBotContext()
				# savely run the callback and track all traceback back to the output
				CallbackRunner(createContext, stdout=self.stdout, stderr=self.stderr, args=[context])
				# get the pdf document and set in the draw view
				pdfDocument = context.getNSPDFDocument()
				selectionIndex = self.thumbnails.getSelection()
				if not liveCoding or (pdfDocument and pdfDocument.pageCount()):
					self.drawView.setPDFDocument(pdfDocument)
				# scroll to the original position
				self.drawView.scrollToPageIndex(selectionIndex)
			else:
				#print "__setPDF"
				# if the panes are not visible, clear the draw view
				self.drawView.setPDFDocument(None)
			# drawing is done
			_drawBotDrawingTool.endDrawing()
			# set the catched print statements and tracebacks in the the output text view
			for text, isError in self.output:
				if liveCoding and isError:
					continue
				self.outPutView.append(text, isError)

			# reset the code backup if the script runs with any crashes
			#setDefault("pythonCodeBackup", None)
			# clean up

			self.output = None
			self.stdout = None
			self.stderr = None
		except Exception, e:
			print "-- Error", e
			print(traceback.format_exc())
			print "-- Error/"

	def checkSyntax(self, sender=None):
		# get the code
		code = self.code()
		# get te path of the document (will be None for an untitled document)
		path = self.path()
		# when enabled clear the output text view
		if getDefault("DrawBotClearOutput", True):
			self.outPutView.set("")
		# create a new std output, catching all print statements and tracebacks
		self.output = []
		self.stdout = StdOutput(self.output)
		self.stderr = StdOutput(self.output, True)
		# run the code, but with the optional flag checkSyntaxOnly so it will just compile the code
		ScriptRunner(code, path, stdout=self.stdout, stderr=self.stderr, checkSyntaxOnly=True)
		# set the catched print statements and tracebacks in the the output text view
		for text, isError in self.output:
			self.outPutView.append(text, isError)
		# clean up
		self.output = None
		self.stdout = None
		self.stderr = None

	def _savePDF(self, path):
		#print "__savePDF path", path
		# get the pdf date from the draw view
		data = self.drawView.get()
		if data:
			# if there is date save it
			data.writeToFile_atomically_(path, False)

	def savePDF(self, sender=None):
		"""
		Save the content as a pdf.
		"""
		# pop up a show put file sheet
		vanilla.dialogs.putFile(fileTypes=["pdf"], parentWindow=self.window(), resultCallback=self._savePDF)
		
	def code(self):
		"""
		Returns the content of the code view as a string.
		"""
		return self.document().text

	def setCode(self, code):
		"""
		Sets code in to the code view.
		"""
		assert(False)
		self.document().setText_(code)

	def pdfData(self):
		"""
		Returns the pdf data from the draw view
		"""
		return self.drawView.get()
	
	def set(self, path, force=False):
		self.setPath(path)
	def assignToDocument(self, nsDocument):
		# assing the window to the document
		self.w.assignToDocument(nsDocument)
	
	# responders
	
	def runButtonAction(self, sender):
		self.runCode()
	
	def clearButtonAction(self, sender):
		self.outPutView.clear()
	
	def commentSelection_(self, sender):
		self.codeView.comment()
		
	def toolbarUncomment(self, sender):
		self.codeView.uncomment()
	
	def shiftSelectedLinesRight_(self, sender):
		self.codeView.indent()
	
	def shiftSelectedLinesLeft_(self, sender):
		self.codeView.dedent()
	
	def toolbarReload(self, sender):
		self.codeView.reload()
	
	def exportFont_(self, sender):
		#print "__self.savePDF()"
		self.savePDF()
