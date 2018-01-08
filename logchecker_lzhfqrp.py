import csv

from participant import Participant
from bs4 import UnicodeDammit
from qso import Qso
import glob
from datetime import datetime
import os
import logging
import logging.config


logging.config.fileConfig("logging.conf", disable_existing_loggers=False)
logger = logging.getLogger(__name__)
logger.setLevel(level=logging.DEBUG)


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


def parseLogs(logs_dir):
    """
    Extracts all the participants data: callsign, name etc and his log from the supplied directory

    :param filename: file that needs to be parsed
    :type filename: str
    :return:
    :rtype: Participant
    """
    participants = {}

    for filename in glob.glob(logs_dir + "*.*"):

        participant = Participant()

        logger.info("parsing log: " + filename)

        logfile = open(filename, "r", encoding=getFileEncoding(filename))

        for line in logfile:
            line_split = line.split()
            try:
                if len(line_split) == 0:
                    pass
                elif line_split[0] == "CALLSIGN:":
                    participant.callsign = line_split[1].upper()
                elif line_split[0] == "NAME:":
                    participant.name = " ".join(line_split[1:])
                elif line_split[0] == "CATEGORY:":
                    participant.category = " ".join(line_split[1:])
                elif line_split[0] == "QSO:":
                    participant.log.append(Qso(line_split))
            except:
                logger.warning("Error in line: " + line)
                pass # empty line

        if len(participant.callsign):
            participants[participant.callsign] = participant
            logger.info("Parsed log for: " + participant.callsign + "\n")
        else:
            logger.error("Couldn't parse the file: " + filename + "\n")

    return participants


def rejectQsoOutdsideTheContest(participant, startDateTime, endDateTime):

    for p in participant:
        date_format = participant[p].log[0].DATE_TIME_FORMAT # Date format used by the Qso class

        start = datetime.strptime(startDateTime, date_format)
        end = datetime.strptime(endDateTime, date_format)

        log = participant[p].log

        for qso in log:
            if qso.date_time.timestamp() < start.timestamp() or qso.date_time.timestamp() > end.timestamp():
                qso.error_code = Qso.ERROR_DATE_TIME


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
        if qso.his_call == q.his_call and isIntervalSmallerThan(qso, q, 30) and q.isValid():
            qso.error_code = Qso.ERROR_DUPE
            qso.error_info = q.toCabrillo()
            return True

    return False


def isExchangeFailed(qso1, qso2):
    """
    Check if the serials from the two qso match

    :type qso1: Qso
    :type qso2: Qso
    :return: True if the two Qso entries match
    :rtype: bool
    """
    if qso1.snd1 != qso2.rcv1 or qso1.snd2 != qso2.rcv2:
        qso1.error_code = Qso.ERROR_PARTNER_RECEIVE
        #qso2.error_code = Qso.ERROR_RECEIVE
        qso1.error_info = qso2.toCabrillo()  # store the QSO from the other log for the Error report
        #qso2.error_info = qso1.toCabrillo()  # store the QSO from this log to the other log so that they have the extra info also
        return True
    if qso2.snd1 != qso1.rcv1 or qso2.snd2 != qso1.rcv2:
        qso1.error_code = Qso.ERROR_RECEIVE
        #qso2.error_code = Qso.ERROR_PARTNER_RECEIVE
        qso1.error_info = qso2.toCabrillo()  # store the QSO from the other log for the Error report
        #qso2.error_info = qso1.toCabrillo()  # store the QSO from this log to the other log so that they have the extra info also
        return True

    return False


def isCrossCheckFailed(qso, participantA, participantB):
    """
    Checks if the "qso" is available in the "log" of the correspondent
    """
    assert(qso.his_call == participantB.log[0].call)

    for q in participantB.log:
        if qso.call == q.his_call and isIntervalSmallerThan(qso, q, 3):

            # QSO that we have found in correspondents log is marked as invalid
            # if q.isInvalid():
            #     # Store the reason for being invalid
            #     qso.error_code = q.translatePartnerError()
            #     qso.error_info = q.toCabrillo()
            #     return True
            return isExchangeFailed(qso, q)

    qso.error_code = Qso.ERROR_NOT_IN_LOG
    return True


def checkLog(participants, start_date_time, end_date_time):
    """
    This will check the validity of each QSO of every participant
    :param participants:
    :type participants: dict of Participant
    :return: none
    """
    rejectQsoOutdsideTheContest(participants, start_date_time, end_date_time)

    for p in participants:
        for qso in participants[p].log:

            if qso.isInvalid():  # Do not check in case the Qso has been rejected
                continue

            if qso.his_call not in participants:
                qso.error_code = Qso.ERROR_PARTNER_LOG_MISSING
                continue  # Correspondent didn't sent log - move to next Qso

            if isDupe(qso, participants[p]):
                continue # Violating the "30min rule" - move to next Qso

            if isCrossCheckFailed(qso, participants[p], participants[qso.his_call]):
                continue  # Not confirmed by correspondent - move to next Qso



def writeResults(participants, dir):
    """
    Writes the results in the supplied dir (this includes stuff like general results, UBN and maybe more)

    :param participants:
    :type participants: list of Participants
    :param dir: Directory where results must be written
    :rtype: str
    :return:
    """

    # Create the classification - results.csv
    # -------------------------
    list_classification = []
    for p in participants:
        list_classification.append(participants[p].getResults())

    list_classification = sorted(list_classification,
                                 key=lambda list_classification: (list_classification[3], list_classification[4]),
                                 reverse=True) # Sort by points

    # Add the rank
    for idx, entry in enumerate(list_classification):
        entry.insert(0, idx+1)

    # Print the results into a CSV file called results.csv
    filename = os.path.join(dir, "results.csv")
    with open(filename, "w+") as output:
        writer = csv.writer(output, lineterminator='\n')
        writer.writerows(list_classification)


    # Write the UBN reports
    # -------------------------
    ubn_dir = os.path.join(dir, "UBN")
    if not os.path.exists(ubn_dir):
        os.makedirs(ubn_dir) # Create UBN directory if not existing

    for p in participants:
        filename = os.path.join(ubn_dir, participants[p].callsign + ".UBN")
        ubn_file = open(filename, "w+")
        ubn_file.write(participants[p].getUbnReport())
        ubn_file.close()


def main():

    start_date = "2017-08-19 0700"     #removeQsoOutdsideTheContest(participants, "2016-08-20 0800", "2016-08-20 1159")
    end_date = "2017-08-19 1059"
    log_directory = "docs/Plovdiv-2017-Logove_v2/"


    # Parse the logs
    participants = parseLogs(log_directory)

    # Check the logs
    checkLog(participants, start_date, end_date)

    # Write the results into the "/results" dir
    results_dir = os.path.join(log_directory, "results")
    if not os.path.exists(results_dir):
        os.makedirs(results_dir)
    writeResults(participants, results_dir)



if __name__ == "__main__":
    main()
