from lxml import etree
import xml.dom.minidom
from enum import Enum
from datetime import *
#from urnparse import * 

#""" add to parent a new child with name name, inner text text, and attributes as an object
#"""
def genInner(parent:etree.Element, name:str, text:str="TODO", attribs:object={}):
	child = etree.SubElement(parent,name,attribs)
	child.text = text
	return child

### Generic datatypes

#12.4 print outs from datetime
def datetime_out(dt:datetime) -> str:
	return datetime.isoformat(dt.replace(tzinfo=None),timespec='seconds') + "Z"

#17.1.1 coordinate 
def latlong_out(lat:float, long:float, multX:float=1, multY:float=1) -> str:
	# 7 places after the decimal (though trailing 0s could be omitted in the future)
	#assert(lat < 90 and lat > -90)
	#assert(long < 360 and long > -360) #TODO
	return "{:.7f} {:.7f}".format(lat*multX, long*multY)

### S-100 (10b-11.6) datatypes
class applicationProfile(Enum):
	base_dataset = 1
	update_dataset = 2

applicationProfileText = {
	applicationProfile.base_dataset: "1",
	applicationProfile.update_dataset: "2"
}

class datasetPurpose(Enum):
	base = 1
	update = 2

#NIWC wants lower case letters
datasetPurposeText = {
	datasetPurpose.base: "base", 
	datasetPurpose.update: "update"
}

"""## S100_Purpose (S-100 Part 17, Clause 17-4.5)
#must be 2 "new edition" (default) or 5 "cancellation"
#TODO" is this necessary?
class s100_purpose(Enum):
    newDataset = 1
    newEdition = 2
    update = 3
    reissue = 4
    cancellation = 5
    delta = 6
"""

### S-129 datatypes

class underKeelClearancePurpose(Enum):
	prePlan = 1
	actualPlan = 2
	actualUpdate = 3

class underKeelClearanceCalculationRequested(Enum):
	timeWindow = 1
	maxDraught = 2

class nameUsage(Enum):
	defaultNameDisplay = 1
	alternateNameDisplay = 2

ClearancePurposeText = {
	underKeelClearancePurpose.prePlan: "Pre-plan",
	underKeelClearancePurpose.actualPlan: "Actual Plan",
	underKeelClearancePurpose.actualUpdate: "Actual Update"
}

CalculationRequestedText = {
	underKeelClearanceCalculationRequested.timeWindow: "Time Window",
	underKeelClearanceCalculationRequested.maxDraught: "Max Draught"
}

NameUsageText = {
	nameUsage.defaultNameDisplay: "Default Name Display",
	nameUsage.alternateNameDisplay: "Alternative Name Display"
}

class featureName:
	language:str = ""
	name:str = ""
	usage:nameUsage = nameUsage.defaultNameDisplay

	def __init__(self, nameIn:str, usageIn:nameUsage=nameUsage.defaultNameDisplay, lang:str="eng") -> None:
		self.language = lang
		self.name = nameIn
		self.nameusage = usageIn
	
	def gengml(self, parent:etree.Element) -> None:
		featureName = etree.SubElement(parent, "featureName")
		genInner(featureName,"language",self.language)
		genInner(featureName, "name", self.name)
		genInner(featureName, "nameUsage", NameUsageText[self.usage], {"code":str(self.usage.value)})

class fixedTimeRange:
	timeStart:datetime
	timeEnd:datetime

	def __init__(self, startIn:datetime, endIn:datetime) -> None:
		self.timeStart = startIn
		self.timeEnd = endIn

	def gengml(self, parent:etree.Element) -> None:
		range = etree.SubElement(parent, "fixedTimeRange")
		genInner(range, "timeStart", datetime_out(self.timeStart))
		genInner(range, "timeEnd", datetime_out(self.timeEnd))

#namespace prefix globals for lxml
GML = "{http://www.opengis.net/gml/3.2}"
S100 = "{http://www.iho.int/s100gml/5.0}"
S129 = "{http://www.iho.int/S129/2.0}"

def generateRoot(id:str="TODO") -> etree.Element:
	nsmap = {
		None: "http://www.iho.int/S129/2.0", #default namespace
		"S100":"http://www.iho.int/s100gml/5.0",
		"gml":"http://www.opengis.net/gml/3.2",
	}
	attribs = {
		GML+"id":id,
	}
	el = etree.Element("Dataset",
                    attrib=attribs,
                    nsmap=nsmap)
	return el

