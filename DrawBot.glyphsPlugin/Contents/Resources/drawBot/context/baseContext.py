import AppKit
import CoreText
import Quartz

from drawBot.misc import DrawBotError, cmyk2rgb, warnings

from tools import openType

_FALLBACKFONT = "LucidaGrande"

class BezierPath(object):

    """
    A bezier path object, if you want to draw the same over and over again.
    """

    def __init__(self, path=None):
        if path is None:
            self._path = AppKit.NSBezierPath.bezierPath()
        else:
            self._path = path

    def __repr__(self):
        return "<BezierPath>"

    def moveTo(self, x, y=None):
        """
        Move to a point `x`, `y`.
        """
        if y is None:
            x, y = x
        self._path.moveToPoint_((x, y))

    moveto = moveTo

    def lineTo(self, x, y=None):
        """
        Line to a point `x`, `y`.
        """
        if y is None:
            x, y = x
        self._path.lineToPoint_((x, y))

    lineto = lineTo

    def curveTo(self, x1, y1, x2, y2=None, x3=None, y3=None):
        """
        Curve to a point `x3`, `y3`.
        With given bezier handles `x1`, `y1` and `x2`, `y2`.
        """
        if y2 is None and x3 is None and y3 is None:
            x3, y3 = x2
            x2, y2 = y1
            x1, y1 = x1
        self._path.curveToPoint_controlPoint1_controlPoint2_((x3, y3), (x1, y1), (x2, y2))

    curveto = curveTo

    def arcTo(self, pt1, pt2, radius):
        """
        Arc from one point to an other point with a given `radius`.
        """
        self._path.appendBezierPathWithArcFromPoint_toPoint_radius_(pt1, pt2, radius)

    def closePath(self):
        """
        Close the path.
        """
        self._path.closePath()

    closepath = closePath

    def rect(self, x, y, w, h):
        """
        Add a rectangle at possition `x`, `y` with a size of `w`, `h`
        """
        self._path.appendBezierPathWithRect_(((x, y), (w, h)))

    def oval(self, x, y, w, h):
        """
        Add a oval at possition `x`, `y` with a size of `w`, `h`
        """
        self._path.appendBezierPathWithOvalInRect_(((x, y), (w, h)))

    def text(self, txt, font=_FALLBACKFONT, fontSize=10, offset=None, box=None):
        """
        Draws a `txt` with a `font` and `fontSize` at an `offset` in the bezier path.

        Optionally `txt` can be a `FormattedString` and be drawn inside a `box`, a tuple of (x, y, width, height).
        """
        try:
            txt = txt.decode("utf-8")
        except:
            pass
        if isinstance(txt, FormattedString):
            attributedString = txt.getNSObject()
        else:
            fontName = font
            font = AppKit.NSFont.fontWithName_size_(font, fontSize)
            if font is None:
                warnings.warn("font: %s is not installed, back to the fallback font: %s" % (fontName, _FALLBACKFONT))
                font = AppKit.NSFont.fontWithName_size_(_FALLBACKFONT, fontSize)

            attributes = {
                AppKit.NSFontAttributeName : font
            }
            attributedString = AppKit.NSAttributedString.alloc().initWithString_attributes_(txt, attributes)
        w, h = attributedString.size()
        setter = CoreText.CTFramesetterCreateWithAttributedString(attributedString)
        path = Quartz.CGPathCreateMutable()
        if offset:
            x, y = offset
        else:
            x = y = 0
        if box:
            bx, by, w, h = box
            x += bx
            y += by
            Quartz.CGPathAddRect(path, None, Quartz.CGRectMake(0, 0, w, h))
        else:
            Quartz.CGPathAddRect(path, None, Quartz.CGRectMake(0, -h, w*2, h*2))
        box = CoreText.CTFramesetterCreateFrame(setter, (0, 0), path, None)
        ctLines = CoreText.CTFrameGetLines(box)
        origins = CoreText.CTFrameGetLineOrigins(box, (0, len(ctLines)), None)
        
        if origins and box is not None:
            x -= origins[-1][0]
            y -= origins[-1][1]
        for i, (originX, originY) in enumerate(origins):
            ctLine = ctLines[i]
            ctRuns = CoreText.CTLineGetGlyphRuns(ctLine)
            for ctRun in ctRuns:
                attributes = CoreText.CTRunGetAttributes(ctRun)
                font = attributes.get(AppKit.NSFontAttributeName)
                glyphCount = CoreText.CTRunGetGlyphCount(ctRun)
                for i in range(glyphCount):
                    glyph = CoreText.CTRunGetGlyphs(ctRun, (i, 1), None)[0]
                    ax, ay = CoreText.CTRunGetPositions(ctRun, (i, 1), None)[0]
                    if glyph:
                        self._path.moveToPoint_((x+originX+ax, y+originY+ay))
                        self._path.appendBezierPathWithGlyph_inFont_(glyph, font)
        self.optimizePath()

    def getNSBezierPath(self):
        """
        Return the nsBezierPath.
        """
        return self._path

    def setNSBezierPath(self, path):
        """
        Set a nsBezierPath.
        """
        self._path = path

    def pointInside(self, (x, y)):
        """
        Check if a point `x`, `y` is inside a path.
        """
        return self._path.containsPoint_((x, y))

    def bounds(self):
        """
        Return the bounding box of the path.
        """
        if self._path.isEmpty():
            return None
        (x, y), (w, h) = self._path.bounds()
        return x, y, x+w, y+h

    def controlPointBounds(self):
        """
        Return the bounding box of the path including the offcurve points.
        """
        (x, y), (w, h) = self._path.controlPointBounds()
        return x, y, x+w, y+h

    def _points(self, onCurve=True, offCurve=True):
        points = []
        if not onCurve and not offCurve:
            return points
        for index in range(self._path.elementCount()):
            instruction, pts = self._path.elementAtIndex_associatedPoints_(index)
            if not onCurve:
                pts = pts[:-1]
            elif not offCurve:
                pts = pts[-1:]
            points.extend([(p.x, p.y) for p in pts])
        return points

    def _get_points(self):
        return self._points()

    points = property(_get_points, doc="Return a list of all points.")

    def _get_onCurvePoints(self):
        return self._points(offCurve=False)

    onCurvePoints = property(_get_onCurvePoints, doc="Return a list of all on curve points.")

    def _get_offCurvePoints(self):
        return self._points(onCurve=False)

    offCurvePoints = property(_get_offCurvePoints, doc="Return a list of all off curve points.")

    def _get_contours(self):
        contours = []
        for index in range(self._path.elementCount()):
            instruction, pts = self._path.elementAtIndex_associatedPoints_(index)
            if instruction == 0:
                contours.append([])
            if pts:
                contours[-1].append([(p.x, p.y) for p in pts])
        if len(contours) >= 2 and len(contours[-1]) == 1 and contours[-1][0] == contours[-2][0]:
            contours.pop()
        return contours

    contours = property(_get_contours, doc="Return a list of contours with all point coordinates sorted in segments.")

    def optimizePath(self):
        count = self._path.elementCount()
        if self._path.elementAtIndex_(count-1) == AppKit.NSMoveToBezierPathElement:
            optimizedPath = AppKit.NSBezierPath.bezierPath()
            for i in range(count-1):
                instruction, points = self._path.elementAtIndex_associatedPoints_(i)
                if instruction == AppKit.NSMoveToBezierPathElement:
                    optimizedPath.moveToPoint_(*points)
                elif instruction == AppKit.NSLineToBezierPathElement:
                    optimizedPath.lineToPoint_(*points)
                elif instruction == AppKit.NSCurveToBezierPathElement:
                    p1, p2, p3 = points
                    optimizedPath.curveToPoint_controlPoint1_controlPoint2_(p3, p1, p2)
                elif instruction == AppKit.NSClosePathBezierPathElement:
                    optimizedPath.closePath()
            self._path = optimizedPath

    def copy(self):
        """
        Copy the bezier path.
        """
        new = self.__class__()
        new._path = self._path.copy()
        return new

