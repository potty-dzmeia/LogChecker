#!/usr/bin/env python
from datetime import datetime, time

import chardet
import glob
from bs4 import UnicodeDammit
import os
from participant import Participant



CALLSIGN = "CALLSIGN:"
NAME = "NAME:"

DELTA_TIME = 3 #in minutes

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

def getFileEncoding1(filename):
    """
    Returns the character encoding of a file using chardet
    :param filename: path to the file
    :type filename: str
    :return: String of the type "latin-1"
    :rtype: str
    """
    result = chardet.detect(open(filename, "rb").read())
    return result['encoding']

def getFileEncoding2(filename):
    """
    Returns the character encoding of a file using Dammit
    :param filename: path to the file
    :type filename: str
    :return: String of the type "latin-1"
    :rtype: str
    """
    raw = open(filename, "rb").read()
    dammit = UnicodeDammit(raw)
    return dammit.original_encoding


# def getExtractLog(filename):
#     """
#     Extracts participant data(callsign, name etc) and his log from the supplied file
#     :param filename: file that needs to be parsed
#     :type filename: str
#     :return:
#     :rtype: (Participant, list)
#     """
#     particpant = Participant()
#     log = []
#
#     logfile = open(filename, "r", encoding=getFileEncoding2(filename))
#
#     for line in logfile:
#         line_split = line.split()
#         if line_split[0] == "CALLSIGN:":
#             particpant.callsign = line_split[1].upper()
#         elif line_split[0] == "NAME:":
#             particpant.name = " ".join(line_split[1:])
#         elif line_split[0] == "CATEGORY:":
#             particpant.category = " ".join(line_split[1:])
#         elif line_split[0] == "QSO:":
#             log.append(line_split)
#
#
#     return particpant, log


def parseLog(filename):
    """
    Extracts participant data(callsign, name etc) and his log from the supplied file
    :param filename: file that needs to be parsed
    :type filename: str
    :return:
    :rtype: Participant
    """
    participant = Participant()

    print("parsing log: " + filename)

    logfile = open(filename, "r", encoding=getFileEncoding2(filename))

    for line in logfile:
        line_split = line.split()
        try:
            if line_split[0] == "CALLSIGN:":
                participant.callsign = line_split[1].upper()
            elif line_split[0] == "NAME:":
                participant.name = " ".join(line_split[1:])
            elif line_split[0] == "CATEGORY:":
                participant.category = " ".join(line_split[1:])
            elif line_split[0] == "QSO:":
                participant.log.append(line_split)
        except:
            pass # empty line

    participant.QSOs = len(participant.log)
    print("parsed log: "+participant.callsign)
    return participant


def isDupe(qso1, qso2, timeinterval):
    """
    Checks if the time interval between the two QSOs is bigger then the timeinterval

    :param qso1: list of the type ['QSO:', '3515', 'CW', '2016-08-20', '0800', 'LZ0AT', '001', '000', 'LZ0AU', '001', '000']
    :type qso1: list
    :param qso2: list of the type ['QSO:', '3515', 'CW', '2016-08-20', '0800', 'LZ0AT', '001', '000', 'LZ0AU', '001', '000']
    :type qso2: list
    :param timeinterval: Time interval in miutes
    :type timeinterval: int
    :return:
    """

    if qso1[HISCALL] != qso2[HISCALL]:
        return # not the same station


    # convert string to actual date and time
    date_format = "%Y-%m-%d %H%M"

    time1 = datetime.strptime(" ".join([qso1[DATE], qso1[TIME]]), date_format)
    time2 = datetime.strptime(" ".join([qso2[DATE], qso2[TIME]]), date_format)
    if time1.timestamp()>time2.timestamp():
        diff = time1-time2
    else:
        diff = time2-time1

    if diff.seconds/60 >= timeinterval:
        return False
    else:
        return True



def checkExchange(qso1, qso2):
    """
    Check if the serials from the two qso match

    :param qso1:
    :param qso2:
    :return:
    """
    return int(qso1[SND1]) == int(qso2[RCV1]) and int(qso1[SND2]) == int(qso2[RCV2]) and int(qso2[SND1]) == int(qso1[RCV1]) and int(qso2[SND2]) == int(qso1[RCV2])


