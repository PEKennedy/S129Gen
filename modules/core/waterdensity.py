import math

def dist(*args)->float:
	sum = 0
	for i,arg in enumerate(args):
		sum += arg**2
	return math.sqrt(sum)

def pure_water_density(t:float) -> float:
	return 999.842594 +  0.06793952*t - 0.009095290*t*t + \
		0.0001001685*t*t*t - 0.000001120083*t*t*t*t + 0.000000006536332*t*t*t*t*t

#t is temperature in Celsius, S is practical salinity
def density_1atm(t:float, S:float) -> float:
	return pure_water_density(t) + \
		S*(0.824493 - 0.0040899*t + 0.000076438*t*t - 0.00000082467*t*t*t + 0.0000000053875*t*t*t*t) + \
		S*math.sqrt(S)*(-0.00572466 + 0.00010227*t - 0.0000016546*t*t) + 0.00048314*S*S
	 
def increased_sinkage(density1:float, density2:float, height1:float) -> float:
	return ((density1/density2)-1)*height1

def error_inc_sinkage(h1:float,r1:float,r2:float,eh1:float,er1:float,er2:float)->float:
	return dist(
		eh1*(r1/r2 -1),
		er1*h1/r2,
		er2*h1*r1/(r2*r2)
	)

def error_pure_water_density(t:float,et:float)->float:
	return abs(et*(6.793952e-2 - t*1.819058e-2 + t*t*3.005055e-4 - (t**3)*4.480332e-6 + (t**4)*3.268166e-8))

def error_density_1atm(t:float,et:float,S:float,eS:float)->float:
	return dist(
		error_pure_water_density(t,et),
		eS*((0.824493 - 0.0040899*t + t*t*7.6438e-5 - t**3 * 8.2467e-7 + t**4 * 5.3875e-9)+ \
	  		1.5*math.sqrt(S)*(-0.00572466 + t*1.0227e-4 - t*t*1.6546e-6) + S*9.6628e-4),
		et*(S*(t**3 * 2.155e-8 - t*t*2.47401e-6 + t*1.52876e-4 + 0.00408990) + S**1.5 * (1.0226e-4 - t*3.3092e-6))
	)

## Fisheries Board 1934-1945 data
temps_surf = [
	7.1,
	3.5,
	1.5,
	0.3,
	0.3,
	1.0,
	7.2,
	12.9,
	14.1,
	14.9,
	13.8,
	10.8
]

salinity_surf = [
	16.8,
	13.7,
	18.7,
	22.7,
	22.3,
	12.2,
	5.7,
	11.5,
	16.9,
	21.7,
	23.3,
	23.3
]

temps_bot = [
	8.3,
	5.5,
	2.9,
	0.3,
	0.5,
	1.2,
	5.6,
	9.9,
	11.8,
	13.3,
	12.0,
	10.9,
]

salinity_bot = [
	24.4,
	22.2,
	23.4,
	28.2,
	28.2,
	18.3,
	14.2,
	19.7,
	22.3,
	22.0,
	27.6,
	27.4,
]

## Test data
temp = 12
sal = 20
draught = 9.8

err_percent = 0.1
eTemp = err_percent*temp
eSal = err_percent*sal
eDraught = err_percent*draught

if __name__ == "__main__":
	# Calculate the densities for the fisheries board data
	densities_bottom = []
	err_densities_bot = []
	for i in range(len(salinity_bot)):
		densities_bottom.append(density_1atm(temps_bot[i],salinity_bot[i]))
		err_densities_bot.append(error_density_1atm(temps_bot[i],temps_bot[i]*err_percent,salinity_bot[i],salinity_bot[i]*err_percent))
	print(densities_bottom)
	print(err_densities_bot)

	densities_surf = []
	err_densities_surf = []
	for i in range(len(salinity_surf)):
		densities_surf.append(density_1atm(temps_surf[i],salinity_surf[i]))
		err_densities_surf.append(error_density_1atm(temps_surf[i],temps_surf[i]*err_percent,salinity_surf[i],salinity_surf[i]*err_percent))
	print(densities_surf)
	print(err_densities_surf)

	# calculate hypothetical sinkage for the SANTA ROSA, and propagated uncertainty
	test_sea_density = density_1atm(12,20)
	test_sea_density_err = error_density_1atm(12,eTemp,20,eSal)
	print(str(test_sea_density) + " uncertainty: " + str(test_sea_density_err))

	print(str(increased_sinkage(test_sea_density,densities_surf[0],draught)) +
	   " uncertainty:" +
		str(error_inc_sinkage(draught,test_sea_density,densities_surf[0],
						eDraught, test_sea_density_err, err_densities_surf[0]))
	)

	print(increased_sinkage(1030,1000,9.8))