class Color(object):

    def __init__(self, r=None, g=None, b=None, a=1):
        if r is None:
            return
        if isinstance(r, AppKit.NSColor):
            self._color = r.colorUsingColorSpaceName_("NSCalibratedRGBColorSpace")
        elif g == None and b == None:
            self._color = AppKit.NSColor.colorWithCalibratedRed_green_blue_alpha_(r, r, r, a)
        elif b == None:
            self._color = AppKit.NSColor.colorWithCalibratedRed_green_blue_alpha_(r, r, r, g)
        else:
            self._color = AppKit.NSColor.colorWithCalibratedRed_green_blue_alpha_(r, g, b, a)

    def set(self):
        self._color.set()

    def setStroke(self):
        self._color.setStroke()

    def getNSObject(self):
        return self._color

    def copy(self):
        new = self.__class__()
        new._color = self._color.copy()
        return new

    @classmethod
    def getColorsFromList(self, inputColors):
        outputColors = []
        for color in inputColors:
            color = self.getColor(color)
            outputColors.append(color)
        return outputColors

    @classmethod
    def getColor(self, color):
        if isinstance(color, (tuple, list)):
            return self(*color)
        elif isinstance(color, AppKit.NSColor):
            return self(color)
        raise DrawBotError, "Not a valid color: %s" % color


class CMYKColor(Color):

    def __init__(self, c=None, m=None, y=None, k=None, a=1):
        if c is None:
            return
        if isinstance(c, AppKit.NSColor):
            self._color = c.colorUsingColorSpaceName_("NSDeviceCMYKColorSpace")
        else:
            self._color = AppKit.NSColor.colorWithDeviceCyan_magenta_yellow_black_alpha_(c, m, y, k, a)

class Shadow(object):

    _colorClass = Color

    def __init__(self, offset=None, blur=None, color=None):
        if offset is None:
            return
        self.offset = offset
        self.blur = blur
        self.color = self._colorClass.getColor(color)
        self.cmykColor = None

    def copy(self):
        new = self.__class__()
        new.offset = self.offset
        new.blur = self.blur
        new.color = self.color.copy()
        new.cmykColor = None
        if self.cmykColor:
            new.cmykColor = self.cmykColor.copy()
        return new

class Gradient(object):

    _colorClass = Color

    def __init__(self, gradientType=None, start=None, end=None, colors=None, positions=None, startRadius=None, endRadius=None):
        if gradientType is None:
            return
        if gradientType not in ("linear", "radial"):
            raise DrawBotError, "Gradient type must be either line or circle"
        if not colors or len(colors) < 2:
            raise DrawBotError, "Gradient needs at least 2 colors"
        if positions is None:
            positions = [i / float(len(colors)-1) for i in range(len(colors))]
        if len(colors) != len(positions):
            raise DrawBotError, "Gradient needs a correct position for each color"
        self.gradientType = gradientType
        self.colors = self._colorClass.getColorsFromList(colors)
        self.cmykColors = None
        self.positions = positions
        self.start = start
        self.end = end
        self.startRadius = startRadius
        self.endRadius = endRadius

    def copy(self):
        new = self.__class__()
        new.gradientType = self.gradientType
        new.colors = [color.copy() for color in self.colors]
        new.cmykColors = None
        if self.cmykColors:
            new.cmykColors = [color.copy() for color in self.cmykColors]
        new.positions = list(self.positions)
        new.start = self.start
        new.end = self.end
        new.startRadius = self.startRadius
        new.endRadius = self.endRadius
        return new

