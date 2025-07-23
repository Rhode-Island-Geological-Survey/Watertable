#!/usr/bin/env python3


import sys
import raster # allows the writing of numpy arrays as tiffs (raster)
from osgeo import ogr
from osgeo import gdal
import numpy as np
import random

ogr.UseExceptions()

filename = "Watertable2.gpkg"

ds = ogr.Open(filename)
print(ds)
layer = ds.GetLayerByName("Watertable")
print(layer)
xyz = []

k = 0
shallow = []

# Read in each point, getting (X, Y) and Altitude (watertable)
for f in layer:
    el = f.GetField('watertable')

    if el is None:
        continue
    g = f.GetGeometryRef()
    v = list(g.GetPoint())[:2]
    v.append(el)
    xyz.append(v)

#
# Subsample the data and compute the interpolated surface
# A random sampling of 80% of the data is used
#
def realization(xyz, bounds, N, all = False, r=0, smoothing=0):
    # Sample only 80% of the data
    if all == False:
        idx = random.sample(range(len(xyz)), k = int(len(xyz)*0.80))
        xyz2 = [xyz[i] for i in idx]
        tmp = f"{xyz2}"
    else:
        tmp = f"{xyz}"
    # Construct a geojson Feature Collection
    #  to feed into gdal.Grid() and returning data in memory
    geojson = """{
"type":"FeatureCollection",
"features": [
     {
        "type": "Feature",
        "geometry": {
           "type": "MultiPoint",
           "coordinates": """ + tmp + """,
        },
        "properties": {}
     }
  ]
}"""

    ds2 = gdal.Grid('',
                    geojson,
                    format = 'MEM',
                    outputBounds = bounds,
                    width = int(1000//N),
                    height = int(1048//N),
                    algorithm = f'invdistnn:radius={r}:nodata=-9999.00:smoothing={smoothing};power=2')

    z = np.array(ds2.GetRasterBand(1).ReadAsArray())
    return z

# Convert (X, Y, Z) to a numpy array
t = np.array(xyz)

# Limits and Bounds of the Dataset
print(np.min(t[:,0]),np.max(t[:,0]))
print(np.min(t[:,1]),np.max(t[:,1]))
print(np.min(t[:,2]),np.max(t[:,2]))
print(t.shape)

x0,x1 = np.min(t[:,0]), np.max(t[:,0])
y0,y1 = np.min(t[:,1]), np.max(t[:,1])

bounds = [x0, y0, x1, y1]
print(bounds)

# Interpolation radius (meters)
radius = 25_000  # Same units as data Coordinate systems (meters)

# Total number of simulations of conduct
nsims = 1000
# Population output
out = []

# Value to scale original grid size by
N = 4

# Size of the output grid
#  1000 and 1048 were numbers used at the beginning of the
#  investigation for a particular grid size
#  They are an artifact
nx = int(np.floor(1000 / N))
ny = int(np.floor(1048 / N))

# Grid
X = np.linspace(bounds[0], bounds[2], nx)
Y = np.linspace(bounds[3], bounds[1], ny)
print(Y[0],Y[-1])
print(X[1] - X[0], Y[1] - Y[0])

# Conduct bootstrap to determine mean surface and standard deviation
print("Simulations")
for i in range(nsims):
    if i % 10 == 0:
        print(i)
    z = realization(xyz, bounds, N, smoothing=0, r=radius)
    out.append(z)

out = np.array(out)
mu = np.mean(out, axis=0)
std = np.std(out, axis=0)
zscore = np.abs((zall - mu)/std)

# Interpolation with all ata
zall = realization(xyz, bounds, N, all=True, smoothing = 0, r=radius)

# Write output to tiff
raster.numpy_array_to_raster('watertable_altitude_3438.tiff', zall,
                             (x0,y1), (X[1]-X[0], Y[1]-Y[0]),
                             nband=1, spatial_reference_system_wkid = 3438)
raster.numpy_array_to_raster('watertable_altitude_mean_3438.tiff', mu,
                             (x0,y1), (X[1]-X[0], Y[1]-Y[0]),
                             nband=1, spatial_reference_system_wkid = 3438)
raster.numpy_array_to_raster('watertable_altitude_std_3438.tiff', std,
                             (x0,y1),  (X[1]-X[0], Y[1]-Y[0]),
                             nband=1, spatial_reference_system_wkid = 3438)
raster.numpy_array_to_raster('watertable_altitude_zscore_3438.tiff', zscore,
                             (x0,y1),  (X[1]-X[0], Y[1]-Y[0]),
                             nband=1, spatial_reference_system_wkid = 3438)

# Convert 3438 to 4326 (WGS84)
import subprocess
subprocess.run("gdalwarp -t_srs EPSG:4326 -overwrite watertable_altitude_3438.tiff watertable_altitude.tiff".split())
subprocess.run("gdalwarp -t_srs EPSG:4326 -overwrite watertable_altitude_mean_3438.tiff watertable_altitude_mean.tiff".split())
subprocess.run("gdalwarp -t_srs EPSG:4326 -overwrite watertable_altitude_std_3438.tiff watertable_altitude_std.tiff".split())
subprocess.run("gdalwarp -t_srs EPSG:4326 -overwrite watertable_altitude_zscore_3438.tiff watertable_altitude_zscore.tiff".split())

print("Pixel Size", X[1] - X[0], Y[1]-Y[0])