def isTimeWithinDelta(qso1, qso2, delta):
    """
       Checks if the time interval between the two QSOs is less then delta

       :param qso1: list of the type ['QSO:', '3515', 'CW', '2016-08-20', '0800', 'LZ0AT', '001', '000', 'LZ0AU', '001', '000']
       :type qso1: list
       :param qso2: list of the type ['QSO:', '3515', 'CW', '2016-08-20', '0800', 'LZ0AT', '001', '000', 'LZ0AU', '001', '000']
       :type qso2: list
       :param delta: Time interval in miutes
       :type delta: int
       :return:
       """

    # convert string to actual date and time
    date_format = "%Y-%m-%d %H%M"

    time1 = datetime.strptime(" ".join([qso1[DATE], qso1[TIME]]), date_format)
    time2 = datetime.strptime(" ".join([qso2[DATE], qso2[TIME]]), date_format)
    if time1.timestamp() > time2.timestamp():
        diff = time1 - time2
    else:
        diff = time2 - time1

    if diff.seconds / 60 < delta:
        return True
    else:
        return False



def crossCheck(qso, participantA, participantB):
    """
    Checks if the "qso" is available in the "log" of the correspondent
    :param qso:
    :type qso: list of the type ['QSO:', '3515', 'CW', '2016-08-20', '0800', 'LZ0AT', '001', '000', 'LZ0AU', '001', '000']
    :param log:
    :type log: list of qso
    :param detlaTime: It is assumed that the difference in the times recorded in both logs should be less then detlaTime[minutes]
    :type detlaTime: int
    :return: True if the check was successful
    :rtype: bool
    """
    assert(qso[HISCALL]==participantB.log[0][CALL])

    for q in participantB.log:

        if qso[CALL] == q[HISCALL] and isTimeWithinDelta(qso, q, 3):
            # if qso[CALL] == "participants[p].log.remove(qso)LZ0DC" and qso[HISCALL] == "LZ0DU":
            #     print("yo")
            if checkExchange(qso, q):
                return True
            else:
                if qso[CALL] == "LZ0AN" and qso[HISCALL] == "LZ0FX":
                    print("yo")
                participantA.errors.append(("Exchange error", qso))
                participantA.log.remove(qso)
                participantA.invalidQSOs += 1
                return False


    participantA.errors.append(("Not in log", qso))
    participantA.log.remove(qso)
    participantA.invalidQSOs += 1
    return False


def checkTimeRules(qso, participant):
    idx = participant.log.index(qso)

    for q in participant.log[0:idx]:
        try:
            if isDupe(qso, q, 30):
                participant.errors.append(("Dupe", qso))
                participant.invalidQSOs += 1
                participant.log.remove(qso)
                return False

        except:
            participant.errors.append(("Unknown formatting", qso))
            participant.invalidQSOs += 1
            participant.log.remove(qso)
            return False

    return True


def removeQsoOutdsideTheContest(participant, startDateTime, endDateTime):

    date_format = "%Y-%m-%d %H%M"
    start = datetime.strptime(startDateTime, date_format)
    end = datetime.strptime(endDateTime, date_format)

    log = participant.log

    for i in len(participant.log):
        # convert string to actual date and time
        dt = datetime.strptime(" ".join(log[i][DATE], log[i][TIME]]), date_format)

        if participant.callsign == "LZ0AC" and log[i][HISCALL] == "LZ0AN":
            print("yo")

        if dt.timestamp() < start.timestamp() or dt.timestamp() > end.timestamp():
            participant.errors.append(("Date/Time", log[i]))
            participant.invalidQSOs += 1
            participant.log.remove(qso)


def checkLog(participants):
    """
    This will check the validity of each QSO of every participant
    :param participants:
    :type participants: dict of Participant
    :return: none
    """

    for p in participants:
        removeQsoOutdsideTheContest(participants[p], "2017-08-19 0700", "2017-08-19 1059")

    for p in participants:
        for qso in participants[p].log:

            if qso[HISCALL] not in participants: # remove QSO if the correspondent didn't sent log
                participants[p].errors.append(("Log not sent", qso))
                participants[p].invalidQSOs += 1
                participants[p].log.remove(qso)
                continue

            if not checkTimeRules(qso, participants[p]): # remove QSO violating the "30min rule" and if outside the contest
                continue

            if not crossCheck(qso, participants[p], participants[qso[HISCALL]]): # Remove QSO which do not cross-check
                continue



def main():
    participants = {}

    # Print the Name of the participant
    for filename in glob.glob("docs/Plovdiv-2017-Logove/*.*"):
        p = parseLog(filename)
        participants[p.callsign] = p

    checkLog(participants)

    for p in participants:
        print(participants[p])
        print("UBN for "+participants[p].callsign)
        for e in participants[p].errors:
            print(e)


    # print(isTimeIntervalLessThan(participants["LZ0DD"].log[0], participants["LZ0DD"].log[6], 4))
    # removeTimeRuleViolations(participants["LZ0DD"], timeinterval=30)

    # print(len(participants["LZ0DD"].log))




if __name__ == "__main__":
    main()