class FormattedString(object):

    _colorClass = Color
    _cmykColorClass = CMYKColor

    _textAlignMap = dict(
        center=AppKit.NSCenterTextAlignment,
        left=AppKit.NSLeftTextAlignment,
        right=AppKit.NSRightTextAlignment,
        justified=AppKit.NSJustifiedTextAlignment,
        )

    """
    A formatted string object, if you want to draw the same over and over again.
    FormattedString objects can be drawn with the `text(txt, (x, y))` and `textBox(txt, (x, y, w, h))` methods.
    """

    def __init__(self, txt=None,
                        font=None, fontSize=10, fallbackFont=None,
                        fill=(0, 0, 0), cmykFill=None,
                        stroke=None, cmykStroke=None, strokeWidth=1,
                        align=None, lineHeight=None, tracking=None,
                        openTypeFeatures=None):
        self._attributedString = AppKit.NSMutableAttributedString.alloc().init()
        self._font = font
        self._fontSize = fontSize
        self._fill = fill
        self._cmykFill = cmykFill
        self._stroke = stroke
        self._cmykStroke = cmykStroke
        self._strokeWidth = strokeWidth
        self._align = align
        self._lineHeight = lineHeight
        self._tracking = tracking
        self._fallbackFont = fallbackFont
        if openTypeFeatures is None:
            openTypeFeatures = dict()
        self._openTypeFeatures = openTypeFeatures
        if txt:
            self.append(txt, font=font, fontSize=fontSize, fallbackFont=fallbackFont,
                        fill=fill, cmykFill=cmykFill,
                        stroke=stroke, cmykStroke=cmykStroke, strokeWidth=strokeWidth,
                        align=align, lineHeight=lineHeight,
                        openTypeFeatures=openTypeFeatures)

    def append(self, txt,
                    font=None, fallbackFont=None, fontSize=None,
                    fill=None, cmykFill=None,
                    stroke=None, cmykStroke=None, strokeWidth=None,
                    align=None, lineHeight=None, tracking=None,
                    openTypeFeatures=None):
        """
        Add `txt` to the formatted string with some additional text formatting attributes:

        * `font`: the font to be used for the given text
        * `fallbackFont`: the fallback font
        * `fontSize`: the font size to be used for the given text
        * `fill`: the fill color to be used for the given text
        * `cmykFill`: the cmyk fill color to be used for the given text
        * `stroke`: the stroke color to be used for the given text
        * `cmykStroke`: the cmyk stroke color to be used for the given text
        * `strokeWidth`: the strokeWidth to be used for the given text
        * `align`: the alignment to be used for the given text
        * `lineHeight`: the lineHeight to be used for the given text
        * `openTypeFeatures`: enable OpenType features

        All formatting attributes follow the same notation as other similar DrawBot methods.
        A color is a tuple of `(r, g, b, alpha)`, and a cmykColor is a tuple of `(c, m, y, k, alpha)`.

        Text can also be added with `formattedString += "hello"`. It will append the text with the current settings of the formatted string.
        """
        try:
            txt = txt.decode("utf-8")
        except:
            pass
        if font is None:
            font = self._font
        else:
            self._font = font

        if fallbackFont is None:
            fallbackFont = self._fallbackFont
        else:
            self._fallbackFont = fallbackFont

        if fontSize is None:
            fontSize = self._fontSize
        else:
            self._fontSize = fontSize

        if fill is None and cmykFill is None:
            fill = self._fill
            cmykFill = self._cmykFill
        elif fill is not None:
            self._fill = fill
            self._cmykFill = None
        elif cmykFill is not None:
            self._cmykFill = cmykFill
            self._fill = None

        if stroke is None and cmykStroke is None:
            stroke = self._stroke
            cmykStroke = self._cmykStroke
        elif stroke is not None:
            self._stroke = stroke
            self._cmykStroke = None
        elif cmykStroke is not None:
            self._cmykStroke = cmykStroke
            self._stroke = None

        if strokeWidth is None:
            strokeWidth = self._strokeWidth
        else:
            self._strokeWidth = strokeWidth

        if align is None:
            align = self._align
        else:
            self._align = align

        if lineHeight is None:
            lineHeight = self._lineHeight
        else:
            self._lineHeight = lineHeight

        if tracking is None:
            tracking = self._tracking
        else:
            self._tracking = tracking

        if openTypeFeatures is None:
            openTypeFeatures = self._openTypeFeatures
        else:
            self._openTypeFeatures = openTypeFeatures

        if isinstance(txt, FormattedString):
            self._attributedString.appendAttributedString_(txt.getNSObject())
            return
        attributes = {}
        if font:
            fontName = font
            font = AppKit.NSFont.fontWithName_size_(fontName, fontSize)
            if font is None:
                ff = fallbackFont
                if ff is None:
                    ff = _FALLBACKFONT
                warnings.warn("font: %s is not installed, back to the fallback font: %s" % (fontName, ff))
                font = AppKit.NSFont.fontWithName_size_(ff, fontSize)
            coreTextfeatures = []
            for featureTag, value in openTypeFeatures.items():
                if not value:
                    featureTag = "%s_off" % featureTag
                if featureTag in openType.featureMap:
                    feature = openType.featureMap[featureTag]
                    coreTextfeatures.append(feature)
            fontDescriptor = font.fontDescriptor()
            fontAttributes = {
                CoreText.NSFontFeatureSettingsAttribute : coreTextfeatures,
                }
            if fallbackFont:
                fontAttributes[CoreText.NSFontCascadeListAttribute] = [AppKit.NSFontDescriptor.fontDescriptorWithName_size_(fallbackFont, fontSize)]
            fontDescriptor = fontDescriptor.fontDescriptorByAddingAttributes_(fontAttributes)
            font = AppKit.NSFont.fontWithDescriptor_size_(fontDescriptor, fontSize)
            attributes[AppKit.NSFontAttributeName] = font
        elif fontSize:
            font = AppKit.NSFont.fontWithName_size_(_FALLBACKFONT, fontSize)
            attributes[AppKit.NSFontAttributeName] = font
        if fill or cmykFill:
            if fill:
                fillColor = self._colorClass.getColor(fill).getNSObject()
            elif cmykFill:
                fillColor = self._cmykColorClass.getColor(cmykFill).getNSObject()
            attributes[AppKit.NSForegroundColorAttributeName] = fillColor
        if stroke or cmykStroke:
            if stroke:
                strokeColor = self._colorClass.getColor(stroke).getNSObject()
            elif cmykStroke:
                strokeColor = self._cmykColorClass.getColor(cmykStroke).getNSObject()
            attributes[AppKit.NSStrokeColorAttributeName] = strokeColor
            attributes[AppKit.NSStrokeWidthAttributeName] = -abs(strokeWidth)
        para = AppKit.NSMutableParagraphStyle.alloc().init()
        if align:
            para.setAlignment_(self._textAlignMap[align])
        if lineHeight:
            #para.setLineSpacing_(lineHeight)
            para.setMaximumLineHeight_(lineHeight)
            para.setMinimumLineHeight_(lineHeight)
        if tracking:
            attributes[AppKit.NSKernAttributeName] = tracking
        attributes[AppKit.NSParagraphStyleAttributeName] = para
        txt = AppKit.NSAttributedString.alloc().initWithString_attributes_(txt, attributes)
        self._attributedString.appendAttributedString_(txt)

    def __add__(self, txt):
        new = self.copy()
        new.append(txt,
                    font=self._font, fallbackFont=self._fallbackFont, fontSize=self._fontSize,
                    fill=self._fill, cmykFill=self._cmykFill,
                    stroke=self._stroke, cmykStroke=self._cmykStroke, strokeWidth=self._strokeWidth,
                    align=self._align, lineHeight=self._lineHeight, tracking=self._tracking, openTypeFeatures=self._openTypeFeatures)
        return new

    def __getitem__(self, index):
        if isinstance(index, slice):
            start = index.start
            stop = index.stop
            textLenght = len(self)

            if start is None:
                start = 0
            elif start < 0:
                start = textLenght + start
            elif start > textLenght:
                start = textLenght

            if stop is None:
                stop = textLenght
            elif stop < 0:
                stop = textLenght + stop

            if start + (stop-start) > textLenght:
                stop = textLenght - stop

            rng = (start, stop-start)
            new = self.__class__()
            try:
                new._attributedString = self._attributedString.attributedSubstringFromRange_(rng)
            except:
                pass
            return new
        else:
            text = str(self)
            return text[index]

    def __len__(self):
        return self._attributedString.length()

    def __repr__(self):
        return self._attributedString.string()

    def font(self, font, fontSize=None):
        """
        Set a font with the name of the font.
        Optionally a `fontSize` can be set directly.
        The default font, also used as fallback font, is 'LucidaGrande'.
        The default `fontSize` is 10pt.

        The name of the font relates to the font's postscript name.
        """
        font = font.encode("ascii", "ignore")
        self._font = font
        if fontSize is not None:
            self._fontSize = fontSize

    def fallbackFont(self, font):
        """
        Set a fallback font, used whenever a glyph is not available in the normal font.
        """
        if font:
            font = font.encode("ascii", "ignore")
            testFont = AppKit.NSFont.fontWithName_size_(font, self._fontSize)
            if testFont is None:
                raise DrawBotError, "Fallback font '%s' is not available" % font
        self._fallbackFont = font

    def fontSize(self, fontSize):
        """
        Set the font size in points.
        The default `fontSize` is 10pt.
        """
        self._fontSize = fontSize

    def fill(self, *fill):
        """
        Sets the fill color with a `red`, `green`, `blue` and `alpha` value.
        Each argument must a value float between 0 and 1.
        """
        self._fill = fill
        self._cmykFill = None

    def stroke(self, *stroke):
        """
        Sets the stroke color with a `red`, `green`, `blue` and `alpha` value.
        Each argument must a value float between 0 and 1.
        """
        self._stroke = stroke
        self._cmykStroke = None

    def cmykFill(self, *cmykFill):
        """
        Set a fill using a CMYK color before drawing a shape. This is handy if the file is intended for print.

        Sets the CMYK fill color. Each value must be a float between 0.0 and 1.0.
        """
        self._cmykFill = cmykFill
        self._fill = None

    def cmykStroke(self, *cmykStroke):
        """
        Set a stroke using a CMYK color before drawing a shape. This is handy if the file is intended for print.

        Sets the CMYK stroke color. Each value must be a float between 0.0 and 1.0.
        """
        self._cmykStroke = cmykStroke
        self._stroke = None

    def strokeWidth(self, strokeWidth):
        """
        Sets stroke width.
        """
        self._strokeWidth = strokeWidth

    def align(self, align):
        """
        Sets the text alignment.
        Possible `align` values are: `left`, `center` and `right`.
        """
        self._align = align

    def lineHeight(self, lineHeight):
        """
        Set the line height.
        """
        self._lineHeight = lineHeight

    def tracking(self, tracking):
        """
        Set the tracking between characters.
        """
        self._tracking = tracking

    def openTypeFeatures(self, *args, **features):
        """
        Enable OpenType features.
        """
        if args and args[0] == None:
            self._openTypeFeatures.clear()
        else:
            self._openTypeFeatures.update(features)

    def listOpenTypeFeatures(self, fontName=None):
        """
        List all OpenType feature tags for the current font.

        Optionally a `fontName` can be given.
        """
        if fontName is None:
            fontName = self._font
        return openType.getFeatureTagsForFontName(fontName)

    def size(self):
        """
        Return the size of the text.
        """
        return self._attributedString.size()

    def getNSObject(self):
        return self._attributedString

    def copy(self):
        """
        Copy the formatted string.
        """
        new = self.__class__()
        new._attributedString = self._attributedString.mutableCopy()
        return new

    def fontAscender(self):
        """
        Returns the current font ascender, based on the current `font` and `fontSize`.
        """
        font = AppKit.NSFont.fontWithName_size_(self._font, self._fontSize)
        if font is None:
            ff = self._fallbackFont or _FALLBACKFONT
            warnings.warn("font: %s is not installed, back to the fallback font: %s" % (self._font, ff))
            font = AppKit.NSFont.fontWithName_size_(ff, self._fontSize)
        return font.ascender()

    def fontDescender(self):
        """
        Returns the current font descender, based on the current `font` and `fontSize`.
        """
        font = AppKit.NSFont.fontWithName_size_(self._font, self._fontSize)
        if font is None:
            ff = self._fallbackFont or _FALLBACKFONT
            warnings.warn("font: %s is not installed, back to the fallback font: %s" % (self._font, ff))
            font = AppKit.NSFont.fontWithName_size_(ff, self._fontSize)
        return font.descender()        

    def fontXHeight(self):
        """
        Returns the current font x-height, based on the current `font` and `fontSize`.
        """
        font = AppKit.NSFont.fontWithName_size_(self._font, self._fontSize)
        if font is None:
            ff = self._fallbackFont or _FALLBACKFONT
            warnings.warn("font: %s is not installed, back to the fallback font: %s" % (self._font, ff))
            font = AppKit.NSFont.fontWithName_size_(ff, self._fontSize)
        return font.xHeight()

    def fontCapHeight(self):
        """
        Returns the current font cap height, based on the current `font` and `fontSize`.
        """
        font = AppKit.NSFont.fontWithName_size_(self._font, self._fontSize)
        if font is None:
            ff = self._fallbackFont or _FALLBACKFONT
            warnings.warn("font: %s is not installed, back to the fallback font: %s" % (self._font, ff))
            font = AppKit.NSFont.fontWithName_size_(ff, self._fontSize)
        return font.capHeight()

    def fontLeading(self):
        """
        Returns the current font leading, based on the current `font` and `fontSize`.
        """
        font = AppKit.NSFont.fontWithName_size_(self._font, self._fontSize)
        if font is None:
            ff = self._fallbackFont or _FALLBACKFONT
            warnings.warn("font: %s is not installed, back to the fallback font: %s" % (self._font, ff))
            font = AppKit.NSFont.fontWithName_size_(ff, self._fontSize)
        return font.leading()

    def fontLineHeight(self):
        """
        Returns the current line height, based on the current `font` and `fontSize`.
        If a `lineHeight` is set, this value will be returned.
        """    
        if self._lineHeight is not None:
            return self._lineHeight
        font = AppKit.NSFont.fontWithName_size_(self._font, self._fontSize)
        if font is None:
            ff = self._fallbackFont or _FALLBACKFONT
            warnings.warn("font: %s is not installed, back to the fallback font: %s" % (self._font, ff))
            font = AppKit.NSFont.fontWithName_size_(ff, self._fontSize)
        return font.defaultLineHeightForFont()

    def appendGlyph(self, *glyphNames):
        """
        Appends a glyph by his glyph name using the current `font`.
        """
        # use a non breaking space as replacement character
        baseString = unichr(0x00A0)
        font = None
        if self._font:
            font = AppKit.NSFont.fontWithName_size_(self._font, self._fontSize)
        if font is None:
            warnings.warn("font: %s is not installed, back to the fallback font: %s" % (self._font, _FALLBACKFONT))
            font = AppKit.NSFont.fontWithName_size_(_FALLBACKFONT, self._fontSize)
        fallbackFont = self._fallbackFont
        self._fallbackFont = None
        for glyphName in glyphNames:
            glyph = font.glyphWithName_(glyphName)
            if glyph:
                self.append(baseString)
                glyphInfo = AppKit.NSGlyphInfo.glyphInfoWithGlyph_forFont_baseString_(glyph, font , baseString)
                self._attributedString.addAttribute_value_range_(AppKit.NSGlyphInfoAttributeName, glyphInfo, (len(self)-1, 1))
            else:
                warnings.warn("font %s has no glyph with the name %s" % (font.fontName(), glyphName))
        self._fallbackFont = fallbackFont

