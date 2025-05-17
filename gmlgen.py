import xml.etree.ElementTree as etree
import xml.dom.minidom
from enum import Enum
from datetime import *
from urnparse import * 

def genInner(parent, name, text="TODO", attribs={}):
	child = etree.SubElement(parent,name,attribs)
	child.text = text
	return child

### Generic datatypes

#12.4 print outs from datetime
def datetime_out(dt:datetime):
	return datetime.isoformat(dt.replace(tzinfo=None),timespec='seconds') + "Z"

#17.1.1 coordinate 
def latlong_out(lat:float, long:float, multX:float=1, multY:float=1):
	# 7 places after the decimal (though trailing 0s could be omitted in the future)
	assert(lat < 90 and lat > -90)
	assert(long < 360 and long > -360) #TODO
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

datasetPurposeText = {
	datasetPurpose.base: "Base",
	datasetPurpose.update: "Update"
}

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

	def __init__(self, nameIn:str, usageIn:nameUsage=nameUsage.defaultNameDisplay, lang:str="eng"):
		self.language = lang
		self.name = nameIn
		self.nameusage = usageIn
	
	def gengml(self, parent):
		featureName = etree.SubElement(parent, "featureName")
		genInner(featureName,"language",self.language)
		genInner(featureName, "name", self.name)
		genInner(featureName, "nameUsage", NameUsageText[self.usage], {"code":str(self.usage.value)})

class fixedTimeRange:
	timeStart:datetime
	timeEnd:datetime

	def __init__(self, startIn:datetime, endIn:datetime):
		self.timeStart = startIn
		self.timeEnd = endIn

	def gengml(self, parent):
		range = etree.SubElement(parent, "fixedTimeRange")
		genInner(range, "timeStart", datetime_out(self.timeStart))
		genInner(range, "timeEnd", datetime_out(self.timeEnd))


def generateRoot(id="TODO"):
	return etree.Element("Dataset",{
		"xmlns:S100":"http://www.iho.int/s100gml/5.0",
		"xmlns:gml":"http://www.opengis.net/gml/3.2",
		"gml:id":id,
		"xmlns":"http://www.iho.int/S129/2.0"
	})

def generateBoundary(parent, positions):
	boundary = etree.SubElement(parent,"gml:boundedBy")
	envelope = etree.SubElement(boundary,"gml:Envelope",{
		"srsName":"http://www.opengis.net/def/crs/EPSG/0/4326",
		"srsDimensions":"2"
	})
	genInner(envelope,"gml:lowerCorner", latlong_out(10,10))
	genInner(envelope,"gml:upperCorner", latlong_out(-10,-10))
	return boundary

def generateDatasetIdentificationInfo(parent, fileName:str, updateNo=0, title="Test Dataset Saint John, NB"):
	profile = applicationProfileText[applicationProfile.base_dataset]
	purpose = datasetPurposeText[datasetPurpose.base]
	if updateNo != 0:
		profile = applicationProfileText[applicationProfile.update_dataset]
		purpose = datasetPurposeText[datasetPurpose.update]
		
	identificatioInfo = etree.SubElement(parent,"S100:DatasetIdentificationInformation")
	genInner(identificatioInfo,"S100:encodingSpecification","S-100 Part 10b")
	genInner(identificatioInfo,"S100:encodingSpecificationEdition","1.0")
	genInner(identificatioInfo,"S100:productIdentifier","S-129")
	genInner(identificatioInfo,"S100:productEdition","2.0.0")
	genInner(identificatioInfo,"S100:applicationProfile", profile)
	genInner(identificatioInfo,"S100:datasetFileIdentifier",fileName)
	genInner(identificatioInfo,"S100:datasetTitle",title)
	genInner(identificatioInfo,"S100:datasetReferenceDate",date.isoformat(date.today()))
	genInner(identificatioInfo,"S100:datasetLanguage","eng")
	#TODO: "Dataset Abstract"

	#ISO 19115-1 code, but oceans seems to always be the most relevant
	genInner(identificatioInfo,"S100:datasetTopicCategory","oceans") 
	genInner(identificatioInfo,"S100:datasetPurpose",purpose)
	genInner(identificatioInfo,"S100:updateNumber",str(updateNo))
	return identificatioInfo