#TODO: get rid of hard coded EPSG, use the one provided by
#the bathymetry
def generateBoundary(parent:etree.Element, bounds:object) -> etree.Element:
	boundary = etree.SubElement(parent,GML+"boundedBy")
	envelope = etree.SubElement(boundary,GML+"Envelope",{
		"srsName":"http://www.opengis.net/def/crs/EPSG/0/4326",
		"srsDimensions":"2"
	})
	genInner(envelope,GML+"lowerCorner", latlong_out(bounds["min"][0],bounds["min"][1]))
	genInner(envelope,GML+"upperCorner", latlong_out(bounds["max"][0],bounds["max"][1]))
	return boundary

def generateDatasetIdentificationInfo(parent:etree.Element, fileName:str, updateNo=0, title="Test Dataset Saint John, NB")  -> etree.Element:
	profile = applicationProfileText[applicationProfile.base_dataset]
	purpose = datasetPurposeText[datasetPurpose.base]
	if updateNo != 0:
		profile = applicationProfileText[applicationProfile.update_dataset]
		purpose = datasetPurposeText[datasetPurpose.update]
		
	identificatioInfo = etree.SubElement(parent,S100+"DatasetIdentificationInformation")
	genInner(identificatioInfo,S100+"encodingSpecification","S-100 Part 10b")
	genInner(identificatioInfo,S100+"encodingSpecificationEdition","1.0")
	genInner(identificatioInfo,S100+"productIdentifier","S-129")
	genInner(identificatioInfo,S100+"productEdition","2.0.0")
	genInner(identificatioInfo,S100+"applicationProfile", profile)
	genInner(identificatioInfo,S100+"datasetFileIdentifier",fileName)
	genInner(identificatioInfo,S100+"datasetTitle",title)
	genInner(identificatioInfo,S100+"datasetReferenceDate",date.isoformat(date.today()))
	genInner(identificatioInfo,S100+"datasetLanguage","eng")
	#TODO: "Dataset Abstract"

	#ISO 19115-1 code, but oceans seems to always be the most relevant
	genInner(identificatioInfo,S100+"datasetTopicCategory","oceans") 
	genInner(identificatioInfo,S100+"datasetPurpose",purpose)
	genInner(identificatioInfo,S100+"updateNumber",str(updateNo))
	return identificatioInfo

def generateUnderKeelClearancePlan(parent:etree.Element, 
		maxDraught:float,
		routeName:str="Saint John Test Plan",
		routeVersion:str="1234567", #interop number to specify what S-421 (421.Route.routeEditionNo) or RTZ plan to use 
		vesselId:str="1234567", #IMO, likely 7 digit number
		purpose:underKeelClearancePurpose = underKeelClearancePurpose.actualPlan,
		calc:underKeelClearanceCalculationRequested = underKeelClearanceCalculationRequested.timeWindow,
		) -> None:
	plan = etree.SubElement(parent,"UnderKeelClearancePlan",{GML+"id":"TODO_Plan_ID"})
	genInner(plan,"generationTime",datetime_out(datetime.now(timezone.utc)))
	genInner(plan,"vesselID",vesselId)
	genInner(plan,"sourceRouteName",routeName)
	genInner(plan,"sourceRouteVersion",routeVersion)
	genInner(plan,"maximumDraught",str(maxDraught))
	genInner(plan,"underKeelClearancePurpose", ClearancePurposeText[purpose],{"code":str(purpose.value)})
	genInner(plan,"underKeelClearanceCalculationRequested",CalculationRequestedText[calc],{"code":str(calc.value)})

def genArea(parent:etree.Element, id:str, gml:str, bounds:object=None) -> None:
	if bounds != None:
		generateBoundary(parent,bounds)
	geo = etree.SubElement(parent, "geometry")
	surProperty = etree.SubElement(geo, S100+"surfaceProperty")
	surface:etree.Element = etree.SubElement(surProperty,S100+"Surface",{
	#genInner(surProperty,S100+"Surface",gml,{
		GML+"id":id,
		"srsName":"http://www.opengis.net/def/crs/EPSG/0/4326",
		"srsDimension":"2"
		})
	parser = etree.XMLParser(encoding="utf-8", recover=True)
	subel:etree.Element = etree.fromstring(gml,parser)
	surface.append(subel)
	
	#patches = etree.SubElement(surface,GML+"patches")
	#polygon = etree.SubElement(patches,GML+"PolygonPatch")
	#ext = etree.SubElement(polygon,GML+"exterior")
	#linRing = etree.SubElement(ext,GML+"LinearRing")
	#posList = genInner(linRing,GML+"posList","TODO TODO TODO TODO TODO TODO TODO TODO")

def generatePlanArea(parent:etree.Element, gml:str, bounds:object) -> None:
	planArea = etree.SubElement(parent,"UnderKeelClearancePlanArea",
		{GML+"id":"TEST_PLAN_AREA_SAINT_JOHN"})
	genInner(planArea,"scaleMinimum","1") #TODO
	genArea(planArea, "TEST_PLAN_AREA_GEOM", gml, bounds)
	#TODO: boundary rect...
	#TODO: scaleMinimum
	#TODO: URN
	#TODO: GM_OrientableSurface...