class Text(object):

    def __init__(self):
        self._fontName = _FALLBACKFONT
        self._fallbackFontName = None
        self._fontSize = 10
        self._lineHeight = None
        self._tracking = None
        self._hyphenation = None
        self.openTypeFeatures = dict()

    def _get_font(self):
        _font = AppKit.NSFont.fontWithName_size_(self._fontName, self.fontSize)
        if _font == None:
            ff = self._fallbackFontName or _FALLBACKFONT
            warnings.warn("font: %s is not installed, back to the fallback font: %s" % (self._fontName, ff))
            self._fontName = ff
            _font = AppKit.NSFont.fontWithName_size_(ff, self.fontSize)
        coreTextfeatures = []
        for featureTag, value in self.openTypeFeatures.items():
            if not value:
                featureTag = "%s_off" % featureTag
            if featureTag in openType.featureMap:
                feature = openType.featureMap[featureTag]
                coreTextfeatures.append(feature)
        fontDescriptor = _font.fontDescriptor()
        fontAttributes = {
            CoreText.NSFontFeatureSettingsAttribute : coreTextfeatures,
            }
        if self._fallbackFontName:
            fontAttributes[CoreText.NSFontCascadeListAttribute] = [AppKit.NSFontDescriptor.fontDescriptorWithName_size_(self._fallbackFontName, self.fontSize)]
        fontDescriptor = fontDescriptor.fontDescriptorByAddingAttributes_(fontAttributes)
        _font = AppKit.NSFont.fontWithDescriptor_size_(fontDescriptor, self.fontSize)
        return _font

    font = property(_get_font)

    def _get_fontName(self):
        return self._fontName

    def _set_fontName(self, fontName):
        self._fontName = fontName

    fontName = property(_get_fontName, _set_fontName)

    def _get_fallbackFontName(self):
        return self._fallbackFontName

    def _set_fallbackFontName(self, fontName):
        if fontName:
            dummyFont = AppKit.NSFont.fontWithName_size_(fontName, 10)
            if dummyFont is None:
                raise DrawBotError, "Fallback font '%s' is not available" % fontName
        self._fallbackFontName = fontName

    fallbackFontName = property(_get_fallbackFontName, _set_fallbackFontName)

    def _get_fontSize(self):
        return self._fontSize

    def _set_fontSize(self, value):
        self._fontSize = value

    fontSize = property(_get_fontSize, _set_fontSize)

    def _get_lineHeight(self):
        return self._lineHeight

    def _set_lineHeight(self, value):
        self._lineHeight = value

    lineHeight = property(_get_lineHeight, _set_lineHeight)

    def _get_tracking(self):
        return self._tracking

    def _set_tracking(self, value):
        self._tracking = value

    tracking = property(_get_tracking, _set_tracking)

    def _get_hyphenation(self):
        return self._hyphenation

    def _set_hyphenation(self, value):
        self._hyphenation = value

    hyphenation = property(_get_hyphenation, _set_hyphenation)

    def copy(self):
        new = self.__class__()
        new.fontName = self.fontName
        new.fallbackFontName = self.fallbackFontName
        new.fontSize = self.fontSize
        new.lineHeight = self.lineHeight
        new.tracking = self.tracking
        new.hyphenation = self.hyphenation
        new.openTypeFeatures = dict(self.openTypeFeatures)
        return new

