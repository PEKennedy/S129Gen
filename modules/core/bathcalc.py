##%matplotlib ipympl # https://matplotlib.org/ipympl/

#import unittest
from osgeo import gdal, ogr, osr
import numpy as np

#TODO: Allow per-pixel clearance calculation (callback function likely)
#TODO: Allow combo of multiple bathymetry sources

def get_unsafe_areas(unsafe_level:float, almost_safe_level:float, input_file:str) -> None | object:
	gdal.UseExceptions()
	dataset:gdal.Dataset = gdal.Open(input_file, gdal.GA_ReadOnly)
	if not dataset:
		print("Failed to load")
		return None

	#get projection
	srs = osr.SpatialReference()
	srs.ImportFromWkt(dataset.GetProjectionRef())
	target_ref = osr.SpatialReference()
	target_ref.ImportFromEPSG(4326)
	coord_tr = osr.CoordinateTransformation(srs,target_ref)

	#Get the elevation band
	el_band:gdal.Band = dataset.GetRasterBand(1) #bag band 1: elevation
	el_band.ReadRaster()
	#TODO: Clip based on plan area
	print(unsafe_level)
	print(almost_safe_level)
	# Reclassify based on safe clearance
	arr = el_band.ReadAsArray()
	nodataval = el_band.GetNoDataValue()
	out = np.full_like(arr, 0)
	#clearance = np.full_like(arr, 0) #clearance values for the almost-navigable areas
	for i in range(out.shape[0]):
		for j in range(out.shape[1]):
			val = arr[i,j]
			if val == nodataval:
				out[i,j] = 0
			elif unsafe_level <= val:
				out[i,j] = 3
			elif almost_safe_level <= val:
				out[i,j] = 2
			else:
				out[i,j] = 1

	scanned = np.where(out != 0, 1,0)
	unsafe = np.where(out == 3, 1,0)
	almost_safe = np.where(out == 2, 1,0)

	gdal_mem_driver:gdal.Driver = gdal.GetDriverByName("MEM")
	tmp_dataset:gdal.Dataset = gdal_mem_driver.CreateCopy('',dataset,0)
	scanned_band:gdal.Band = tmp_dataset.GetRasterBand(1) #Get the default band 1 #unsafe_band
 
	tmp_dataset.AddBand(gdal.GFT_Real)
	tmp_dataset.AddBand(gdal.GFT_Real)

	almost_safe_band:gdal.Band = tmp_dataset.GetRasterBand(2)
	unsafe_band:gdal.Band = tmp_dataset.GetRasterBand(3) #scanned_band

	unsafe_band.WriteArray(unsafe)
	almost_safe_band.WriteArray(almost_safe)
	scanned_band.WriteArray(scanned) #actually want plan area, since safe area is implied

	# Polygonize
 	#https://github.com/OSGeo/gdal/blob/master/autotest/alg/polygonize.py
	# in memory data source to put results in
	ogr_mem_driver:ogr.Driver = ogr.GetDriverByName('MEM')
	mem_datasource:ogr.DataSource = ogr_mem_driver.CreateDataSource("out")
	mem_layer_scanned:ogr.Layer = mem_datasource.CreateLayer("scanned", None, ogr.wkbMultiPolygon)#ogr.wkbLinearRing) #lin ring so 1 feature?
	mem_layer_unsafe:ogr.Layer = mem_datasource.CreateLayer("unsafe",None,ogr.wkbMultiPolygon)	
	mem_layer_almost_safe:ogr.Layer = mem_datasource.CreateLayer("almost_safe",None,ogr.wkbMultiPolygon)
 
	mem_field = ogr.FieldDefn("DN",ogr.OFTReal)
	mem_layer_scanned.CreateField(mem_field)
	mem_layer_unsafe.CreateField(mem_field)
	mem_layer_almost_safe.CreateField(mem_field)

	gdal.FPolygonize(scanned_band,None,mem_layer_scanned,0)
	gdal.FPolygonize(unsafe_band,None,mem_layer_unsafe,0)
	gdal.FPolygonize(almost_safe_band,None,mem_layer_almost_safe,0)

	#Free memory
	#mem_datasource = None

	#separate by value (unsafe, almost safe), safe is implied by plan area
	print("feature counts (scanned, non-nav, almost-nav):")
	print(mem_layer_scanned.GetFeatureCount())
	print(mem_layer_unsafe.GetFeatureCount())
	print(mem_layer_almost_safe.GetFeatureCount())

	bounds = {}
	unnavigable_areas = []
	almost_unnavigable_areas = []

	gml_settings = {"FORMAT":"GML3.2", "SRSNAME_FORMAT":"SHORT"}
	#export to GML
	combined_geo:ogr.Geometry = ogr.Geometry(ogr.wkbGeometryCollection)#ogr.wkbMultiPolygon)#ogr.wkbGeometryCollection)
	for i in range(mem_layer_scanned.GetFeatureCount()-1):
		feature:ogr.Feature = mem_layer_scanned.GetFeature(i)
		geom:ogr.Geometry = feature.geometry()
		geom.AssignSpatialReference(srs)
		geom.Transform(coord_tr) #.SetPrecision(...) or .roundCoordinates()
		geom.CloseRings()
		combined_geo.AddGeometry(geom)

		bounds = geom.GetEnvelope() #minx: float maxx: float miny: float maxy: float
		bounds = {"min":[bounds[0],bounds[2]], "max": [bounds[1],bounds[3]]}

	#double ratio, bool allow holes. This silently crashes now??
	combined_geo = combined_geo.ConcaveHull(0.4,True)
	combined_geo.CloseRings()

	scanned_areas:str = combined_geo.ExportToGML(options=gml_settings)
	#print("xyz")
	#-1 because the last feature in the list is everything outside the unsafe areas
	for i in range(mem_layer_unsafe.GetFeatureCount()-1):
		feature:ogr.Feature = mem_layer_unsafe.GetFeature(i)
		geom:ogr.Geometry = feature.geometry()
		geom.BuildArea()
		geom.AssignSpatialReference(srs)
		geom.Transform(coord_tr)
		geom.CloseRings()
		geo_str = geom.ExportToGML(options=gml_settings)
		unnavigable_areas.append(geo_str)

	for i in range(mem_layer_almost_safe.GetFeatureCount()-1):
		feature:ogr.Feature = mem_layer_almost_safe.GetFeature(i)
		geom:ogr.Geometry = feature.geometry()
		geom.AssignSpatialReference(srs)
		geom.Transform(coord_tr)
		geom.CloseRings()
		geo_str = geom.ExportToGML(options=gml_settings)
		almost_unnavigable_areas.append(geo_str)

	return {
		"bounds":  bounds,
		"scanned": scanned_areas,
		"non_nav": unnavigable_areas,
		"almost_non_nav": almost_unnavigable_areas
	}

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