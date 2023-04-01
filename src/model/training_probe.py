from datetime import datetime, timedelta
import numpy as np
from typing import Callable
from ..server.database import DatabaseProvider

# CONST
NO_VALUES = 3


# collect data from database
def _get_data() -> list[tuple[str,float]]:
    connection = DatabaseProvider()
    cursor = connection.handler()
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


# return index of data with matching date, if there is no such date raises exception
def _get_index_date(date: datetime, data: list[tuple[str, float]]) -> int:
    for i in range(round(len(data) / 2) - 1):
        if date == datetime.strptime(data[i][0], "%Y-%m-%d"):
            return i
    raise Exception("Invalid date")


def _correct_date(dateStart: datetime, dateEnd: datetime) -> bool:
    if dateEnd > dateStart:
        return False
    return True


#return number of days between given dates
def _get_available_days(dateStart: datetime, dateEnd: datetime) -> int:
    return (dateEnd - dateStart).days + 1

def _basic_compressing_function(x: int) -> int:
  return x*x + x + 1

# return amount of needed days
def _calc_vector_length(noDays: int, ageLimit: int = 10, compressing_function: Callable[[int], int] = _basic_compressing_function) -> int:
    age = 0
    length = 0
    lengthInDays = 1
    while noDays > 0:
        length += 1
        age += 1
        noDays -= lengthInDays
        if age % ageLimit == 0:
            lengthInDays = compressing_function(age/ageLimit)
    return length * NO_VALUES + 1


#def get_vector_columns(dateStart: datetime, dateEnd: datetime, ageLimit: int = 10) -> int:
#    """Get length of vector after compression of data."""
#    return _get_vector_length(_get_no_days(dateStart, dateEnd), ageLimit)


def get_vector(dateEnd: datetime, noDays: int, ageLimit: int = 10, compressing_function: Callable[[int], int] = _basic_compressing_function) -> tuple[np.ndarray, np.ndarray]:
    """Generate vectors for learning."""

    # data set consists of 3 values per day: High, Avg, Low
    data = _get_data()
    
    timeJump = 1  # how many days will be used for this data set in the vector
    age = 0  # how many times same timeJump has been used for this vector
    counter = 0  # how many days has been used in this data set
    dataSetCounter = 0  # how many data sets have been prepared
    tempData = np.zeros((NO_VALUES))
    
    indexEnd = _get_index_date(dateEnd, data)
    _get_index_date(dateEnd - timedelta(days=noDays-1), data)

    length = _calc_vector_length(noDays, ageLimit, compressing_function) #length of a vector
    vector = np.zeros(length)  # input data

    y_value = data[indexEnd + 1][1]  # output data

    # last value of each vector is a month (starting time)
    vector[length - 1] = datetime.strptime(data[indexEnd][0], "%Y-%m-%d").month

    # max number of vectors that can be achieved with set parameters from data file
    for i in range(noDays):
        if counter == 0:
            # values as in data file
            tempData[0] = data[indexEnd - i][1]  # High
            tempData[1] = data[indexEnd - i][1]  # Avg
            tempData[2] = data[indexEnd - i][1]  # Low
        else:
            # values of multiple days streamlined into one
            tempData[0] = max(data[i + indexEnd][1], tempData[0])  # High
            tempData[1] = (data[i + indexEnd][1] + tempData[1]) / 2  # Avg
            tempData[2] = min(data[i + indexEnd][1], tempData[2])  # Low

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
            if age % ageLimit == 0:
                timeJump = compressing_function(age/ageLimit)
    if counter != 0:
        for k in range(dataSetCounter * NO_VALUES, dataSetCounter * NO_VALUES + NO_VALUES):
            vector[k] = tempData[k % NO_VALUES]
    return vector, y_value


def get_vectorS(dateEnd: datetime, dateStart: datetime, noDays: int, ageLimit: int = 10, compressing_function: Callable[[int], int] = _basic_compressing_function) -> tuple[np.ndarray, np.ndarray]:
    """Get set of vectors and array of expected values."""
    if not _correct_date(dateEnd, dateStart):
        raise Exception("Invalid date")
    length = _calc_vector_length(noDays, ageLimit, compressing_function)
    availableDays = _get_available_days(dateStart, dateEnd)
    noRows = availableDays - noDays + 1
    if noRows < 1:
        raise Exception("Vector is too long")
    vectors = np.zeros((noRows, length))
    y_values = np.zeros((noRows, 1))
    for i in range(noRows):
        timeshift = timedelta(days=i)
        vectors[i], y_values[i] = get_vector(dateEnd - timeshift, noDays, ageLimit, compressing_function)
    return vectors, y_values


#!!!!!!!!!!!!!!
# EXAMPLE OF USE
# Dataset means set of three values: Min, Avg and Max, which are based on values found across multiple days

# dateEnd = datetime(2015, 1, 1) # Date from which we move BACKWARD while filling our vector
# noDays = 7 # How many days are part of single vector, it is NOT length of a vector
# ageLimit = 3 # After how many datasets level of compression is to go up
# compressing_function = _basic_compressing_function # When ageLimit is reached, change number of days put into dataset to next value of the function
# vector, y_value = get_vector(dateEnd, noDays, ageLimit, compressing_function) # single vector

# for multiple vectors
# dateStart = datetime(2014, 1, 1) # After reaching this date we stop making more vectors
# vectors, y_values = get_vectorS(dateEnd, dateStart, noDays, ageLimit, compressing_function)
