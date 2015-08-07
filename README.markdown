A small tool to produce images of your GPS track breadcrumbs over the top of
OSM mapping tile data.

Naïvely supports GPX, KML and KMZ files. If you have any other formats, for the
time being you can use `gpsbabel` to convert into GPX, and leave an issue if
you would like it natively supported.

<img src="example.png"><br />
To produce the above image from <b>example.kmz</b>, run <code><kbd>./gpx2png.py example.kmz</kbd></code>

TODO: this was made before the OSM move to a new licence, and needs further
work to support extra file types - as it appears the kml output from Tracks on
Android is not compatible with gpsbabel.
