#! /usr/bin/python
# -*- coding: utf-8 -*-
# GPLv3, John Drinkwater <john@nextraweb.com>
# http://johndrinkwater.name/code/gpx2png/

import Image, ImageDraw
import math
import os
import urllib
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

cachelocation = 'cache'
# build dir
cachelocation = os.path.join('.', cachelocation)
if not os.path.isdir(cachelocation):
	os.mkdir(cachelocation)

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
		expand = 1

		return {'x': { 'min':tilexmin - expand, 'max':tilexmax + 1+expand, 'count': tilexmax - tilexmin +1 + 2 * expand },
				'y': { 'min':tileymin - expand, 'max':tileymax + 1+expand, 'count': tileymax - tileymin +1 + 2 * expand },
				'zoom': zoom }

	# returns tile bounding box that is automatically scaled to a correct zoom level.
	# The BB is +1 in all directions so we can trim the image later ()
	@staticmethod
	def calculateTilesAuto( points ):

		zoomdefault = 16

		# get the default scale tiles
		tiles = Tile.calculateTiles( points, zoomdefault )

		while ( (tiles['x']['count']) * (tiles['y']['count']) > (osize+1 * osize+1) ):
			zoomdefault -= 1
			tiles['x']['count'] >>= 1
			tiles['y']['count'] >>= 1

		# get the re-scaled tiles
		return Tile.calculateTiles( points, zoomdefault )

	@staticmethod
	def	getPixelForCoord( point, bounds, tiles ):

		# return pixel coordinate in image of 

		#tile = Tile.getNumber( point[0], point[1], tiles['zoom'] )
		#offsetx = tile[0] - tiles['x']['min']
		#offsety = tile[1] - tiles['y']['min']
		#print offsetx, offsety
		return [1,1]
		pass

	@staticmethod
	def	populateBackground( tiles, image ):
		rootx = tiles['x']['min']
		rooty = tiles['y']['min']
		for x in range(tiles['x']['min'],tiles['x']['min'] + tiles['x']['count'] + 1):
			for y in range(tiles['y']['min'],tiles['y']['min'] + tiles['y']['count'] + 1):
				fromx = abs(rootx - x)
				fromy = abs(rooty - y)
				temptilename = '-'.join( ['cache', str(zoom), str(x), str(y) ] ) + '.png' 
				temptilename = os.path.join(cachelocation, temptilename)
				# TODO thread this?
				if not os.path.isfile( temptilename ):
					print 'Fetching tile…'
					urllib.urlretrieve( Tile.getTileURL( x, y, tiles['zoom'] ), 
						temptilename )

				tile = Image.open( temptilename )
				image.paste( tile, (256*fromx, 256*fromy ))

		return image

		

# GPX helper class, for singular files
class GPX:
	points = []
	tiles = []
	bounds = [(),()]
	delta = [0,0]

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

	def computeBounds(self):
		# here we use self.points and get the area of the drawing
		# (tiles), and figure out the lat/long bounds
		# then we return
		self.tiles = Tile.calculateTilesAuto( self.points )

		self.bounds[0] = Tile.getCoords( self.tiles['x']['min'], self.tiles['y']['min'], self.tiles['zoom'] )
		# because tile coords are from top left
		self.bounds[1] = Tile.getCoords( self.tiles['x']['max']+1, self.tiles['y']['max']+1, self.tiles['zoom']  )		
		
	def drawTrack(self, filename):

		imagesize = ( self.tiles['x']['count'] * 256, self.tiles['y']['count'] * 256 )
		image = Image.new("RGB", imagesize, '#ffffff')

		# this will write the tiles into the image..
		image = Tile.populateBackground(self.tiles, image)

		# draw track (skewing it to the projection)
		draw = ImageDraw.Draw(image)

		# compute pixel locations
		pointlist = map( lambda x: Tile.getPixelForCoord(x, self.bounds, self.tiles), self.points)

		# draw

		# trim image by tile - border
		# atm, its ½ tile wide..
		trim = int(256/2)
		image = image.crop( tuple( [trim, trim] + map( lambda x: x-trim, image.size) ) )

		# write file 
		image.save(filename, "PNG")

		pass

# Just test data for now
track = GPX()
track.loadFromFile('winchcombe.gpx')
# track.loadFromFile('2010-07-12_12-18-49.gpx')

# push this into loading, obviously
track.computeBounds()
track.drawTrack('output.png')

