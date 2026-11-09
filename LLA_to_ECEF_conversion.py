import pandas as pd
import numpy as np
import sys



# Algorithmic techniques from previous codes written by me during my work at CIWRO were iterated upon for use in this source code.



#take CLAs
if (len(sys.argv) > 1): # checking for command line arguments
    if len(sys.argv) > 2: # making sure there's only one argument
        sys.exit("\nToo many inputs. Please provide one integer between 1532332859 and 1532335359.")

    inp = sys.argv[1] # assign the second argument to "inp"

    if inp.isdigit() == False: # make sure the second argument is a number
        sys.exit("\nInput is not a number. Please provide an integer between 1532332859 and 1532335359.")

    inp = int(inp) # convert input to an integer after confirming it is a number, note this will round down if the provided argument is a decimal.

    if (inp < 1532332859) or (inp > 1532335359): # making sure the input is within the range of the data
        sys.exit("\nInput not within range of data. Please provide an integer between 1532332859 and 1532335359.")



#import csv from the native folder into a pandas dataframe
file = 'SciTec_code_problem_data.csv'
rawdf = pd.read_csv(file, names=['time', 'lat', 'lon', 'alt'])



#create functions to convert variables from LLA to ECEF (ECEF coordinates are calculated in meters). Formulas taken from personal notes on datum transformations from an Advanced Atmospheric Dynamics course at the University of Oklahoma.
#define parameters. Parameters taken from "Datum Transformations of GPS Positions," instructions provided by SciTec. 
a = 6378137 # semi-major axis (meters)
f = 1/(298.25722356) # flattening factor
b = a*(1 - f) # semi-minor axis
e2 = 1 - (b / a) ** 2 # square of eccentricity
def getX(lat, lon, alt): # function that returns the value of X in ECEF coordinate plane when provided with lat/lon in degrees and altitude in meters
    lat = np.radians(lat) # convert degrees to radians
    lon = np.radians(lon) # convert degrees to radians
    h = alt*1000 # height above elipsoid in meters (altitude)

    N = a / np.sqrt(1 - ( (e2) * np.sin(lat)**2 ) ) # radius of curvature
    x = (N + h) * np.cos(lat) * np.cos(lon)
    return x

def getY(lat, lon, alt): # function that returns the value of Y in ECEF coordinate plane when provided with lat/lon in degrees and altitude in meters
    lat = np.radians(lat) # convert degrees to radians
    lon = np.radians(lon) # convert degrees to radians
    h = alt*1000 # height above elipsoid in meters (altitude)

    N = a / np.sqrt(1 - ( (e2) * np.sin(lat)**2 ) ) # radius of curvature
    y = (N + h) * np.cos(lat) * np.sin(lon)
    return y

def getZ(lat, lon, alt): # function that returns the value of Z in ECEF coordinate plane when provided with lat/lon in degrees and altitude in meters
    h = alt*1000 # height above elipsoid in meters (altitude)
    lat = np.radians(lat) # convert degrees to radians
    lon = np.radians(lon) # convert degrees to radians

    N = a / np.sqrt(1 - ( (e2) * np.sin(lat)**2 ) ) # radius of curvature
    z = ( ( (1 - e2) * N) + h) * np.sin(lat)
    return z



#apply functions to dataframe and create new dataframe with converted coordinate values
df = rawdf # assign raw df to a new df to work with
df['X'] = (getX(df['lat'], df['lon'], df['alt'])) # creates a new value in each row for ECEF coordinate X based on the lat, lon, alt for that row
df['Y'] = (getY(df['lat'], df['lon'], df['alt'])) # creates a new value in each row for ECEF coordinate Y based on the lat, lon, alt for that row
df['Z'] = (getZ(df['lat'], df['lon'], df['alt'])) # creates a new value in each row for ECEF coordinate Z based on the lat, lon, alt for that row
ECEFdf = df.drop(['lat','lon','alt'], axis=1) # remove old coordinate values
# print(ECEFdf.iloc[0:20:,:]) # un-comment this line to check first 20 rows of dataframe at this point in the source code



#find rate of change between XYZ coordinates
ECEFdf['time_diff'] = ECEFdf['time'].diff() # creates new value in each row that calculate difference in time between current row and previous row into a new column
ECEFdf['X_vel_ms-1'] = ECEFdf['X'].diff() / ECEFdf['time_diff'] # creates new value that calculates change in X from the last datapoint, then divides by the change in time (rate of change)
ECEFdf['Y_vel_ms-1'] = ECEFdf['Y'].diff() / ECEFdf['time_diff'] # creates new value that calculates change in Y from the last datapoint, then divides by the change in time (rate of change)
ECEFdf['Z_vel_ms-1'] = ECEFdf['Z'].diff() / ECEFdf['time_diff'] # creates new value that calculates change in Z from the last datapoint, then divides by the change in time (rate of change)
# print(ECEFdf.iloc[0:20:,:]) # un-comment this line to check first 20 rows of dataframe at this point in the source code

ECEFdf = ECEFdf.drop(['X','Y','Z','time_diff'], axis=1) # reduce dataframe down to time series of XYZ velocities
ECEFdf['time'] = ECEFdf['time'].round(decimals=0) # round times to nearest integer
ECEFdf = ECEFdf.set_index('time') # set time to index
ECEFdf = ECEFdf.rename_axis(None, axis=0) # remove label for index



#lineraly interpolate velocity values between known datapoints
ECEFdf.index = pd.to_datetime(ECEFdf.index, unit='s') # convert ECEFdf to datetime in order to begint he process of filling in missing datapoints
fullrangedf = pd.date_range(start=ECEFdf.index[0], end=ECEFdf.index[-1], freq='1S') # create an empty dataframe with an index that spands the range of ECEFdf but including the rows for missing times
ECEFdf = ECEFdf.reindex(fullrangedf) # remake ECEFdf by joining the indicies of the two dataframes while keeping the original data
ECEFdf.index = ECEFdf.index.astype(int) // 10**9 # reset index back to Unix time by diving by 10**9 since the datetime index is in nanoseconds
ECEFdf = ECEFdf.interpolate(method='linear') # replace NaN valuesa with linearly interpolated data between known values
ECEFdf.fillna(0, inplace=True) # replace NaN values with 0, the velocity of the data that references the first known datapoint will be 0
# print(ECEFdf.iloc[1000:1030:,:]) # un-comment this line to check first 20 rows of dataframe at this point in the source code



#print velocity vectors at the command line input time, as well as two fixed times of 1532334000 and 1532335268
print(f'\nThe velocity vector for X, Y, and Z respectively, in units of m·s⁻¹, at 1532334000 seconds is:\n{ECEFdf.loc[1532334000].to_csv(index=False, header=False).strip()}',f'\n\nThe velocity vector for X, Y, and Z respectively, in units of m·s⁻¹, at 1532335268 seconds is:\n{ECEFdf.loc[1532335268].to_csv(index=False, header=False).strip()}')
if (len(sys.argv) > 1): # print the velocity vector at input time if there is one
    input = int(sys.argv[1])
    print(f'\nThe velocity vector for X, Y, and Z respectively, in units of m·s⁻¹, at the requested time of {input} is:\n{ECEFdf.loc[input].to_csv(index=False, header=False).strip()}')
else:
    print('\nNo additional velocity values requested.')