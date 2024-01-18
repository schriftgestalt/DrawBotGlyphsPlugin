# from distutils.version import StrictVersion
import platform

# It is safe to compare osVersion to strings, as StrictVersion casts strings
# to StrictVersion instances upon compare.
# macOSVersion = StrictVersion(platform.mac_ver("0.0.0")[0])

version = platform.mac_ver()[0].split('.')[:2]
shortVersionString = '%s.%0.2d' % (version[0], int(version[1]))
macOSVersion = float(shortVersionString)