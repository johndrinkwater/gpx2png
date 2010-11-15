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

# TODO if Verbose, output parsed options

# XXX we are just using defaults now

# Static methods for tile maths
class Tile:

	# Returns an OSM tile coordinate for the lat, long provided
	@staticmethod
	def getNumber( lat, long, zoom ):
		# Code from OSM
		latrad = math.radians(lat)
		n = 2.0 ** zoom
		xtile = int((long + 180.0) / 360.0 * n)
		ytile = int((1.0 - math.log(math.tan(latrad) + (1 / math.cos(latrad))) / math.pi) / 2.0 * n)
		return (xtile, ytile)

	# Returns a lat, long for the provided OSM tile coordinate
	@staticmethod
	def getCoords( xtile, ytile, zoom ):
		# Code from OSM
		n = 2.0 ** zoom
		long = xtile / n * 360.0 - 180.0
		latrad = math.atan(math.sinh(math.pi * (1 - 2 * ytile / n)))
		lat = math.degrees(latrad)
		return(lat, long)

	# Return a URL for the tile at the tileserver
	@staticmethod
	def getTileURL( tileserver, tilex, tiley, zoom ):
		return '/'.join( [tileserver, zoom, str(tilex), str(tiley)] ) + '.png'

	# returns tile bounding box for the points at this zoom level
	@staticmethod
	def calculateTiles( bounds, zoom = 10 ):

		tilexmin = tileymin = 200000
		tilexmax = tileymax = 0
		[tilexmin, tileymin] = Tile.getNumber( bounds[0][0], bounds[0][1], zoom )
		[tilexmax, tileymax] = Tile.getNumber( bounds[1][0], bounds[1][1], zoom )

		return {'x': { 'min':tilexmin, 'max':tilexmax , 'count': tilexmax - tilexmin +1 },
				'y': { 'min':tileymin, 'max':tileymax , 'count': tileymax - tileymin +1 },
				'zoom': zoom }

	# returns tile bounding box that is automatically scaled to a correct zoom level.
	# The BB is +1 in all directions so we can trim the image later ()
	@staticmethod
	def calculateTilesAuto( bounds, size ):

		zoomdefault = 16

		# get the default scale tiles
		tiles = Tile.calculateTiles( bounds, zoomdefault )
		while ( (tiles['x']['count']) * (tiles['y']['count']) >= ( size * size) ):
			zoomdefault -= 1
			tiles['x']['count'] >>= 1
			tiles['y']['count'] >>= 1

		# get the re-scaled tiles
		return Tile.calculateTiles( bounds, zoomdefault )

	@staticmethod
	def getPixelForCoord( point, bounds, imagesize ):
		return (int((bounds[0][1] - point[1] ) / bounds[2][1] * imagesize[0]) ,
				int((bounds[0][0] - point[0] ) / bounds[2][0] * imagesize[1]))

	# TODO fetch more bordering tiles than we need, so we can better fit out image!
	@staticmethod
	def populateBackground( server, style, tiles, image ):
		rootx = tiles['x']['min']
		rooty = tiles['y']['min']
		zoom = str(tiles['zoom'])
		templocation = os.path.join(cachelocation, style)
		if not os.path.isdir(templocation):
			os.mkdir(templocation)

		for x in range(tiles['x']['min'],tiles['x']['min'] + tiles['x']['count'] + 1):
			for y in range(tiles['y']['min'],tiles['y']['min'] + tiles['y']['count'] + 1):
				fromx = abs(rootx - x)
				fromy = abs(rooty - y)
				temptilename = '-'.join( ['cache', zoom, str(x), str(y) ] ) + '.png'
				temptilename = os.path.join(templocation, temptilename)
				# TODO thread this?
				if not os.path.isfile( temptilename ):
					print 'Fetching tile…'
					urllib.urlretrieve( Tile.getTileURL( server, x, y, zoom ),
						temptilename )

				tile = Image.open( temptilename )
				image.paste( tile, (256*fromx, 256*fromy ))

		return image



