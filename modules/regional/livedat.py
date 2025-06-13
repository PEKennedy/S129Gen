### SmartAtlantic data (provided under CC BY 4.0) for anenometer and buoy weather data
### https://www.smartatlantic.ca/terms.html

### Diamond Jubilee Cruise Ship Terminal Meteorological Station
# https://www.smartatlantic.ca/erddap/tabledap/SMA_saint_john_cruise_terminal.csv?
# time%2Cwind_dir_avg%2Cwind_spd_avg%2Cwind_spd_max
# &time%3E=2025-05-10T00%3A00%3A00Z
# &time%3C=2025-05-17T14%3A55%3A00Z

# the var%2Cvar specifies what variables we are using. Possible values:
# station_name, time, degrees_east, degrees_north, wind_dir_avg, wind_spd_avg, wind_spd_max
# station name is always smb_saint_john_cruise_terminal
# long is always -66.06116667, lat is always 45.26683333
# So we don't need to poll those constants

# &time is specifying the constraints. %3A is ":" for the URL, %3C is, %3E is >, %3C is <

#buoy properties. station_name and the lat, longs are fixed
# station_name	time	longitude	latitude	precise_lon	precise_lat	wind_spd_avg	wind_spd_max	wind_dir_avg	air_temp_avg	air_pressure_avg	surface_temp_avg	wave_ht_max	wave_ht_sig	wave_dir_avg	wave_spread_avg	wave_period_max	curr_spd_avg	curr_dir_avg	curr_spd2_avg	curr_dir2_avg	curr_spd3_avg	curr_dir3_avg	curr_spd4_avg	curr_dir4_avg	curr_spd5_avg	curr_dir5_avg	curr_spd6_avg	curr_dir6_avg	curr_spd7_avg	curr_dir7_avg	curr_spd8_avg	curr_dir8_avg	curr_spd9_avg	curr_dir9_avg	curr_spd10_avg	curr_dir10_avg	curr_spd11_avg	curr_dir11_avg	curr_spd12_avg	curr_dir12_avg	curr_spd13_avg	curr_dir13_avg	curr_spd14_avg	curr_dir14_avg	curr_spd15_avg	curr_dir15_avg	curr_spd16_avg	curr_dir16_avg	curr_spd17_avg	curr_dir17_avg	curr_spd18_avg	curr_dir18_avg	curr_spd19_avg	curr_dir19_avg	curr_spd20_avg	curr_dir20_avg	wind_chill


import requests
from datetime import *
import json
import csv
from enum import Enum

### SMART ATLANTIC DATA

met_station_name = "smb_saint_john_cruise_terminal"
met_lat = 45.26683333
met_long = -66.06116667

buoy_lat = 45.19716666666667
buoy_long = -66.11376666666666
buoy_station_name = "smb_saint_john"

base_met_station_req = "https://www.smartatlantic.ca/erddap/tabledap/SMA_saint_john_cruise_terminal.json?time%2Cwind_dir_avg%2Cwind_spd_avg%2Cwind_spd_max"
base_buoy_station_req = "https://www.smartatlantic.ca/erddap/tabledap/SMA_saint_john.json?time%2Cwind_spd_avg%2Cwind_spd_max%2Cwind_dir_avg%2Cair_temp_avg%2Cair_pressure_avg%2Csurface_temp_avg%2Cwave_ht_max%2Cwave_ht_sig%2Cwave_dir_avg%2Cwave_spread_avg%2Cwave_period_max%2Ccurr_spd_avg%2Ccurr_dir_avg%2Ccurr_spd2_avg%2Ccurr_dir2_avg%2Ccurr_spd3_avg%2Ccurr_dir3_avg%2Ccurr_spd4_avg%2Ccurr_dir4_avg%2Ccurr_spd5_avg%2Ccurr_dir5_avg%2Ccurr_spd6_avg%2Ccurr_dir6_avg%2Ccurr_spd7_avg%2Ccurr_dir7_avg%2Ccurr_spd8_avg%2Ccurr_dir8_avg%2Ccurr_spd9_avg%2Ccurr_dir9_avg%2Ccurr_spd10_avg%2Ccurr_dir10_avg%2Ccurr_spd11_avg%2Ccurr_dir11_avg%2Ccurr_spd12_avg%2Ccurr_dir12_avg%2Ccurr_spd13_avg%2Ccurr_dir13_avg%2Ccurr_spd14_avg%2Ccurr_dir14_avg%2Ccurr_spd15_avg%2Ccurr_dir15_avg%2Ccurr_spd16_avg%2Ccurr_dir16_avg%2Ccurr_spd17_avg%2Ccurr_dir17_avg%2Ccurr_spd18_avg%2Ccurr_dir18_avg%2Ccurr_spd19_avg%2Ccurr_dir19_avg%2Ccurr_spd20_avg%2Ccurr_dir20_avg%2Cwind_chill"

time_min = "&time%3E="
time_max = "&time%3C="

def writeout_json(jsondata, filename:str) -> None:
	file = open(filename+".json", "w")
	file.write(json.dumps(jsondata,sort_keys=True, indent=4))
	file.close()

def getSmartAtlData(base_req:str=base_met_station_req, minutes:int=10, attempts:int=3, incr:int=30):
	#Keep trying to get the data
	# if we don't get anything, try increasing the range by 'incr' minutes
	for i in range(attempts):
		req = base_req + time_min + datetime_out(mins_ago(minutes+(incr*i))) + time_max + datetime_out(now())
		print(req)
		x = requests.get(req)
		if x.ok:
			print("Success (attempt "+str(i+1)+")")
			return json.loads(x.text)
		print("Error (attempt "+str(i+1)+"): status code was "+str(x.status_code))
	return


