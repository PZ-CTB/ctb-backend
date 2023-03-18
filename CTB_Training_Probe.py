import math

import numpy as np
import pandas as pd

from datetime import datetime

#function 'simulating' data from API
#all its instances should be replaced with API readings
def avg_value(a, b, c, d):
  return (a + b + c + d)/4

df = pd.read_csv("coin_Bitcoin.csv")  # reading csv file

# data set consists of 4 values: High, Low, Open, Close
numOfValues = 4
age = 0  # how many times same timeJump has been used for this vector
counter = 0  # how many days has been used in this data set
loop = 0  # how many data sets were already put in this vector
rows = 0  # which vector is being prepared right now
timeJump = np.array([1, 3, 7, 14, 30])  # how many days will be used for this data set in the vector
tjIndex = 0  # used to mark which timeJump is being used
probeDist = 1 # distance in days between starting of each data set
tempData = np.zeros((numOfValues))



# size is calculated based on size of data from file, length (in days) of one vector and difference
# between neighbouring vector starting (ending) time
vectors = np.zeros((math.floor((df.Date.size - 372) / probeDist) + 1, 40 * numOfValues - 10 * (numOfValues - 1) + 1))  # input data
y_values = np.zeros((math.floor((df.Date.size - 372) / probeDist) + 1, 1))  # output data
# 40 - number of max loops in vector, 4 - number of values


# fills output with corresponding day values
for g in range (0, y_values.size):
    y_values[g] = avg_value(df.High[df.Date.size - 1 - g*probeDist], df.Low[df.Date.size - 1 - g*probeDist], df.Open[df.Date.size - 1 - g*probeDist], df.Close[df.Date.size - 1 - g*probeDist])


# max number of vectors that can be achieved with set parameters from data file
while df.Date.size - 371 - rows * probeDist > 0:
    # last value of each vector is a month (starting time)
    date = datetime.strptime(df.Date[df.Date.size-1 - rows*probeDist], '%Y-%m-%d %H:%M:%S')
    vectors[rows][vectors.shape[1] - 1] = date.month

    # fills first 10 days, as they do not have different high, low, open and close values
    for l in range (0, 10):
            vectors[rows][l] = avg_value(df.High[df.Date.size - 2 - rows * probeDist - l], df.Low[df.Date.size - 2 - rows * probeDist - l], df.Open[df.Date.size - 2 - rows * probeDist - l], df.Close[df.Date.size - 2 - rows * probeDist - l])

    for i in range(df.Date.size - 2 - 10 - rows * probeDist, df.Date.size - 372 - rows * probeDist, -1):
        if counter == 0:
            # values as in data file
            avgData = avg_value(df.High[i], df.Low[i], df.Open[i], df.Close[i])
            tempData[0] = avgData  # High
            tempData[1] = avgData  # Low
            tempData[2] = avgData  # Open
            tempData[3] = avgData  # Close
        else:
            # values of multiple days streamlined into one
            avgData = avg_value(df.High[i], df.Low[i], df.Open[i], df.Close[i])
            tempData[0] = max(avgData, tempData[0])  # High
            tempData[1] = min(avgData, tempData[1])  # Low
            tempData[3] = avgData  # Close

        # after performing above operations day is added to the count
        counter += 1

        # if vector is full, start working on the next one
        if loop == 30:
            loop = 0
            rows += 1

        # print(loop, end=', ')
        # print(rows)

        # if data set is fully realised (enough days worth of data was compiled into it),
        # fill vector with it
        if (tjIndex != numOfValues) and (counter == timeJump[tjIndex]) and (rows < vectors.shape[0]):
            for k in range(10 + loop * numOfValues, 10 + loop * numOfValues + numOfValues, 1):
                vectors[rows][k] = tempData[(k - 10) % numOfValues]
            loop += 1
            counter = 0
            # after injecting data into vector, add to the count of data sets with the same
            # timeJump in this vector
            age += 1
            # if enough same days length data sets has been used, expand the scope (move timeJump
            # by 1 step)
            if age == (10 - tjIndex):
                tjIndex += 1
                age = 0
    tjIndex = 0
    age = 0
    counter = 0
    loop = 0

#print(vectors)
