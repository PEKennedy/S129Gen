import math

# Utils

def chooseClosest(num:float, options:list):
	closestInd = 0
	closestDist = 0
	for i,option in enumerate(options):
		if option-num < closestDist:
			closestDist = option-num
			closestInd = i
	return options[closestInd]

def totable(num,base=50, lower=150, upper=350)->int:
	rounded = base*round(float(num)/base)
	#print("from "+str(num)+" to "+str(min(max(rounded,lower),upper)))
	return min(max(rounded,lower),upper)

def angular_dist(a:float,b:float):
	return 180-abs(abs(a-b)-180)

# math.dist is equivalent
def dist(*args)->float:
	sum = 0
	for i,arg in enumerate(args):
		sum += arg**2
	return math.sqrt(sum)

def relative_vel(s1,h1,s2,h2)->list: #speed, heading 1 and 2
	x1 = s1*math.cos(h1)
	x2 = s2*math.cos(h2)
	y1 = s1*math.sin(h1)
	y2 = s2*math.sin(h2)
	v = dist(x2-x1,y2-y1)
	angle = math.atan((y2-y1)/(x2-x1))
	return [v,angle]

# Data classes
# ocean parameters loosely based on the saint john harbour
class Ocean:
	def __init__(self,Hs=1.6,wave_heading=205,density=1.020,cur_spd_kn=1,cur_heading=90,pErr=0.1):
		self.Hs = Hs							#signficant wave height, was 0.5 to be similar to observed, but that lead to a coefficient being 0
		self.wave_heading = wave_heading		#waves heading SSW
		self.cur_spd_kn = cur_spd_kn
		self.cur_spd_ms = 0.514*cur_spd_kn
		self.cur_heading = cur_heading			#current heads east
		self.density = density					#water density

		self.eHs = pErr*Hs
		self.ewave_heading = pErr*wave_heading
		self.ecur_spd_kn = pErr*cur_spd_kn
		self.ecur_spd_ms = pErr*self.cur_spd_ms
		self.ecur_heading = pErr*cur_heading
		self.edensity = pErr*density

class Wind:
	def __init__(self,wind_spd_kn=7,wind_heading=180,density=1.25,pErr=0.1):
		self.spd_kn = wind_spd_kn
		self.spd_ms = wind_spd_kn*0.514
		self.heading = wind_heading
		self.density = density			#kg/m^3, could be calculated in the future

		self.espd_kn = pErr*wind_spd_kn
		self.espd_ms = pErr*self.spd_ms
		self.eheading = pErr*self.heading
		self.edensity = pErr*self.density

