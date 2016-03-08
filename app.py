from flask import Flask, render_template, url_for

#internal libraries
import itertools,csv,sys,os,pickle
#External libraries
import gmaps,tweepy,wgetter,numpy as np,pandas as pd
from sklearn.externals import joblib
from TrainClassifier import labelHash, separate_column_by_type, process_nontext
import Compiled as cp
from scipy import stats
from geopy.geocoders import Nominatim
import operator
app = Flask(__name__)

@app.route("/")
def main():
    return render_template('index.html')

@app.route("/dashboard")
def dashboard():

    pred,location,mult,casualties,weaptype,propdmg,nperps="ISIS","Police",9.4,2.3,"Explosives",52.8,3
    pred = cp.predictTerroristGroup()
    # mult = float(cp.multipleAttacks(pred))*100
    # location = cp.typeFreqPlaceAttacked(pred)
    # casualties = cp.numOfCasualties(pred)
    # weaptype = cp.findTypeOfWeapon(pred)
    # propdmg = float(cp.findPropertyDamage(pred))*100
    # nperps = cp.numPerps(pred)
    # cp.plotRiskyLocations(location)
    
    return render_template('dashboard.html',
    	prediction=pred,
    	location=location,
    	mult=mult,
    	casualties_num=casualties,
    	weaptype=weaptype,
    	propdmg_prob=propdmg,
    	numperps_arr=nperps)

@app.route("/heatmap")
def heatmap():
    return render_template('heatmap.html')


if __name__ == "__main__":
	app.run(debug=True)