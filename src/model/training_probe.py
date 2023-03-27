import math
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

from src.server.database_provider import get_database_connection

# CONST
NO_VALUES = 3


# collect data from database
def _get_data() -> list[tuple[str,float]]:
    connection = get_database_connection()
    cursor = connection.cursor()
    sql_data = """
      SELECT
      date,
      value
      FROM
      exchange_rate_history
      GROUP BY date;
             """
    cursor.execute(sql_data)
    data = cursor.fetchall()
    cursor.close()
    return data


# returns index of data with matching date
def _for_date(date: datetime, data: list[tuple[str, float]]) -> int:
    for i in range(round(len(data) / 2)):
        if date == datetime.strptime(data[i][0], "%Y-%m-%d"):
            return i
    return -1


# returns two indexes of data with matching dates
def _get_index_start_end(dateStart: datetime, dateEnd: datetime, data: list[tuple[str, float]]) -> tuple[int,int]:
    indexStart = _for_date(dateStart, data)
    indexEnd = _for_date(dateEnd, data)
    return indexStart, indexEnd


def _correct_date(dateStart: datetime, dateEnd: datetime) -> bool:
    if dateStart > dateEnd:
        return False
    return True


# returns number of days between given dates
def _get_no_days(dateStart: datetime, dateEnd: datetime) -> int:
    return (dateEnd - dateStart).days + 1


# returns length of vector after compression of data
def _get_vector_length(numOfDays: int, ageLimit: int) -> int:
    length = 0
    age = 0
    lengthInDays = 1
    while numOfDays > 0:
        length += 1
        age += 1
        numOfDays -= lengthInDays
        if age % ageLimit == 0:
            lengthInDays += 1
    return length * NO_VALUES + 1  # accounting for additional month value


def get_vector_columns(dateStart: datetime, dateEnd: datetime, ageLimit=10) -> int:
    """Get length of vector after compression of data."""
    return _get_vector_length(_get_no_days(dateStart, dateEnd), ageLimit)


def get_vector(dateStart: datetime, dateEnd: datetime, ageLimit=10) -> tuple[np.ndarray, np.ndarray]:
    """Generate vectors for learning."""
    if not _correct_date(dateStart, dateEnd):
        raise Exception("Invalid data")

    # data set consists of 3 values per day: High, Avg, Low
    data = _get_data()
    noDays = _get_no_days(dateStart, dateEnd)

    timeJump = 1  # how many days will be used for this data set in the vector
    age = 0  # how many times same timeJump has been used for this vector
    counter = 0  # how many days has been used in this data set
    dataSetCounter = 0  # how many data sets have been prepared
    tempData = np.zeros((NO_VALUES))
    length = get_vector_columns(dateStart, dateEnd, ageLimit)  # length of compressed data

    vector = np.zeros(length)  # input data
    indexStart, indexEnd = _get_index_start_end(dateStart, dateEnd, data)
    y_value = data[indexStart - 1][1]  # output data

    # last value of each vector is a month (starting time)
    vector[length - 1] = datetime.strptime(data[indexEnd][0], "%Y-%m-%d").month

    # max number of vectors that can be achieved with set parameters from data file
    for i in range(noDays):
        if counter == 0:
            # values as in data file
            tempData[0] = data[i + indexStart][1]  # High
            tempData[1] = data[i + indexStart][1]  # Avg
            tempData[2] = data[i + indexStart][1]  # Low
        else:
            # values of multiple days streamlined into one
            tempData[0] = max(data[i + indexStart][1], tempData[0])  # High
            tempData[1] = (data[i + indexStart][1] + tempData[1]) / 2  # Avg
            tempData[2] = min(data[i + indexStart][1], tempData[2])  # Low

        # after performing above operations day is added to the count
        counter += 1

        # if data set is fully realised (enough days worth of data was compiled into it),
        # fill vector with it
        if counter == timeJump:
            for k in range(dataSetCounter * NO_VALUES, dataSetCounter * NO_VALUES + NO_VALUES):
                vector[k] = tempData[k % NO_VALUES]
            dataSetCounter += 1
            counter = 0
            # after injecting data into vector, add to the count of data sets with the same
            # timeJump in this vector
            age += 1
            # if enough same days length data sets has been used, expand the scope (move timeJump
            # by 1 step)
            if age == ageLimit:
                age = 0
                timeJump += 1
    for k in range(dataSetCounter * NO_VALUES, dataSetCounter * NO_VALUES + NO_VALUES):
        vector[k] = tempData[k % NO_VALUES]
    return vector, y_value


def get_vectorS(dateStart: datetime, dateEnd: datetime, noRows: int, ageLimit=10) -> tuple[np.ndarray, np.ndarray]:
    """Get set of vectors and array of expected values."""
    length = get_vector_columns(dateStart, dateEnd, ageLimit)
    vectors = np.zeros((noRows, length))
    y_values = np.zeros((noRows, 1))
    for i in range(noRows):
        timeshift = timedelta(days=i)
        vectors[i], y_values[i] = get_vector(dateStart + timeshift, dateEnd + timeshift)
    return vectors, y_values


#!!!!!!!!!!!!!!
# EXAMPLE OF USE
# dateStart = datetime(2014, 1, 1)
# dateEnd = datetime(2015, 1, 1)
# vector, y_value = get_vector(dateStart, dateEnd) #single vector

# for multiple vectors
# vectors, y_values = get_vectorS(dateStart, dateEnd, noRows) #returns noRows vectors ie. array shape = (noRows, vectorLength)
