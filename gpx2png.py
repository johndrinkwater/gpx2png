#! /usr/bin/python
# -*- coding: utf-8 -*-
# GPLv3, John Drinkwater <john@nextraweb.com>
# http://johndrinkwater.name/code/gpx2png/

import math
from xml.dom.minidom import parse

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

# Compute zoom for us, use osize
autozoom = True

# default if not auto..
zoom = 10

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
	
	@staticmethod
	def getNumber( lat, long, zoom ):
		# Code from OSM
		latrad = math.radians(lat)
		n = 2.0 ** zoom
		xtile = int((long + 180.0) / 360.0 * n)
		ytile = int((1.0 - math.log(math.tan(latrad) + (1 / math.cos(latrad))) / math.pi) / 2.0 * n)
		return (xtile, ytile)

	@staticmethod
	def getCoords( xtile, ytile, zoom ):
		# Code from OSM
		n = 2.0 ** zoom
		long = xtile / n * 360.0 - 180.0
		latrad = math.atan(math.sinh(math.pi * (1 - 2 * ytile / n)))
		lat = math.degrees(latrad)
		return(lat, long)

	@staticmethod
	def getTileURL( xtile, ytile, zoom ):
		return '/'.join( [tileserver, str(zoom), str(xtile), str(ytile)] ) + '.png'

	# TODO Remove this, testing 
	@staticmethod
	def quickTest( tiles ):
		for x in range(tiles['x']['min'],tiles['x']['min'] + tiles['x']['count'] + 1):
			for y in range(tiles['y']['min'],tiles['y']['min'] + tiles['y']['count'] + 1):
				print Tile.getTileURL( x, y, tiles['zoom'] )

	# returns tile bounding box for the points at this zoom level
	# Be cautious, as this can produce a lot of tiles
	# The BB is +1 in all directions so we can trim the image later ()
	@staticmethod
	def calculateTiles( points, zoom = 10 ):

		tilexmin = tileymin = 200000
		tilexmax = tileymax = 0
		
		# TODO could we do odds/evens to lighten this load?
		
		for point in points:
			[xtile, ytile] = Tile.getNumber( point[0], point[1], zoom )
			tilexmin = min(xtile, tilexmin)
			tilexmax = max(xtile, tilexmax)
			tileymin = min(ytile, tileymin)
			tileymax = max(ytile, tileymax)

		# TODO possibly expand here wrt image ‘border’

		return {'x': { 'min':tilexmin - 1, 'max':tilexmax + 1, 'count': tilexmax - tilexmin + 2},
				'y': { 'min':tileymin - 1, 'max':tileymax + 1, 'count': tileymax - tileymin + 2},
				'zoom': zoom }

	# returns tile bounding box that is automatically scaled to a correct zoom level.
	# The BB is +1 in all directions so we can trim the image later ()
	@staticmethod
	def calculateTilesAuto( points ):

		zoomdefault = 16

		# get the default scale tiles
		tiles = Tile.calculateTiles( points, zoomdefault )

		while ( (tiles['x']['count']+1) * (tiles['y']['count']+1) > (osize * osize) ):
			zoomdefault -= 1
			tiles['x']['count'] >>= 1
			tiles['y']['count'] >>= 1

		# get the re-scaled tiles
		return Tile.calculateTiles( points, zoomdefault )

# GPX helper class, for singular files
class GPX:
	points = []

	def load(self, dom):
		# we're going to be ignorant of anything but trkpt for now
		# TODO support waypoints, track segments
		trackPoints = dom.getElementsByTagName('trkpt')
		self.points = map( lambda x: [float(x.getAttribute('lat')), float(x.getAttribute('lon'))], trackPoints)
	
	def loadFromFile(self, file):
		dom = parse(file)
		self.load(dom)
	
	def loadFromString(self, string):
		dom = parseString(string)
		self.load(dom)


# Just test data for now
track = GPX()
track.loadFromFile('winchcombe.gpx')
print track

tiles = Tile.calculateTilesAuto( track.points )

Tile.quickTest( tiles )