### TIDE GAUGE

#Station 00065 (Saint John Tide gauge) has an id of 5cebf1df3d0f4a073c4bbc24
#latitude:45.254629, longitude:-66.059804
#Time series name - code (ie parameter to specify what data value we want from the api)
#Water level predictions 		- wlp
#Water level forecasts 			- wlf
#Water level official value 	- wlo
#water lavel sensor 1,2,3 		- wl1, wl2, wl3
#High and low tide predictions 	- wlp-hilo

#https://api.iwls-sine.azure.cloud-nuage.dfo-mpo.gc.ca/api/v1/stations/5cebf1df3d0f4a073c4bbc24/data?time-series-code=
# wlo
# &from=2025-05-17T00%3A00%3A00Z
# &to=2025-05-17T01%3A00%3A00Z
# &resolution=FIFTEEN_MINUTES

#resolution can be one of: ALL, ONE_MINUTE, THREE_MINUTES, FIVE_MINUTES, FIFTEEN_MINUTES, SIXTY_MINUTES

# We want the official value for real time monitoring, then forecasts
# forecasts are shorter term and more accurate than predictions,
#  "include recently observed differences btw predictions and real-time observations"
# - https://tides.gc.ca/tides/en/definitions-content-tides-and-currents

tide_gauge_lat = 45.254629
tide_gauge_long = -66.059804

tide_base_req = "https://api.iwls-sine.azure.cloud-nuage.dfo-mpo.gc.ca/api/v1/stations/5cebf1df3d0f4a073c4bbc24/data?time-series-code="

time_from = "&from="
time_to = "&to="
res = "&resolution="

class TimeSeries(Enum):
	prediction = 1
	forecast = 2
	official = 3
	sensor1 = 4
	sensor2 = 5
	sensor3 = 7
	high_low_pred = 7

TimeSeriesText = {
	TimeSeries.prediction : "wlp",
	TimeSeries.forecast : "wlf",
	TimeSeries.official : "wlo",
	TimeSeries.sensor1 : "wl1",
	TimeSeries.sensor2 : "wl2",
	TimeSeries.sensor3 : "wl3",
	TimeSeries.high_low_pred : "wlp-hilo"
}

tide_time_res = {
	1:"ONE_MINUTE",
	3:"THREE_MINUTES",
	5:"FIVE_MINUTES",
	15:"FIFTEEN_MINUTES",
	60:"SIXTY_MINUTES"
}

def getTideData(series:TimeSeries=TimeSeries.forecast, hours:float=1, time_res:int=15, attempts:int=3, incr:int=1):
	#Keep trying to get the data
	# if we don't get anything, try increasing the range by 'incr' minutes
	for i in range(attempts):
		req = tide_base_req + TimeSeriesText[series] + time_from + datetime_out(hours_ago(hours+incr*i)) +\
			time_to + datetime_out(now()) + res + tide_time_res[time_res]
		print(req)
		x = requests.get(req)
		if x.ok:
			print("Success (attempt "+str(i+1)+")")
			return json.loads(x.text)
		print("Error (attempt "+str(i+1)+"): status code was "+str(x.status_code))
	return

### RIVER GAUGE

#"Recent real time data" (csv) ie. latest
#https://wateroffice.ec.gc.ca/services/recent_real_time_data/csv/inline?stations[]=01AP005&parameters[]=46
#Ex. for more values (real time data csv)
#https://wateroffice.ec.gc.ca/services/real_time_data/csv/inline?stations[]=01AP005&parameters[]=46&parameters[]=47&start_date=2025-05-15%2000:00:00&end_date=2025-05-17%2023:59:59

#Only water level works (param 46) (flow rate, param 47 is listed, but wasn't returned, so ignore it)

#looks like, the only values which change are 1-DateTime and 3-Value
#ID,Date,Parameter,Value,Qualifier,Symbol,Approval,Grade,Qualifiers
#01AP005,2025-05-15T00:00:00Z,46,2.113,,,Provisional/Provisoire,,


river_req = "https://wateroffice.ec.gc.ca/services/recent_real_time_data/csv/inline?stations[]=01AP005&parameters[]=46"

def getRiverData(attempts:int=3) -> list:
	for i in range(attempts):
		x = requests.get(river_req)
		if x.ok:
			dat = list(csv.reader(x.text.splitlines()))
			time = dat[1][1]
			river_level = dat[1][3]
			return {"level":river_level, "time":time}
		print("Error (attempt "+str(i+1)+"): status code was "+str(x.status_code))
	return

### Formatting

def datetime_out(dt:datetime) -> str:
	return datetime.isoformat(dt.replace(tzinfo=None),timespec='seconds') + "Z"

def now() -> datetime:
	return datetime.now(UTC)

def last_hour() -> datetime:
	return now() + timedelta(hours=-1)

def mins_ago(mins:float) -> datetime:
	return now() + timedelta(minutes=-mins)

def hours_ago(hours:float) -> datetime:
	return now() + timedelta(hours=-hours)

if __name__ == "__main__":
	anenometer_data = getSmartAtlData()
	if anenometer_data != None:
		writeout_json(anenometer_data,"met_test")

	buoy_dat = getSmartAtlData(base_buoy_station_req,60) # Buoy data only updated every hour or so
	if buoy_dat != None:
		writeout_json(buoy_dat,"buoy_test")
	
	river_dat = getRiverData()
	if river_dat != None:
		writeout_json(river_dat,"river_test")

	tide_dat = getTideData()
	if tide_dat != None:
		writeout_json(tide_dat, "tide_test")