#%%

##%matplotlib ipympl # https://matplotlib.org/ipympl/

import unittest
from osgeo import gdal, ogr, osr #ogr is vec, gdal is raster
import matplotlib.pyplot as plt
import numpy as np
import rasterio
from affine import Affine
import rasterio.features
from shapely.geometry import shape

#https://gis.stackexchange.com/questions/128139/how-to-convert-float-raster-to-vector-with-python-gdal
#https://gdal.org/en/stable/api/python/osgeo.gdal.html#osgeo.gdal.FPolygonize
#https://gdal.org/en/stable/programs/gdal_raster_polygonize.html

#TODO: Allow per-pixel clearance calculation (callback function likely)
#TODO: Return plan area as polygonization of scanned area
#TODO: Allow combo of multiple bathymetry sources?

def get_unsafe_areas(unsafe_level:float, almost_safe_level:float, input_file:str) -> None | object:
	dataset:gdal.Dataset = gdal.Open(input_file, gdal.GA_ReadOnly)
	if not dataset:
		print("Failed to load")
		return None
		"""return {
			"scanned":None
			"non_nav":None,
			"almost_non_nav":None
		}"""
	gdal.SetConfigOption("OGR_ORGANIZE_POLYGONS","ONLY_CCW")
	#src_driver:gdal.Driver = dataset.GetDriver()
 
	#get projection
	srs = osr.SpatialReference()
	srs.ImportFromWkt(dataset.GetProjectionRef())

	#Get the elevation band
	el_band:gdal.Band = dataset.GetRasterBand(1) #bag band 1: elevation

	#TODO: Clip based on plan area

	# Reclassify based on safe clearance
	arr = el_band.ReadAsArray()

	#conditions are inverted because depth is + in the numbers, but ?- in the raster?
	scanned = np.where(arr != None, 1,0)
	unsafe = np.where(unsafe_level <= arr,1,0)
	almost_safe = np.where(np.logical_and(almost_safe_level <= arr, arr < unsafe_level),1,0)
	#safe = np.where(almost_safe_level > arr,1,0)	

	gdal_mem_driver:gdal.Driver = gdal.GetDriverByName("MEM")
	tmp_dataset:gdal.Dataset = gdal_mem_driver.CreateCopy('',dataset,0)
	unsafe_band:gdal.Band = tmp_dataset.GetRasterBand(1) #Get the default band 1
	
	tmp_dataset.AddBand(gdal.GFT_Real)
	tmp_dataset.AddBand(gdal.GFT_Real)

	almost_safe_band:gdal.Band = tmp_dataset.GetRasterBand(2)
	scanned_band:gdal.Band = tmp_dataset.GetRasterBand(3)

	#reclass_band.WriteArray(reclass)
	unsafe_band.WriteArray(unsafe)
	almost_safe_band.WriteArray(almost_safe)
	scanned_band.WriteArray(scanned) #actually want plan area, since safe area is implied
 
 	# .........
	"""plt.figure()
	plt.imshow(unsafe)

	plt.figure()
	plt.imshow(almost_safe)

	plt.figure()
	plt.imshow(safe)"""

	# Polygonize
 	#https://github.com/OSGeo/gdal/blob/master/autotest/alg/polygonize.py
	# in memory data source to put results in
	ogr_mem_driver:ogr.Driver = ogr.GetDriverByName('MEMORY')
	mem_datasource:ogr.DataSource = ogr_mem_driver.CreateDataSource("out")
	mem_layer_scanned:ogr.Layer = mem_datasource.CreateLayer("scanned", None, ogr.wkbLinearRing) #lin ring so 1 feature?
	mem_layer_unsafe:ogr.Layer = mem_datasource.CreateLayer("unsafe",None,ogr.wkbMultiPolygon)	
	mem_layer_almost_safe:ogr.Layer = mem_datasource.CreateLayer("almost_safe",None,ogr.wkbMultiPolygon)
 
 	#is this necessary?? >> yes it is
	#what does "DN" stand for?
	mem_field = ogr.FieldDefn("DN",ogr.OFTReal)
	mem_layer_scanned.CreateField(mem_field)
	mem_layer_unsafe.CreateField(mem_field)
	mem_layer_almost_safe.CreateField(mem_field)

	gdal.FPolygonize(scanned_band,None,mem_layer_scanned,0)
	gdal.FPolygonize(unsafe_band,None,mem_layer_unsafe,0)
	gdal.FPolygonize(almost_safe_band,None,mem_layer_almost_safe,0)

	#separate by value (unsafe, almost safe), safe is implied by plan area
	print("feature counts (scanned, non-nav, almost-nav):")
	print(mem_layer_scanned.GetFeatureCount())
	print(mem_layer_unsafe.GetFeatureCount())
	print(mem_layer_almost_safe.GetFeatureCount())

	bounds = {}
	scanned_areas = []
	unnavigable_areas = []
	almost_unnavigable_areas = []

	#export to GML
	for i in range(mem_layer_scanned.GetFeatureCount()):
		feature:ogr.Feature = mem_layer_scanned.GetFeature(i)
		geom:ogr.Geometry = feature.geometry()
		geom.AssignSpatialReference(srs)
		bounds = geom.GetEnvelope() #minx: float maxx: float miny: float maxy: float
		#print(bounds)
		bounds = {"min":[bounds[0],bounds[2]], "max": [bounds[1],bounds[3]]}
		scanned_areas.append(geom.ExportToGML())

	for i in range(mem_layer_unsafe.GetFeatureCount()):
		feature:ogr.Feature = mem_layer_unsafe.GetFeature(i)
		geom:ogr.Geometry = feature.geometry()
		geom.AssignSpatialReference(srs)
		unnavigable_areas.append(geom.ExportToGML())
	
	for i in range(mem_layer_almost_safe.GetFeatureCount()):
		feature:ogr.Feature = mem_layer_almost_safe.GetFeature(i)
		geom:ogr.Geometry = feature.geometry()
		geom.AssignSpatialReference(srs)
		almost_unnavigable_areas.append(geom.ExportToGML())

	return {
		"bounds": bounds,
		"scanned": scanned_areas,
		"non_nav":unnavigable_areas,
		"almost_non_nav":almost_unnavigable_areas
	}

# %%

if __name__ == "__main__":
	tide = 1
	keel = 6
	keel_clearance_unsafe = 1.1 #based on SJ port procedures
	keel_clearance_almost_safe = 1.2 #arbitrary

	unsafe_level = tide - (keel*keel_clearance_unsafe)
	almost_safe_level = tide - (keel*keel_clearance_almost_safe)
 
	areas = get_unsafe_areas(unsafe_level,almost_safe_level,"STJohn_bath_1.tif")

	with open("out/unnav.gml", "w") as f1:
		f1.writelines(areas["non_nav"])
		f1.close()

	with open("out/almost_unnav.gml", "w") as f2:
		f2.writelines(areas["almost_non_nav"])
		f2.close()