#p48
# Ship parameters loosely based on the Santa Rosa, the largest ship to ever dock at Saint John
class Vessel:
	def __init__(self,d=9.8,L=300,B=43,Fk=0.9,CS=2.4,Lpp=285,dis=113778, vol_m3=254862,
				KGW=30,Aside=10000,CW=0.5,Kr=0.6,dr=3.14/2,trim=math.radians(2),course=270,
				speed_kn=8,pErr=0.1):
		self.d = d						#draught
		self.B = B						#Beam (width)
		self.L = L						#Length (overall)
		self.Fk = Fk					#keel factor
		self.CS = CS					# "an empirical coefficient"
		self.Lpp = Lpp					#length between perpendiculars
		self.dis = dis					#displacement
		self.CB = dis/(Lpp*B*d)			#block coefficient
		self.AS = B*d					#cross sectional area
		self.GM = d/8#B/25				#approximate metacentric height, table is another approach, should be 0 to 0.6 ish
		self.KGW = KGW					#keel to center of windage area, approx d+(avl/2lpp)
		self.Aside=Aside				#side area the wind acts upon
		self.CW=CW						#wind coefficient
		self.lw=KGW - (d/2)				#wind moment arm
		self.Kr=Kr						#index of turning ability in shallow waters
		self.dr=dr						#rudder position
		self.Rc=Lpp/(Kr*dr)				#turning circle
		self.BM = B*B/(20.4*self.CB*d)
		self.KB = d*(0.84-((0.33*self.CB)/(0.18+0.88*self.CB)))
		self.KG = self.KB-self.GM+self.BM	#keel to center of gravity
		self.vol_m3 = vol_m3 #d*B*self.Lpp

		self.trim=trim					#angle of trim (front - back)
		self.course=course				#heading west
		self.spd_kn = speed_kn
		self.spd_ms = 0.514*speed_kn

		self.ed = d*pErr				#CCG recommends 1% uncertainty for draught, but here its 10%
		self.eL = L*pErr
		self.eB = B*pErr
		self.eFk = Fk*pErr
		self.eCS = CS*pErr
		self.eLpp = Lpp*pErr
		self.edis = dis*pErr
		self.eCB = dist(
			self.edis/(Lpp*B*d),
			self.eLpp*dis/(Lpp*Lpp*B*d),
			self.eB*dis/(Lpp*B*B*d),
			self.ed*dis/(Lpp*B*d*d)
		)
		self.eAS = dist(self.ed*B,self.eB*d)
		self.eGM = self.eB/25
		self.eKGW = KGW*pErr
		self.eAside=Aside*pErr
		self.eCW=CW*pErr
		self.elw = dist(self.eKGW,self.ed/2)
		self.eKr = pErr*Kr
		self.edr = pErr*dr
		self.eRc = dist(
			self.eLpp/(Kr*dr),
			self.eKr*Lpp/(Kr*Kr*dr),
			self.edr*Lpp/(Kr*dr*dr)
		)
		self.eBM = dist(
			self.eB*2*B/(20.4*self.CB*d),
			self.eCB*B*B/(20.4*self.CB*self.CB*d),
			self.ed*B*B/(20.4*self.CB*d*d)
		)
		self.eKB = dist(
			self.ed*(0.84-(0.33*self.CB/(0.18*0.88*self.CB))),
			d*self.eCB/(2*(44*self.CB+9)**2)
		)
		self.eKG = dist(self.eKB,self.eGM,self.eBM)
		self.evol = vol_m3*pErr

		self.etrim = pErr*self.trim
		self.ecourse = pErr*course
		self.espd_kn = pErr*self.spd_kn
		self.espd_ms = pErr*self.spd_ms

# Channel properties, made to be larger than the Santa Rosa
class Channel:
	def __init__(self,h=10,w=50,n=3, pErr=0.1):
		self.h=h
		self.n=n #run over rise
		self.w=w
		self.eh=h*pErr
		self.en=n*pErr
		self.ew=w*pErr
		self.AC=w*h+n*h*h
		self.eAC=dist(self.ew*h,self.eh*(w+2*n*h),self.en*h*h)

"""wind = Wind(wind_spd_kn=25,wind_heading=90,density=1.25,pErr=0.1)
ocean = Ocean(Hs=2.5,wave_heading=90,density=1.020,cur_spd_kn=0,cur_heading=90,pErr=0.1)
vessel = Vessel(d=16.5,L=300,B=59,Fk=0.9,CS=2.4,Lpp=385,dis=254862,
				KGW=34.6,Aside=13929,CW=1.12,Kr=0.42,dr=0.349,trim=math.radians(0),course=0,
				speed_kn=12,pErr=0.1)
channel = Channel()"""

wind = Wind()
ocean = Ocean()
vessel = Vessel()
channel = Channel()

#TODO: Remove this
heel_combined=math.radians(5) 	#angle of heel (side to side)	
#error_heel_combined = heel_combined * percent_error

#angle that the waves hit the vessel at
#def angle_of_incidence(ocean:Ocean,vessel:Vessel,pErr=0.1)->float:
angle_of_incidence = min(angular_dist(vessel.course+90,ocean.wave_heading),angular_dist(vessel.course-90,ocean.wave_heading))
print("angle of incidence "+str(angle_of_incidence))
e_angle = 0.1*angle_of_incidence



##### WAVE RESPONSE
def WaveResponse_trig(ocean:Ocean=ocean) -> float:
	return 1.6*ocean.Hs

def WaveResponseError_trig(ocean:Ocean=ocean) -> float:
	return 1.6*ocean.eHs

