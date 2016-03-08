# -*- coding: utf-8 -*-
"""
Created on Wed Feb 17 10:25:43 2016

@author: Thiru
"""
#internal libraries
import itertools,csv,sys,os,pickle
#External libraries
import gmaps,tweepy,wgetter,numpy as np,pandas as pd
from sklearn.externals import joblib
from TrainClassifier import labelHash, separate_column_by_type, process_nontext
from scipy import stats
from geopy.geocoders import Nominatim
import operator
from HTMLText import *

country = None
heatmapVariable=None
"""
Input: Features of attack, from file input.csv
Output: [String] Terrorist Group name
"""
def predictTerroristGroup():
	def format_inputs():
		df = pd.read_csv('input.csv')
		global country
		country = df['country_txt'][0]
		nontext_df,text_df,labels = separate_column_by_type(df)
		nontext_df = process_nontext(nontext_df)
		return nontext_df

	def predict_group(features):
		classifier = joblib.load('extratrees/Extra Trees.pkl')
		pred = classifier.predict(features)[0]
		res = "Unknown"
		for entry in labelHash:
			if labelHash[entry] == pred:
				res = entry
		return res
		
	prediction = predict_group(format_inputs())
	print('Likely terrorist group: '+prediction)
	return prediction

"""
Input: [String] Terrorist Group name
Output: [String] Risky Locations

Description: This function prints the details of the terrorist group, and of its next attack (if any)
"""
def printTerroristDetails(name):
	print("\n")
	print('***** Summary Details for '+name+' *****')
	print("\n")
	multipleAttacks(name)
	location=typeFreqPlaceAttacked(name)
	numOfCasualties(name)
	findTypeOfWeapon(name)
	findPropertyDamage(name)
	numPerps(name)
	return location #return risky location!

def multipleAttacks(name):
	locProb = "csv-files/prob_mult.csv"
	df2 = pd.read_csv(locProb,encoding='Latin-1')
	value = round(float(df2[df2['gname']==name]['prob_mult']),3)
	if value > 0.5:
		print('MULTIPLE ATTACKS LIKELY with probability: '+str(value))
	else:
		print('Multiple attacks are unlikely with probability: '+str(1-value))
	return value

def typeFreqPlaceAttacked(name):
	dic= pickle.load(open('dics/typeOfPlace','rb'))
	if name in dic.keys():
		likelyPlaceAttacked= max(dic[name].items(), key=operator.itemgetter(1))[0]
		confidence = dic[name][likelyPlaceAttacked] / sum(dic[name].values())
		confidence = round(confidence,3)
		print("\n")
		print('Most Frequent Place attacked: '+likelyPlaceAttacked+' consisting of '+str(confidence*100)+'% of all attacks')
	return likelyPlaceAttacked
	
def numOfCasualties(name):
	print('\n')
	dic = pickle.load(open('dics/numOfCasualties','rb'))
	if name in dic.keys():
		print("Estimated number of casualties: " + str(round(dic[name],3)))
	else:
		print('Number of Casualties Unknown')
	return round(dic[name],2)

def conditionalPlaceAttacked(name):
	##TO BE DONE WHEN I CAN BE BOTHERED TO
	return
	
def findTypeOfWeapon(name):
	dic= pickle.load(open('dics/typeOfWeapon','rb'))
	if name in dic.keys():
		likelyAttackWeapon= max(dic[name].items(), key=operator.itemgetter(1))[0]
		confidence = dic[name][likelyAttackWeapon] / sum(dic[name].values())
		confidence = round(confidence,3)
		print("\n")
		print('Likely type of weapon used in successive attacks is '+likelyAttackWeapon+ 'with probability: '+str(confidence))
	else:
		print("\n")
		print('Likely type of weapon unknown')
	return likelyAttackWeapon
	  

def numPerps(name):
	dic = pickle.load(open('dics/numPerps','rb'))
	if name in dic.keys():
		print("\n")
		mean= np.mean(dic[name])
		median=np.median(dic[name])
		mode= stats.mode(dic[name])
		print ('Mean Num Perpetrators = '+str(mean)+'\n Median Num Perpetrators = '+str(median) +'\n Mode Num Perpetrators = '+str(int(mode.mode[0])))
		return [mean,median,mode]
	print("\n")
	print('Likely size of attackers unknown.')
	return False
	
def findPropertyDamage(name):
	dic = pickle.load(open('dics/propertyDamage','rb'))
	try:
		currGroup=dic[name]
	except:
		print(name + 'will likely NOT have property damage with probability 1')
		return
	probability=currGroup[0] / sum(currGroup)
	print("\n")
	if (probability) > 0.5:
		print(name +' will likely have property damage of estimated < $1 Millon with probability '+str(round(probability,3)))
	else:
		print(name + 'will likely NOT have property damage with probability '+str(round(probability,3)))
	return round(probability,3)
	
 ##Modified for dashboard --> return data instead of plotting it in gmaps.
