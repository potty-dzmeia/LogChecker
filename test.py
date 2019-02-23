import glob
from bs4 import UnicodeDammit
import os
from participant import Participant

FREQ = 1
MODE = 2
DATE = 3
TIME = 4
CALL = 5
SND1 = 6
SND2 = 7
HISCALL = 8
RCV1 = 9
RCV2 = 10


def isTimeIntervalLessThan(qso1, qso2, timeinterval):
    """
    Checks if the time interval between the two QSOs is less then timeinterval
    :param qso1: list of the type ['QSO:', '3515', 'CW', '2016-08-20', '0800', 'LZ0AT', '001', '000', 'LZ0AU', '001', '000']
    :type qso1: list
    :param qso2: list of the type ['QSO:', '3515', 'CW', '2016-08-20', '0800', 'LZ0AT', '001', '000', 'LZ0AU', '001', '000']
    :type qso2: list
    :param timeinterval: Time interval in miutes
    :type timeinterval: int
    :return:
    """
    # convert string to actual date and time
    date_format = "%Y-%m-%d %H:%M"

    time1 = datetime.strptime(" ".join([qso1[DATE], qso1[TIME]]), date_format)
    time2 = datetime.strptime(" ".join([qso2[DATE], qso2[TIME]]), date_format)
    diff = time2 - time1

    print(diff)


isTimeIntervalLessThan()