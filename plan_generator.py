from modules.core import bathcalc as bc, gmlgen as gg
from modules.regional import livedat as ld
from datetime import *
from lxml import etree

#margins
KEEL_UNSAFE = 1.1 #based on SJ port procedures
KEEL_ALMOST_SAFE = 1.2 #arbitrary

if __name__=="__main__":
	# Get vessel, water, and bathymetry info
	maxVesselDraught = 5.1
	#VesselVel = [1,1]
	tide = 1
 
	#Generate root
	fileName = gg.genFileName("STJN","TEST0001")
	root = gg.generateRoot()
	
	#Get Areas
	unsafe_level = tide - (maxVesselDraught*KEEL_UNSAFE)
	almost_safe_level = tide - (maxVesselDraught*KEEL_ALMOST_SAFE)
	areas = bc.get_unsafe_areas(unsafe_level,almost_safe_level,"STJohn_bath_1.tif")

	#Generate metadata
	bounds = areas["bounds"]
	gg.generateBoundary(root,bounds)
	gg.generateDatasetIdentificationInfo(root,fileName)

	#Generate gml areas
	members = etree.SubElement(root,"members")
	gg.generateUnderKeelClearancePlan(members,maxVesselDraught)
	
	scanned_area = areas["scanned"][0]
	gg.generatePlanArea(members, scanned_area, bounds)

	i:int = 0
	for area in areas["non_nav"]:
		gg.generateNonNavArea(members,area,i)
		i += 1

	i:int = 0
	for area in areas["almost_non_nav"]:
		gg.generateAlmostNonNavArea(members,area, i)
		i += 1

	#Add waypoints (TODO)
	for i in range(5):
		gg.generateClearancePt(members,
			str(i),
			datetime.now() + timedelta(hours=i),
			1+i*0.1,
			0.5,
			-10+i*0.1,140+i*0.1
		)
	#printxml(root)

	gg.writeout("out/"+fileName,root)