def plotRiskyLocations(name):
	global country
	if name == None:
		return
	#Consider saving this to pickle file.
	dic={'Business':['Business','Gas','mall','restaurant','cafe','hotel'],
		 'Government (General)':['Government buildings','Ministry'],
		  'Police':['Police post','prison','Police'],
		  'Military':['military base','air base','navy'],
		  'abortion related':'abortion clinic',
		  'airports & aircraft':'airport',
		  'Government (Diplomatic)': 'embassy',
		   'Educational Institution':['school','university'],
		   'Food or Water Supply':['water treatment plant','farms'],
			'NGO':['NGO','Non governmental organisations'],
			'Maritime':['port','ferry'],
			'Journalists & Media':'newspaper company',
			'Other':['fire station','hospital'],#wtf do you code for this
			'Private Citizens & Property':['shopping malls','markets'],
		   'Religious Figures/Institutions':['temples','churches','mosques'],
			'Terrorists/Non-State Militia':'militia',
			'Transportation':['Train station','Bus stations'],
			'Utilities':['power plant','water plant'],
			'Tourists':['tourist spots'],
			'Telecommunications':['Radio station','TV station','Internet provider'],
			'Violent Political Party': 'political party' #and this
	}
	name = dic[name]    
	geolocator = Nominatim()
	location=[]
	if type(name) != list:
		loc=geolocator.geocode(name + ' '+country,exactly_one=False,timeout=10)
		if loc is not None:
			location.append(loc)
	else:
		for entry in name:
			loc = geolocator.geocode(entry + ' '+country,exactly_one=False,timeout=10)
			if loc is not None:
				location.append(loc)
	location= list(itertools.chain(*location)) #flatten list
	data=[]
	for entry in location:
		data.append([entry.latitude,entry.longitude])
	convertGpsToHTML(data,0)
 
#Writes GPS coordinates into a HTML file.
"""
 Input: List of lists of GPS coordinates.
 Output: HTML file of the heatmap.
"""
def convertGpsToHTML(data,state):
    #taken from HTMLText
    global initial1,initial2,twitter1,endTwitter,heatmapVariable
    #new google.maps.LatLng(-6.9742784,109.122315),
    FORMAT = 'new google.maps.LatLng('
    addToHTML=''
    for i in range(len(data)):
        lat = data[i][0]
        long = data[i][1]
        add = FORMAT + str(lat) + ','+str(long)+'),'
        addToHTML+=add
    addToHTML=addToHTML[:-1] #remove last comma
    if state==0:
        heatmapVariable = initial1+addToHTML+twitter1 #set var for future rewrites to add twitter
        f = open('templates/predictionHeatmap.html','w')
        f.write(initial1+addToHTML+initial2) #INITIAL HEATMAP WITH NO TWITTER POINTS
        f.close()
    elif state == 1:
        f = open('templates/predictionHeatmap.html','w')
        f.write(heatmapVariable+addToHTML+endTwitter) #INITIAL HEATMAP WITH NO TWITTER POINTS
        f.close()
    else:
        print('That is not a valid state')
    

def crowdSourceInformation():
	#Create twitter streamer class
	print('Beginning Twitter Crowdsource Bot')
	class CustomStreamListener(tweepy.StreamListener):
		def on_status(self, status): 
			#Check if CSV exists. Else, create it.
			if os.path.isfile('csv-files/terrortracking.csv') == False:
				with open('csv-files/terrortracking.csv','w',newline='',encoding='utf-8') as f:
					writer=csv.writer(f)
					writer.writerow(['Screen name','Created At','Location','Lat','Long','Media link'])
					
			with open('csv-files/terrortracking.csv', 'a',newline="") as f: 
				writer = csv.writer(f)
				try:
					lat=status.coordinates['coordinates'][0]
					long=status.coordinates['coordinates'][1]
				except:
					lat=''
					long=''
				try:
					geo = status.place.name
				except:
					geo=''
				media = status.entities.get('media', [])
				if(len(media) > 0):
					media=media[0]['media_url']
					#name=str(status.created_at)+'_'+status.author.screen_name
					#name += self.extensionFinder(media)
					wgetter.download(media,outdir="TerrorAttachment")
					
				writer.writerow([status.author.screen_name, status.created_at, status.text,geo,lat,long,media])
		def on_error(self, status_code):
			print ( sys.stderr, 'Encountered error with status code:', status_code)
			return True # Don't kill the stream
	
		def on_timeout(self):
			print ( sys.stderr, 'Timeout...')
			return True # Don't kill the stream
	"""
	Main twitter function. Creates the customstream listener class and begins streaming tweets.
	"""      
	def twitterCatcherStream():
		#remove 3 lines below and replace client ID and stuff before submission
		accesstokenlist=[]
		accesstokenlist.append(['2FLlfrbBb2ldxHDs4ulwTbwAF','lWcdpSPt1kNjQp12HXoKFl8YhuEDMlEoZJU2OZkljMLZcVVPeY','464726631-wf0YX3qpxFcX583TNdRetYkHctwwJYdlQOohMSvQ','c3PK4xGIZUZK93GpkGTzFN3RaSFZvXZ78hJ8FaEig8741'])
		currentKey = accesstokenlist[0]
		### end removal
		
		auth = tweepy.auth.OAuthHandler(currentKey[0], currentKey[1])
		auth.set_access_token(currentKey[2], currentKey[3])
		api = tweepy.API(auth)
		l=CustomStreamListener()
		stream = tweepy.Stream(api.auth, l)
		stream.userstream('terrorBgone')
		stream.filter(track=['@terrorBgone'],async=True)
	twitterCatcherStream()

def run():
	print('***Welcome to the Integrated Terrorism Response Solution done by Andre, Eddy, and Thiru***')
	country = input("What is your Country?: ")
	print("\n")
	predictedGroup = predictTerroristGroup()
	location = printTerroristDetails(predictedGroup)
	plotRiskyLocations(location,country)
	#crowdSourceInformation()
	
if __name__ == '__main__':
	run()