#lookup by Lpp, then Hs
#PIANC has more values than CCG...
C2 = {
	75 :{0.5:0.2, 1:0.17, 1.5:0.23, 2:0.29, 2.5:0.31, 3:0.34, 3.5:0.37, 4:0.40},
	100:{0.5:0.1, 1:0.14, 1.5:0.19, 2:0.23, 2.5:0.26, 3:0.29, 3.5:0.32, 4:0.34},
	150:{0.5:0  , 1:0.09, 1.5:0.2 , 2:0.34, 2.5:0.51, 3:0.69, 3.5:0.87, 4:1.08},
	200:{0.5:0  , 1:0.05, 1.5:0.15, 2:0.26, 2.5:0.40, 3:0.57, 3.5:0.72, 4:0.92},
	250:{0.5:0  , 1:0.03, 1.5:0.1 , 2:0.21, 2.5:0.33, 3:0.48, 3.5:0.63, 4:0.80},
	300:{0.5:0  , 1:0, 	  1.5:0.07, 2:0.16, 2.5:0.25, 3:0.39, 3.5:0.56, 4:0.68},
	350:{0.5:0  , 1:0,	  1.5:0.04, 2:0.11, 2.5:0.18, 3:0.31, 3.5:0.51, 4:0.58},
}
#lookup by incidence angle
C6 = {
	15:1, 35:1.4, 90:1.7
}

def WaveResponse_ROM(v:Vessel=vessel, o:Ocean=ocean, angle:float=angle_of_incidence) -> float:
	print("C2 chosen: "+str(C2[totable(v.Lpp)][totable(o.Hs,0.5,1,4)])+" C6 chosen: "+str(C6[chooseClosest(angle,[15,35,90])]))
	return 3.9*o.Hs*C2[totable(v.Lpp)][totable(o.Hs,0.5,1,4)]*C6[chooseClosest(angle,[15,35,90])]

def WaveResponse_error_ROM(v:Vessel=vessel, o:Ocean=ocean, angle:float=angle_of_incidence, pErr=0.1)->float:
	xC2 = C2[totable(v.Lpp)][totable(o.Hs,0.5,1,4)]
	xC6 = C6[chooseClosest(angle,[15,35,90])]
	#print(xC6)
	eC2 = pErr*xC2
	eC6 = pErr*xC6
	return dist(
		3.9*eC2*xC6*o.Hs,
		3.9*eC6*xC2*o.Hs,
		3.9*o.eHs*xC2*xC6
	)

#### SQUAT

## CCG SQUAT
def froude(V:float,channel:Channel=channel,g=9.81)->float:
	return V/math.sqrt(g*channel.h)

def err_froude(V:float,eV,channel:Channel=channel,g=9.81)->float:
	return dist(
		eV/math.sqrt(g*channel.h),
		channel.eh*V/(2*math.sqrt(g)*(channel.h**1.5))
	)

def CCG_squat(Fr:float,v:Vessel=vessel)->float:
	Fr2 = Fr*Fr
	return v.CS*v.dis*Fr2 / (v.Lpp*v.Lpp*math.sqrt(1-Fr2))

def CCG_squat_err(Fr:float,eFr:float,v:Vessel=vessel)->float:
	Fr2 = Fr*Fr
	Lpp2 = v.Lpp*v.Lpp
	FrR = math.sqrt(1-(Fr*Fr))
	return dist(
		v.eCS*v.dis*Fr2/(Lpp2*FrR),
		v.edis*v.CS*Fr2/(Lpp2*FrR),
		2*v.eLpp*v.CS*Fr2/((v.Lpp**3) * Fr2),
		eFr*v.CS*v.dis*Fr*(Fr2-2)/(Lpp2*(1-Fr2)**1.5)
	)

## BARASS SQUAT
def blockage_S(v:Vessel=vessel,c:Channel=channel)->float:
	return v.AS/c.AC

def err_S(v:Vessel=vessel,c:Channel=channel)->float:
	return (v.AS/c.AC)*dist(v.eAS/v.AS, c.eAC/c.AC)