def generateNonNavArea(parent:etree.Element, gml:str, iter:int=0) -> None:
	id = "NON_NAVIGABLE_"+str(iter)
	nonNavArea = etree.SubElement(parent,"UnderKeelClearanceNonNavigableArea",
		{GML+"id":id})
	genInner(nonNavArea,"scaleMinimum","1") #TODO
	genArea(nonNavArea,id+"_GEOM", gml)
	#TODO: scaleMinimum
	#TODO: URN
	#TODO: GM_OrientableSurface...

def generateAlmostNonNavArea(parent:etree.Element, gml:str, iter:int=0) -> None:
	id = "ALMOST_NON_NAVIGABLE_"+str(iter)
	almostNonNavArea = etree.SubElement(parent,"UnderKeelClearanceAlmostNonNavigableArea",
		{GML+"id":id})
	genInner(almostNonNavArea,"scaleMinimum","1") #TODO
	genInner(almostNonNavArea, "distanceAboveUKCLimit","0.2") #TODO
	genArea(almostNonNavArea,id+"_GEOM", gml)
	#TODO: distanceAboveUKCLimit
	#TODO: scaleMinimum
	#TODO: URN
	#TODO: GM_OrientableSurface...
	pass

def generatePoint(parent:etree.Element, id:str, lat:float, long:float) -> etree.Element:
	geo = etree.SubElement(parent, "geometry")
	ptProperty = etree.SubElement(geo, S100+"pointProperty")
	pt = etree.SubElement(ptProperty, S100+"Point", {GML+"id":id})
	genInner(pt, GML+"pos", latlong_out(lat,long))
	return geo

def generateClearancePt(parent:etree.Element, cp_num:str, passingTime:datetime, speed:float, distAboveUKCLim:float, lat:float, long:float) -> None:
	#perhaps we will want leading 0s for the name in the future
	cp_name = "CP_"+cp_num
	controlPt = etree.SubElement(parent, "UnderKeelClearanceControlPoint", {GML+"id":cp_name})
	featureName("CP"+cp_num).gengml(controlPt)
	genInner(controlPt,"expectedPassingTime",datetime_out(passingTime))
	genInner(controlPt,"expectedPassingSpeed",str(speed))
	genInner(controlPt,"distanceAboveUKCLimit",str(distAboveUKCLim))
	# TODO: fixed time range
	# TODO: URN
	generatePoint(controlPt,cp_name+"_GEOM",lat,long)

def printxml(element:etree.Element, **kwargs) -> None:
	myxml = etree.tostring(element, xml_declaration=True, encoding="utf-8", **kwargs)
	print(xml.dom.minidom.parseString(myxml.decode()).toprettyxml(), end='')

def writeout(fileName:str, element:etree.Element, **kwargs):
	myxml = etree.tostring(element, xml_declaration=True, encoding="utf-8", **kwargs)
	file = open(fileName, "w")
	file.write(xml.dom.minidom.parseString(myxml.decode()).toprettyxml())
	file.close()

def genFileName(issuerID:str,uniqueName:str="") -> str:
	#TODO: more graceful error handling?
	assert(len(issuerID) == 4)
	assert(len(uniqueName) <= 8)
	#TODO: check uniqueName has characters in the set {A-Z, 0-9, _}
	return "129" + issuerID + uniqueName + ".gml"

if __name__ == "__main__":
	fileName = genFileName("STJN","TEST0000")
	maxVesselDraught = 5.1
	bounds = {"min":[10, 10],"max":[-10, -10]}

	root = generateRoot()
	generateBoundary(root,bounds)
	generateDatasetIdentificationInfo(root,fileName)

	test_gml = """<gml:patches><gml:PolygonPatch><gml:exterior><gml:LinearRing><gml:posList>TODO TODO TODO TODO TODO TODO TODO TODO</gml:posList></gml:LinearRing></gml:exterior></gml:PolygonPatch></gml:patches>"""
	
	members = etree.SubElement(root,"members")
	generateUnderKeelClearancePlan(members,maxVesselDraught)
	generatePlanArea(members,test_gml, bounds)

	generateNonNavArea(members,test_gml)
	generateAlmostNonNavArea(members,test_gml)
	for i in range(5):
		generateClearancePt(members,
			str(i),
			datetime.now() + timedelta(hours=i),
			1+i*0.1,
			0.5,
			-10+i*0.1,140+i*0.1
		)
	#printxml(root)
	writeout(fileName,root)

# urn: https://events.iala.int/content/uploads/2021/11/MRN-value-and-use-_Minsu-Jeon-2.pdf
# https://pypi.org/project/urnparse/, figure out URNs later