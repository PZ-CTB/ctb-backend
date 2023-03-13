import pandas as pd
import numpy as np
import math


df = pd.read_csv('coin_Bitcoin.csv') #reading csv file

#data set consists of 5 values: High, Low, Open, Close, Volume

age = 0 #how many times same timeJump has been used for this vector
counter = 0 #how many days has been used in this data set
loop = 0 #how many data sets were already put in this vector
rows = 0 #which vector is being prepared right now
timeJump = np.array([1, 3, 7, 14, 30]) #how many days will be used for this data set in the vector
tjIndex = 0 #used to mark which timeJump is being used
tempData = np.zeros((5));

#size is calculated based on size of data from file, length (in days) of one vector and difference between neighbouring vector starting (ending) time
vectors = np.zeros((math.floor((df.Date.size-372)/30) + 1, 40*5)); #40 - number of max loops in vector, 5 - number of values
vectors[0] = df.High[df.Date.size-1] #High
vectors[1] = df.Low[df.Date.size-1] #Low
vectors[2] = df.Open[df.Date.size-1] #Open
vectors[3] = df.Close[df.Date.size-1] #Close
vectors[4] = df.Volume[df.Date.size-1] #Volume

#max number of vectors that can be achieved with set parameters from data file
while (df.Date.size - 372 - rows*30 > 0):
  for i in range(df.Date.size-2 - rows*30, df.Date.size-375 - rows*30, -1):
    if counter == 0:
      #values as in data file
      tempData[0] = df.High[i] #High
      tempData[1] = df.Low[i] #Low
      tempData[2] = df.Open[i] #Open
      tempData[3] = df.Close[i] #Close
      tempData[4] = df.Volume[i] #Volume
    else:
      #values of multiple days streamlined into one
      tempData[0] = max(df.High[i], tempData[0])
      tempData[1] = min(df.Low[i], tempData[1])
      tempData[2] = sum([df.Open[i], tempData[2]])/2
      tempData[3] = sum([df.Close[i], tempData[3]])/2
      tempData[4] = sum([df.Volume[i], tempData[4]])/2

    #after performing above operations day is added to the count
    counter += 1

    #if vector is full, start working on the next one
    if loop == 40:
      loop = 0
      rows += 1

    #print(loop, end=', ')
    #print(rows)

    #if data set is fully realised (enough days worth of data was compiled into it), fill vector with it
    if (tjIndex != 5) and (counter == timeJump[tjIndex]):
      for k in range(loop*5, loop*5 + 5, 1):
        vectors[rows][k] = tempData[k%5]
      loop += 1
      counter = 0
      #after injecting data into vector, add to the count of data sets with the same timeJump in this vector
      age += 1
      #if enough same days length data sets has been used, expand the scope (move timeJump by 1 step)
      if age == (10 - tjIndex):
        tjIndex += 1
        age = 0
  tjIndex = 0
  age = 0
  counter = 0
  loop = 0
print(vectors)