def generateUnderKeelClearancePlan(parent, 
		maxDraught:float,
		routeName:str="Saint John Test Plan",
		routeVersion:str="1234567", #interop number to specify what S-421 (421.Route.routeEditionNo) or RTZ plan to use 
		vesselId:str="1234567", #IMO, likely 7 digit number
		purpose:underKeelClearancePurpose = underKeelClearancePurpose.actualPlan,
		calc:underKeelClearanceCalculationRequested = underKeelClearanceCalculationRequested.timeWindow,
		):
	plan = etree.SubElement(parent,"UnderKeelClearancePlan",{"gml:id":"TODO_Plan_ID"})
	genInner(plan,"generationTime",datetime_out(datetime.now(timezone.utc)))
	genInner(plan,"vesselID",vesselId)
	genInner(plan,"sourceRouteName",routeName)
	genInner(plan,"sourceRouteVersion",routeVersion)
	genInner(plan,"maximumDraught",str(maxDraught))
	genInner(plan,"underKeelClearancePurpose", ClearancePurposeText[purpose],{"code":str(purpose.value)})
	genInner(plan,"underKeelClearanceCalculationRequested",CalculationRequestedText[calc],{"code":str(calc.value)})

def generatePlanArea(parent):
	#TODO: boundary rect...
	#TODO: scaleMinimum
	#TODO: URN
	#TODO: GM_OrientableSurface...
	pass

def generateNonNavArea(parent):
	#TODO: scaleMinimum
	#TODO: URN
	#TODO: GM_OrientableSurface...
	pass

def generateAlmostNonNavArea(parent):
	#TODO: distanceAboveUKCLimit
	#TODO: scaleMinimum
	#TODO: URN
	#TODO: GM_OrientableSurface...
	pass

def generatePoint(parent, id:str, lat:float, long:float):
	geo = etree.SubElement(parent, "geometry")
	ptProperty = etree.SubElement(geo, "S100:pointProperty")
	pt = etree.SubElement(ptProperty, "S100:Point", {"gml:id":id})
	genInner(pt, "gml:pos", latlong_out(lat,long))
	return geo

def generateClearancePt(parent, cp_num:str, passingTime:datetime, speed:float, distAboveUKCLim:float, lat:float, long:float):
	#perhaps we will want leading 0s for the name in the future
	cp_name = "CP_"+cp_num
	controlPt = etree.SubElement(parent, "UnderClearanceControlPoint", {"gml:id":cp_name})
	featureName("CP"+cp_num).gengml(controlPt)
	genInner(controlPt,"expectedPassingTime",datetime_out(passingTime))
	genInner(controlPt,"expectedPassingSpeed",str(speed))
	genInner(controlPt,"distanceAboveUKCLimit",str(distAboveUKCLim))
	# TODO: fixed time range
	# TODO: URN
	generatePoint(controlPt,cp_name+"_GEOM",lat,long)

def printxml(element, **kwargs):
	myxml = etree.tostring(element, xml_declaration=True, encoding="utf-8", **kwargs)
	print(xml.dom.minidom.parseString(myxml.decode()).toprettyxml(), end='')

def writeout(fileName, element, **kwargs):
	myxml = etree.tostring(element, xml_declaration=True, encoding="utf-8", **kwargs)
	file = open(fileName, "w")
	file.write(xml.dom.minidom.parseString(myxml.decode()).toprettyxml())
	file.close()

def genFileName(issuerID:str,uniqueName:str=""):
	#TODO: more graceful error handling?
	assert(len(issuerID) == 4)
	assert(len(uniqueName) <= 8)
	#TODO: check uniqueName has characters in the set {A-Z, 0-9, _}
	return "129" + issuerID + uniqueName + ".gml"

if __name__ == "__main__":
	fileName = genFileName("STJN","TEST0000")
	maxVesselDraught = 5.1

	root = generateRoot()
	generateBoundary(root,[10, 10, -10, -10])
	generateDatasetIdentificationInfo(root,fileName)
	members = etree.SubElement(root,"members")
	generateUnderKeelClearancePlan(members,maxVesselDraught)
	for i in range(5):
		generateClearancePt(members,
			str(i),
			datetime.now() + timedelta(hours=i),
			i*0.1,
			0.5,
			-10+i*0.1,140+i*0.1
		)
	#printxml(root)
	writeout(fileName,root)

# urn: https://events.iala.int/content/uploads/2021/11/MRN-value-and-use-_Minsu-Jeon-2.pdf
# https://pypi.org/project/urnparse/, figure out URNs later