class GraphicsState(object):

    _textClass = Text
    _colorClass = Color

    def __init__(self):
        self.fillColor =  self._colorClass(0)
        self.strokeColor = None
        self.cmykFillColor = None
        self.cmykStrokeColor = None
        self.shadow = None
        self.gradient = None
        self.strokeWidth = 1
        self.lineDash = None
        self.lineCap = None
        self.lineJoin = None
        self.miterLimit = 10
        self.text = self._textClass()
        self.path = None

    def copy(self):
        new = self.__class__()
        if self.fillColor is not None:
            new.fillColor = self.fillColor.copy()
        else:
            new.fillColor = None
        if self.strokeColor:
            new.strokeColor = self.strokeColor.copy()
        if self.cmykFillColor:
            new.cmykFillColor = self.cmykFillColor.copy()
        if self.cmykStrokeColor:
            new.cmykStrokeColor = self.cmykStrokeColor.copy()
        if self.shadow:
            new.shadow = self.shadow.copy()
        if self.gradient:
            new.gradient = self.gradient.copy()
        if self.path is not None:
            new.path = self.path.copy()
        new.text = self.text.copy()

        new.strokeWidth = self.strokeWidth
        new.lineCap = self.lineCap
        if self.lineDash is not None:
            new.lineDash = list(self.lineDash)
        new.lineJoin = self.lineJoin
        new.miterLimit = self.miterLimit
        return new