def Barass_squat(S,Vk,v:Vessel=vessel)->float:
	return v.CB*(S**0.81)*(Vk**2.08)/20

def Barass_squat_err(S,Vk,eS,eVk,v:Vessel=vessel)->float:
	return dist(
		v.eCB*(S**0.81)*(Vk**2.08)/20,
		eS*0.81*v.CB*(S**-0.19)*(Vk**2.08)/20,
		eVk*2.08*v.CB*(S**0.81)*(Vk**1.08)/20
	)

#### TRIM AND HEEL

def incline(side:float,angle:float)->float: #heel, trim
	return side/2 * math.sin(angle)

def error_incline(side:float,angle:float,eSide:float,eAngle:float)->float:
	return dist(
		eSide/2 *math.sin(angle),
		eAngle*side/2 * math.cos(angle)
	)


#euclidean distance is used in propagation of errors
def error_heel_sinkage(angle, error_angle, v:Vessel=vessel) -> float:
	return dist(
		(v.B*0.5 * math.sin(angle)*v.eFk),
		(v.Fk*0.5 * math.sin(angle)*v.eB),
		(v.Fk*v.B*0.5*math.cos(angle)*error_angle)
	)

def heel_sinkage(heel:float, v:Vessel=vessel)->float:
	return v.Fk*v.B*0.5*math.sin(heel)

#### Heel angle due to wind (radians)
def phiw(Mw:float,v:Vessel=vessel,o:Ocean=ocean)->float:
	return Mw/(9.81*v.vol_m3*o.density*v.GM)

def Mw(fw:float,v:Vessel=vessel)->float:
	return fw*v.lw/1000 #divide by 1000 to convert N to kN

def Fw(Vvw:float,w:Wind=wind,v:Vessel=vessel)->float:
	return 0.5*w.density*v.CW*v.Aside*Vvw*Vvw

def eFw(Vvw:float,eVvw:float,w:Wind=wind,v:Vessel=vessel)->float:
	return dist(
		w.edensity*0.5*v.CW*v.Aside*Vvw*Vvw,
		w.density*0.5*v.eCW*v.Aside*Vvw*Vvw,
		w.density*0.5*v.CW*v.eAside*Vvw*Vvw,
		w.density*v.CW*v.Aside*Vvw*eVvw,
	)

def eMw(fw:float,efw:float,v:Vessel=vessel)->float:
	return dist(efw*v.lw/1000,v.elw*fw/1000)

def ePhiw(Mw:float,eMw:float,v:Vessel=vessel,o:Ocean=ocean)->float:
	return dist(
		eMw/(9.81*v.dis*o.density*v.GM),
		v.edis*Mw/(9.81*v.dis*v.dis*o.density*v.GM),
		o.edensity*Mw/(9.81*v.dis*o.density*o.density*v.GM),
		v.eGM*Mw/(9.81*v.dis*o.density*v.GM*v.GM)
	)

### Heel angle due to turning (radians)
def phiC(relV,v:Vessel=vessel)->float:
	return relV*relV*(v.KG-(0.5*v.d))/(9.81*v.Rc*v.GM)

def ePhiC(relV, erelV ,v:Vessel=vessel)->float:
	t2 = v.KG-(v.d/2)
	relV2 = relV**2
	g=9.81
	bot_term = g*v.Rc*v.GM
	return dist(
		erelV*2*relV*t2/(bot_term),
		v.eRc*relV2*t2/(bot_term*v.Rc),
		v.eGM*relV2*t2/(bot_term*v.GM),
		v.eKG*relV2/(bot_term),
		v.ed*relV2/(2*bot_term),
	)

# print a property and its uncertainty with nice-ish formatting
def pr_prop(prop_name:str, property:float, uncertainty:float)->None:
	print("{:<20}| {:>15.4f} \tuncertainty: {:>12.4f}".format(prop_name,property,uncertainty))

