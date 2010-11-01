#! /usr/bin/python
# -*- coding: utf-8 -*-
# GPLv3, John Drinkwater <john@nextraweb.com>
# http://johndrinkwater.name/code/gpx2png/

import math

# defaults
ofilename = "map.png"

verbose = False

# use tiles from OSM
background = True

# px border around track
border = 50

# Max tile w×h for output image, we auto scale
# TODO allow for wider/taller output images?
osize = 2

# need to include CC notice if we use tiles
cnotice = "CC BY-SA OpenStreetMap"

# TODO caching?
# TODO text overlays
# TODO SVG graphics for cnotice
# TODO options for tiles renderer

# variables
version = 0.01


# TODO parse cli here
tilerenderer = 'mapnik'
tileserver = 'http://tile.openstreetmap.org'

# TODO if Verbose, output parsed options

# XXX we are just using defaults now

#### Helper classes here

class Tile:
	
	# Code from OSM
	@staticmethod
	def getNumber( lat, long, zoom ):
		latrad = math.radians(lat)
		n = 2.0 ** zoom
		xtile = int((long + 180.0) / 360.0 * n)
		ytile = int((1.0 - math.log(math.tan(latrad) + (1 / math.cos(latrad))) / math.pi) / 2.0 * n)
		return(xtile, ytile)

	# Code from OSM
	@staticmethod
	def getCoords( xtile, ytile, zoom ):
		n = 2.0 ** zoom
		long = xtile / n * 360.0 - 180.0
		latrad = math.atan(math.sinh(math.pi * (1 - 2 * ytile / n)))
		lat = math.degrees(latrad)
		return(lat, long)

# TODO read file

# assuming we track data here, loop to calc tiles needed
def calculateTiles( points ):
	tilexmin = 2^20
	tilexmax = 0
	tileymin = 2^20
	tileymax = 0

	zoom = 10

	for point in points:
		[xtile, ytile] = Tile.getNumber( point[0], point[1], zoom )
		tilexmin = min(xtile, tilexmin)
		tilexmax = max(xtile, tilexmax)
		tileymin = min(ytile, tileymin)
		tileymax = max(ytile, tileymax)

	# now whittle it down to osize = max
	# TODO where to expand tiles for cropping?
	
# Just test data for now
print calculateTiles( [[51.937697,-1.983817],
	[51.947704,-1.973797],
	[51.997670,-1.923847]])