class BaseContext(object):

    _graphicsStateClass = GraphicsState

    _cmykColorClass = CMYKColor
    _colorClass = Color
    _textClass = Text
    _shadowClass = Shadow
    _bezierPathClass = BezierPath
    _gradientClass = Gradient

    fileExtensions = []

    _lineJoinStylesMap = dict(
        miter=Quartz.kCGLineJoinMiter,
        round=Quartz.kCGLineJoinRound,
        bevel=Quartz.kCGLineJoinBevel
        )

    _lineCapStylesMap = dict(
        butt=Quartz.kCGLineCapButt,
        square=Quartz.kCGLineCapSquare,
        round=Quartz.kCGLineCapRound,
        )

    _textAlignMap = dict(
        center=AppKit.NSCenterTextAlignment,
        left=AppKit.NSLeftTextAlignment,
        right=AppKit.NSRightTextAlignment,
        justified=AppKit.NSJustifiedTextAlignment,
        )

    _softHypen = 0x00AD

    def __init__(self):
        self.width = None
        self.height = None
        self.hasPage = False
        self.reset()

    # overwrite by a subclass

    def _newPage(self, width, height):
        pass

    def _save(self):
        pass

    def _restore(self):
        pass

    def _drawPath(self):
        pass

    def _clipPath(self):
        pass

    def _transform(self, matrix):
        pass

    def _text(self, txt, (x, y)):
        pass

    def _textBox(self, txt, (x, y, w, h), align):
        pass

    def _image(self, path, (x, y), alpha):
        pass

    def _frameDuration(self, seconds):
        pass

    def _reset(self):
        pass

    def _saveImage(self, path, multipage):
        pass

    def _printImage(self, pdf=None):
        pass

    ###

    def reset(self):
        self._stack = []
        self._state = self._graphicsStateClass()
        self._reset()

    def size(self, width=None, height=None):
        if width is not None:
            self.width = width
        if height is not None:
            self.height = height

    def newPage(self, width=None, height=None):
        if self.width is None and width is None:
            raise DrawBotError, "A page must have a width"
        if self.height is None and height is None:
            raise DrawBotError, "A page must have a height"
        self.hasPage = True
        self._newPage(width, height)

    def saveImage(self, path, multipage):
        if not self.hasPage:
            raise DrawBotError, "can't save image when no page is set"
        self._saveImage(path, multipage)

    def printImage(self, pdf=None):
        self._printImage(pdf)

    def frameDuration(self, seconds):
        self._frameDuration(seconds)

    def save(self):
        self._stack.append(self._state.copy())
        self._save()

    def restore(self):
        if not self._stack:
            raise DrawBotError, "can't restore graphics state: no matching save()"
        self._state = self._stack.pop()
        self._restore()

    def rect(self, x, y, w, h):
        path = self._bezierPathClass()
        path.rect(x, y, w, h)
        self.drawPath(path)

    def oval(self, x, y, w, h):
        path = self._bezierPathClass()
        path.oval(x, y, w, h)
        self.drawPath(path)

    def newPath(self):
        self._state.path = self._bezierPathClass()

    def moveTo(self, pt):
        if self._state.path is None:
            raise DrawBotError, "Create a new path first"
        self._state.path.moveTo(pt)

    def lineTo(self, pt):
        self._state.path.lineTo(pt)

    def curveTo(self, pt1, pt2, pt):
        self._state.path.curveTo(pt1, pt2, pt)

    def arcTo(self, pt1, pt2, radius):
        self._state.path.arcTo(pt1, pt2, radius)

    def closePath(self):
        self._state.path.closePath()

    def drawPath(self, path):
        if path is not None:
            self._state.path = path
        self._drawPath()

    def clipPath(self, path):
        if path is not None:
            self._state.path = path
        self._clipPath()

    def fill(self, r, g=None, b=None, a=1):
        if r is  None:
            self._state.fillColor = None
            self._state.cmykFillColor = None
            return
        self._state.fillColor = self._colorClass(r, g, b, a)
        self._state.gradient = None

    def cmykFill(self, c , m, y, k, a=1):
        if c is None:
            self.fill(None)
        else:
            self._state.cmykFillColor = self._cmykColorClass(c, m, y, k, a)
            r, g, b = cmyk2rgb(c, m, y, k)
            self.fill(r, g, b, a)

    def stroke(self, r, g=None, b=None, a=1):
        if r is None:
            self._state.strokeColor = None
            self._state.cmykStrokeColor = None
            return
        self._state.strokeColor = self._colorClass(r, g, b, a)

    def cmykStroke(self, c , m, y, k, a=1):
        if c is None:
            self.stroke(None)
        else:
            self._state.cmykStrokeColor = self._cmykColorClass(c, m, y, k, a)
            r, g, b = cmyk2rgb(c, m, y, k)
            self.stroke(r, g, b, a)

    def shadow(self, offset, blur, color):
        if offset is None:
            self._state.shadow = None
            return
        self._state.shadow = self._shadowClass(offset, blur, color)

    def cmykShadow(self, offset, blur, color):
        if offset is None:
            self._state.shadow = None
            return
        rgbColor = cmyk2rgb(color[0], color[1], color[2], color[3])
        self._state.shadow = self._shadowClass(offset, blur, rgbColor)
        self._state.shadow.cmykColor = self._cmykColorClass(*color)

    def linearGradient(self, startPoint=None, endPoint=None, colors=None, locations=None):
        if startPoint is None:
            self._state.gradient = None
            self.fill(0)
            return
        self._state.gradient = self._gradientClass("linear", startPoint, endPoint, colors, locations)
        self.fill(None)

    def cmykLinearGradient(self, startPoint=None, endPoint=None, colors=None, locations=None):
        if startPoint is None:
            self._state.gradient = None
            self.fill(0)
            return
        rgbColors = [cmyk2rgb(color[0], color[1], color[2], color[3]) for color in colors]
        self._state.gradient = self._gradientClass("linear", startPoint, endPoint, rgbColors, locations)
        self._state.gradient.cmykColors = [self._cmykColorClass(*color) for color in colors]
        self.fill(None)

    def radialGradient(self, startPoint=None, endPoint=None, colors=None, locations=None, startRadius=0, endRadius=100):
        if startPoint is None:
            self._state.gradient = None
            self.fill(0)
            return
        self._state.gradient = self._gradientClass("radial", startPoint, endPoint, colors, locations, startRadius, endRadius)
        self.fill(None)

    def cmykRadialGradient(self, startPoint=None, endPoint=None, colors=None, locations=None, startRadius=0, endRadius=100):
        if startPoint is None:
            self._state.gradient = None
            self.fill(0)
            return
        rgbColors = [cmyk2rgb(color[0], color[1], color[2], color[3]) for color in colors]
        self._state.gradient = self._gradientClass("radial", startPoint, endPoint, rgbColors, locations, startRadius, endRadius)
        self._state.gradient.cmykColors = [self._cmykColorClass(*color) for color in colors]
        self.fill(None)

    def strokeWidth(self, value):
        self._state.strokeWidth = value

    def miterLimit(self, value):
        self._state.miterLimit = value

    def lineJoin(self, join):
        if join is None:
            self._state.lineJoin = None
        if join not in self._lineJoinStylesMap:
            raise DrawBotError, "lineJoin() argument must be 'bevel', 'miter' or 'round'"
        self._state.lineJoin = self._lineJoinStylesMap[join]

    def lineCap(self, cap):
        if cap is None:
            self._state.lineCap = None
        if cap not in self._lineCapStylesMap:
            raise DrawBotError, "lineCap() argument must be 'butt', 'square' or 'round'"
        self._state.lineCap = self._lineCapStylesMap[cap]

    def lineDash(self, dash):
        if dash[0] == None:
            self._state.lineDash = None
            return
        self._state.lineDash = list(dash)

    def transform(self, matrix):
        self._transform(matrix)

    def font(self, fontName, fontSize):
        self._state.text.fontName = fontName
        if fontSize != None:
            self.fontSize(fontSize)

    def fallbackFont(self, fontName):
        self._state.text.fallbackFontName = fontName

    def fontSize(self, fontSize):
        self._state.text.fontSize = fontSize

    def lineHeight(self, lineHeight):
        self._state.text.lineHeight = lineHeight

    def tracking(self, tracking):
        self._state.text.tracking = tracking

    def hyphenation(self, value):
        self._state.text.hyphenation = value

    def openTypeFeatures(self, *args, **features):
        if args and args[0] == None:
            self._state.text.openTypeFeatures.clear()
        else:
            self._state.text.openTypeFeatures.update(features)

    def attributedString(self, txt, align=None):
        if isinstance(txt, FormattedString):
            return txt.getNSObject()
        attributes = {AppKit.NSFontAttributeName : self._state.text.font}
        if self._state.fillColor is not None:
            if self._state.cmykFillColor:
                c = self._state.cmykFillColor
            else:
                c = self._state.fillColor
            extra = {
                AppKit.NSForegroundColorAttributeName : c.getNSObject(),
                }
            attributes.update(extra)
        if self._state.strokeColor is not None:
            if self._state.cmykStrokeColor:
                c = self._state.cmykStrokeColor
            else:
                c = self._state.strokeColor
            #strokeWidth = -abs(self._state.strokeWidth)
            extra = {
                    #AppKit.NSStrokeWidthAttributeName : strokeWidth,
                    AppKit.NSStrokeColorAttributeName : c.getNSObject(),
                    }

            attributes.update(extra)
        para = AppKit.NSMutableParagraphStyle.alloc().init()
        if align:
            para.setAlignment_(self._textAlignMap[align])
        if self._state.text.lineHeight:
            #para.setLineSpacing_(self._state.text.lineHeight)
            para.setMaximumLineHeight_(self._state.text.lineHeight)
            para.setMinimumLineHeight_(self._state.text.lineHeight)
        attributes[AppKit.NSParagraphStyleAttributeName] = para
        if self._state.text.tracking:
            attributes[AppKit.NSKernAttributeName] = self._state.text.tracking
        text = AppKit.NSAttributedString.alloc().initWithString_attributes_(txt, attributes)
        return text

    def hyphenateAttributedString(self, attrString, width):
        attrString = attrString.mutableCopy()
        mutString = attrString.mutableString()
        wordRange = AppKit.NSMakeRange(mutString.length(), 0)
        while wordRange.location > 2:
            wordRange = attrString.doubleClickAtIndex_(wordRange.location - 2)
            hyphenIndex = AppKit.NSMaxRange(wordRange)
            while hyphenIndex != AppKit.NSNotFound:
                hyphenIndex = attrString.lineBreakByHyphenatingBeforeIndex_withinRange_(hyphenIndex, wordRange)
                if hyphenIndex != AppKit.NSNotFound:
                    mutString.insertString_atIndex_(unichr(self._softHypen), hyphenIndex)

        textLength = attrString.length()

        setter = CoreText.CTTypesetterCreateWithAttributedString(attrString)
        location = 0

        while location < textLength:
            breakIndex = CoreText.CTTypesetterSuggestLineBreak(setter, location, width)
            sub = attrString.attributedSubstringFromRange_((location, breakIndex))
            location += breakIndex
            subString = sub.string()
            if breakIndex == 0:
                break
            subString = sub.string()
            if subString[-1] == unichr(self._softHypen):
                subAttr, _ = sub.attributesAtIndex_effectiveRange_(0, None)
                hyphenAttrString = AppKit.NSAttributedString.alloc().initWithString_attributes_("-", subAttr)
                hyphenWidth = hyphenAttrString.size().width
                if sub.size().width + hyphenWidth < width:
                    mutString.insertString_atIndex_("-", location)
                    setter = CoreText.CTTypesetterCreateWithAttributedString(attrString)
                    location += 1
                else:
                    attrString.deleteCharactersInRange_((location-1, 1))
                    setter = CoreText.CTTypesetterCreateWithAttributedString(attrString)
                    location -= breakIndex

        mutString.replaceOccurrencesOfString_withString_options_range_(unichr(self._softHypen), "", AppKit.NSLiteralSearch, (0, mutString.length()))
        return attrString

    def clippedText(self, txt, (x, y, w, h), align):
        attrString = self.attributedString(txt, align=align)
        if self._state.text.hyphenation:
            hyphenIndexes = [i for i, c in enumerate(attrString.string()) if c == "-"]
            attrString = self.hyphenateAttributedString(attrString, w)
        setter = CoreText.CTFramesetterCreateWithAttributedString(attrString)
        path = CoreText.CGPathCreateMutable()
        CoreText.CGPathAddRect(path, None, CoreText.CGRectMake(x, y, w, h))
        box = CoreText.CTFramesetterCreateFrame(setter, (0, 0), path, None)
        visibleRange = CoreText.CTFrameGetVisibleStringRange(box)
        clip = visibleRange.length
        if self._state.text.hyphenation:
            subString = attrString.string()[:clip]
            for i in hyphenIndexes:
                if i < clip:
                    clip += 1
                else:
                    break
            clip -= subString.count("-")
        return txt[clip:]

    def textSize(self, txt, align):
        text = self.attributedString(txt, align)
        w, h = text.size()
        return w, h

    def textBox(self, txt, (x, y, w, h), align="left"):
        self._state.path = None
        self._textBox(txt, (x, y, w, h), align)

    def image(self, path, (x, y), alpha):
        self._image(path, (x, y), alpha)