# GPX helper class, for singular files
class GPX:
	points = []
	pointsbounds = [(),()]

	tiles = []
	tilesbounds = [(),(), ()]

	options = {
		'size': 2, # Max tile w×h for output image
		'border': 20, # TODO distance from edge of image to nearest path?
		'line': 1,
		'filename': 'output.png', # Default output filename if not provided
		'renderer': 'mapnik', # OSM server to use
		}

	def setOptions(self, opt):
		self.options.update(opt)

		# Push the selected tile server into options
		tileservers = { 'mapnik': 'http://tile.openstreetmap.org',
						'osmarender': 'http://tah.openstreetmap.org/Tiles/tile/',
						'cyclemap': 'http://andy.sandbox.cloudmade.com/tiles/cycle/',
						}
		tileserver = { 'tileserver' : tileservers.get( self.options.get('renderer') ) }
		self.options.update(tileserver)

	def load(self, dom):
		# we're going to be ignorant of anything but trkpt for now
		# TODO support waypoints, track segments
		trackPoints = dom.getElementsByTagName('trkpt')
		self.points = map( lambda x: [float(x.getAttribute('lat')), float(x.getAttribute('lon'))], trackPoints)
		self.computeBounds()

	def loadFromFile(self, file):
		dom = parse(file)
		self.load(dom)

	def loadFromString(self, string):
		dom = parseString(string)
		self.load(dom)

	# calculate lat/long bounds of path
	# calculate tile area, and produce tile bounds
	def computeBounds(self):

		latmin = longmin = 200000
		latmax = longmax = -200000

		for point in self.points:
			latmin = min(point[0], latmin)
			latmax = max(point[0], latmax)
			longmin = min(point[1], longmin)
			longmax = max(point[1], longmax)
		self.pointsbounds = [(latmax, longmin), (latmin, longmax)]

		self.tiles = Tile.calculateTilesAuto( self.pointsbounds, self.options.get('size') )

		self.tilesbounds[0] = Tile.getCoords( self.tiles['x']['min'], self.tiles['y']['min'], self.tiles['zoom'] )
		# because tile coords are from top left
		self.tilesbounds[1] = Tile.getCoords( self.tiles['x']['max']+1, self.tiles['y']['max']+1, self.tiles['zoom'] )		
		self.tilesbounds[2] = (	self.tilesbounds[0][0] - self.tilesbounds[1][0],
							self.tilesbounds[0][1] - self.tilesbounds[1][1] )

	def drawTrack(self, filename = ''):

		if filename == '':
			filename = self.options.get('filename')

		imagesize = ( self.tiles['x']['count'] * 256, self.tiles['y']['count'] * 256 )
		image = Image.new("RGB", imagesize, '#ffffff')

		# this will write the tiles into the image..
		image = Tile.populateBackground(self.options.get('tileserver'), self.options.get('renderer'), self.tiles, image)

		# draw track (skewing it to the projection)
		draw = ImageDraw.Draw(image)

		# compute pixel locations
		pointlist = map( lambda x: Tile.getPixelForCoord(x, self.tilesbounds, imagesize), self.points)

		# draw
		# TODO give user option to style
		draw.line(pointlist, fill='black', width=self.options.get('line'))

		size = self.options.get('size')

		# Attempt to intelligently trim the image if its over
		# TODO give user a gutter option
		# TODO give user a scale option
		# TODO move to function
		if size*size < self.tiles['x']['count']*self.tiles['y']['count']:
			path = [ Tile.getPixelForCoord( self.pointsbounds[0], self.tilesbounds, imagesize),
					Tile.getPixelForCoord( self.pointsbounds[1], self.tilesbounds, imagesize) ]
			imagebox = [ [0,0], list(imagesize) ]
			# so here we have a bounding box for the path, can we trim edges of image?
			if imagesize[0] > size * 256:
				# TODO assumption is, we can trim a tile, might need 2 × in future
				if path[1][0] - path [0][0] < imagesize[0] - 256:
					# We can trim
					centrex = (path[1][0] - path [0][0])/2 + path[0][0]
					halfwidth = ((imagesize[0] - 256) / 2)
					imagebox[0][0] = centrex - halfwidth
					imagebox[1][0] = centrex + halfwidth

			if imagesize[1] > size * 256:
				# TODO same as above
				if path[1][1] - path [0][1] < imagesize[1] - 256:
					centrey = (path[1][1] - path [0][1])/2 + path[0][1]
					halfwidth = ((imagesize[1] - 256) / 2)
					imagebox[0][1] = centrey - halfwidth
					imagebox[1][1] = centrey + halfwidth

			imagebox = reduce(lambda x,y: x+y,imagebox)
			image = image.crop( imagebox )

		#trim = int(256/2)
		#image = image.crop( tuple( [trim, trim] + map( lambda x: x-trim, image.size) ) )

		# write file 
		image.save(filename, "PNG")

# Just test data for now
track = GPX()
track.setOptions({'size': 2, 'filename': '2010-07-12_12-18-49.png' })
track.loadFromFile('2010-07-12_12-18-49.gpx')
#track.setOptions({'size': 3, 'filename': 'winchcombe.png' })
#track.loadFromFile('winchcombe.gpx')
track.drawTrack()

