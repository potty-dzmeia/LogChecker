from participant import Participant
from bs4 import UnicodeDammit
from qso import Qso
import glob
from datetime import datetime


def getFileEncoding(filename):
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

    logfile = open(filename, "r", encoding=getFileEncoding(filename))

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
                participant.log.append(Qso(line_split))
        except:
            pass # empty line

    print("parsed log: "+participant.callsign)
    return participant




def removeQsoOutdsideTheContest(participant, startDateTime, endDateTime):

    for p in participant:
        date_format = participant[p].log[0].DATE_TIME_FORMAT # Date format used by the Qso class

        start = datetime.strptime(startDateTime, date_format)
        end = datetime.strptime(endDateTime, date_format)

        log = participant[p].log

        for qso in log:
            if qso.date_time.timestamp() < start.timestamp() or qso.date_time.timestamp() > end.timestamp():
                qso.error_code = Qso.ERROR_TIME_DATE


def isIntervalSmallerThan(qso1, qso2, timeinterval):
    """
    Checks if the time interval between the two QSOs is less then delta

    :type qso1: Qso
    :type qso2: Qsolist
    :param delta: Time interval in miutes
    :type delta: int
    :rtype: bool
    """

    if qso1.date_time.timestamp() > qso2.date_time.timestamp():
        diff = qso1.date_time - qso2.date_time
    else:
        diff = qso2.date_time - qso1.date_time

    if diff.total_seconds() / 60 < timeinterval:
        return True
    else:
        return False


def isDupe(qso, participant):
    """
    Checks if the QSO did not meet the "30min rule"
    :type qso: Qso
    :type participant: Participant
    :rtype: bool
    """
    idx = participant.log.index(qso)

    for q in participant.log[0:idx]:
        if qso.his_call == q.his_call and isIntervalSmallerThan(qso, q, 30):
            qso.error_code = Qso.ERROR_DUPE
            return False

    return True


def checkExchange(qso1, qso2):
    """
    Check if the serials from the two qso match

    :type qso1: Qso
    :type qso2: Qso
    :return: True if the two Qso entries match
    :rtype: bool
    """
    if qso1.snd1 != qso2.rcv1 or qso1.snd2 != qso2.rcv2:
        qso1.error_code = Qso.ERROR_PARTNER_RECEIVE
        qso2.error_code = Qso.ERROR_RECEIVE
        return False
    if qso2.snd1 != qso1.rcv1 or qso2.snd2 != qso1.rcv2:
        qso1.error_code = Qso.ERROR_RECEIVE
        qso2.error_code = Qso.ERROR_PARTNER_RECEIVE
        return False


def crossCheck(qso, participantA, participantB):
    """
    Checks if the "qso" is available in the "log" of the correspondent
    """
    assert(qso.his_call == participantB.log[0].call)

    for q in participantB.log:
        if qso.call == q.his_call and isIntervalSmallerThan(qso, q, 3):

            return checkExchange(qso, q)

    qso.error_code = Qso.ERROR_NOT_IN_LOG
    return False


def checkLog(participants):
    """
    This will check the validity of each QSO of every participant
    :param participants:
    :type participants: dict of Participant
    :return: none
    """
    removeQsoOutdsideTheContest(participants, "2017-08-19 0700", "2017-08-19 1059")
    #removeQsoOutdsideTheContest(participants, "2016-08-20 0800", "2016-08-20 1159")
    for p in participants:
        for qso in participants[p].log:

            if qso.error_code != Qso.NO_ERROR:  # Do not check in case the Qso has been rejected
                continue

            if qso.his_call not in participants: # find if the correspondent didn't sent log
                qso.error_code = Qso.ERROR_PARTNER_LOG_MISSING
                continue

            if not isDupe(qso, participants[p]): # find if violating the "30min rule"
                continue

            if not crossCheck(qso, participants[p], participants[qso.his_call]): # find if the correspondent confirms it
                continue

def writeUbnReportToFile(participant):
    filename = "docs/Plovdiv-2017-UBN/"+participant.callsign+".UBN"
    ubn_file = open(filename, "w+")

    ubn_file.write(participant.getUbnReport())

    ubn_file.close()


def main():
    participants = {}

    # Print the Name of the participant
    for filename in glob.glob("docs/Plovdiv-2017-Logove/*.*"):
        p = parseLog(filename)
        participants[p.callsign] = p


    checkLog(participants)
    #
    for p in participants:

        print(participants[p])
        writeUbnReportToFile(participants[p])
    #     print("UBN for "+participants[p].callsign)
    #     for e in participants[p].errors:
    #         print(e)


if __name__ == "__main__":
    main()
