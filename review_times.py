import requests
from obspy import UTCDateTime
import pandas as pd
from scipy import stats

# starttime and endtime -  use YYYY-MM-DDTHH:MM:SS
starttime = "2020-01-01T00:00:00"
endtime = "2020-07-01T00:00:00"

# Earthuake pull request - defines as inside network interest and after or between specified timeframes -

earthquakes = requests.get("https://wfs.geonet.org.nz/geonet/ows?service=WFS&version=1.0.0&request=GetFeature&typeName=geonet:"
                           "quake_search_v1&outputFormat=json&cql_filter=origintime>" + starttime + "+AND+origintime<" + endtime + 
                           "+AND+BBOX(origin_geom,163,-33,185,-50)").json()

#empty lists to append to
history_json, quakeid, prelimjson, bestjson = [], [], [], []

#generate list of quake ids
for index, quake in enumerate(earthquakes['features']):
    quakeid.append(quake['properties']['publicid'])
#generate "history" for each quake by running an api query within a for loop
for id in quakeid:
    history_json.append(requests.get("https://api.geonet.org.nz/quake/history/"  + id).json())
    
#for loop to split in to prelim and best quality solutions. 
for a in range(len(history_json)):
    for ind, value in enumerate(history_json[a]['features']):
        # below tests whether value is prelim or not and if so generates a dictionary of id, modification time and origin time
        # using ObsPy's UTCDateTime function as it's nice and tidy and good for subtracting times, automatically parses.
        if value['properties']['quality'] == 'preliminary':
            prelimjson.append({"id":value['properties']['publicID'],
                               "modtime":UTCDateTime(value['properties']['modificationTime']),
                               "origtime":UTCDateTime(value['properties']['time'])})
            
        # as above but for "best" solutions    
        if value['properties']['quality'] == 'best':
            bestjson.append({"id":value['properties']['publicID'],
                             "modtime":UTCDateTime(value['properties']['modificationTime']),
                             "origtime":UTCDateTime(value['properties']['time'])})         
            
# calculation of first prelim review time
df = pd.DataFrame(prelimjson) # converts dictionary into dataframe    
ids = df.groupby('id') # groups by quakeid, as there are duplicates for each value
firstprelim = ids.last() # takes the last value of each group which is the first in terms of time
firstprelim['reviewtime'] = firstprelim['modtime'] - firstprelim['origtime'] #calculates review time

#print outpt below, currently a trimmed mean at 10% either side 
print("Trimmed mean for preliminary commit: " + str(stats.trim_mean(firstprelim['reviewtime'], 0.1)))
print("Median for preliminary commit: " + str(firstprelim['reviewtime'].median()))

# as above but with best instead of prelim
df2 = pd.DataFrame(bestjson)
ids2 = df2.groupby('id')
firstbest = ids2.last()
firstbest['reviewtime'] = firstbest['modtime'] - firstbest['origtime']
print("Trimmed mean for first best commit: " + str(stats.trim_mean(firstbest['reviewtime'], 0.1)))
print("Median for first best commit: " + str(firstbest['reviewtime'].median()))
