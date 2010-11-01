#/usr/bin/python
# -*- coding: utf-8 -*-

# GPLv3, John Drinkwater <john@nextraweb.com>
# http://johndrinkwater.name/code/gpx2png/

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

# TODO read file

# assuming we track data here, loop to calc tiles needed