if __name__ == "__main__":
	
	## WAVE RESPONSE
	print("#####################################################")
	pr_prop("trig wave response_m",WaveResponse_trig(),WaveResponseError_trig())
	pr_prop("ROM wave response_m",WaveResponse_ROM(),WaveResponse_error_ROM())
 
	## TRIM
	pr_prop("trim",incline(vessel.L,vessel.trim),error_incline(vessel.L,vessel.trim,vessel.eL,vessel.etrim))

	## SQUAT (CCG)
	print("#####################################################")
	rel_water_spd_kn = relative_vel(vessel.spd_kn,vessel.course,ocean.cur_spd_kn,ocean.cur_heading)[0]
	rel_water_spd_ms = 0.514*rel_water_spd_kn
	print("spd kn "+str(rel_water_spd_kn)+" spd ms "+str(rel_water_spd_ms))
	#print(rel_water_spd_ms)
	fr=froude(rel_water_spd_ms)
	fr_er = err_froude(rel_water_spd_ms,rel_water_spd_ms*0.1)
	pr_prop("froude number",fr,fr_er)
	pr_prop("CCG squat_m",CCG_squat(fr),CCG_squat_err(fr,fr_er))

	## SQUAT (BARASS)
	print("#####################################################")
	S = blockage_S()
	eS = err_S()
	pr_prop("CB",vessel.CB,vessel.eCB)
	pr_prop("AS_m2",vessel.AS,vessel.eAS)
	pr_prop("AC_m2",channel.AC,channel.eAC)
	pr_prop("S",S,eS)
	pr_prop("BARASS squat_m",Barass_squat(S,rel_water_spd_kn),Barass_squat_err(S,rel_water_spd_kn,eS,rel_water_spd_kn*0.1))

	## HEEL
	### Wind
	print("#####################################################")
	rel_wind_spd_kn = relative_vel(vessel.spd_kn,vessel.course,wind.spd_kn,wind.heading)[0]
	rel_wind_spd_ms = 0.514*rel_wind_spd_kn

	fw = Fw(rel_wind_spd_ms)
	mw = Mw(fw)
	heel_wind = phiw(mw)
	efw = eFw(rel_wind_spd_ms,rel_wind_spd_ms*0.1)
	emw = eMw(fw,efw)
	e_heel_wind = ePhiw(mw,emw)

	pr_prop("water density_kg/m3",ocean.density,ocean.edensity)
	pr_prop("volume_m3",vessel.vol_m3,vessel.evol)
	pr_prop("GM_m",vessel.GM,vessel.eGM)
	pr_prop("lw_m",vessel.lw,vessel.elw)
	pr_prop("fw_N",fw,efw)
	pr_prop("mw_kN",mw,emw)
	pr_prop("heel wind deg",heel_wind*57.3,e_heel_wind*57.3)

	### Turning
	print("#####################################################")
	heel_turning = phiC(rel_water_spd_ms)
	e_heel_turning = ePhiC(rel_water_spd_ms,rel_water_spd_ms*0.1)

	pr_prop("BM_m",vessel.BM,vessel.eBM)
	pr_prop("KB_m",vessel.KB,vessel.eKB)
	pr_prop("KG_m",vessel.KG,vessel.eKG)
	pr_prop("Kr",vessel.Kr,vessel.eKr)
	pr_prop("d_m",vessel.d,vessel.ed)
	pr_prop("Lpp_m",vessel.Lpp,vessel.eLpp)
	pr_prop("turning radius Rc_m",vessel.Rc,vessel.eRc)
	pr_prop("GM_m",vessel.GM,vessel.eGM)
	pr_prop("rel vel ms",rel_water_spd_ms,rel_water_spd_ms*0.1)
	pr_prop("heel turning deg",heel_turning*57.3,e_heel_turning*57.3)

	heel_angle_combined = heel_turning+heel_wind
	e_heel_combined = dist(e_heel_turning,e_heel_wind)

	_heel_sinkage = heel_sinkage(heel_angle_combined)
	e_heel_sinkage = error_heel_sinkage(heel_angle_combined,e_heel_combined)

	print("#####################################################")
	pr_prop("heel combined deg",heel_angle_combined*57.3,e_heel_combined*57.3)
	pr_prop("heel sinkage",_heel_sinkage,e_heel_sinkage)



