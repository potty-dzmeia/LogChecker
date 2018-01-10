import csv

from participant import Participant
from qso import Qso
import glob
from datetime import datetime
import os
import logging
import logging.config
import my_utils

logging.config.fileConfig("logging.conf", disable_existing_loggers=False)
logger = logging.getLogger(__name__)
logger.setLevel(level=logging.DEBUG)





def parseLogs(logs_dir):
    """
    Extracts all the participants data: callsign, name etc and his log from the supplied directory

    :param filename: file that needs to be parsed
    :type filename: str
    :return:
    :rtype: Participant
    """
    participants = {}

    for filename in glob.glob(os.path.join(logs_dir, "*.*")):

        participant = Participant()

        logger.info("parsing log: " + filename)

        logfile = open(filename, "r", encoding=my_utils.getFileEncoding(filename))

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


def isDupe(qso, participant, qso_repeat_period):
    """
    Checks if the QSO did not meet the "30min rule"

    :type qso: Qso
    :type participant: Participant
    :rtype: bool
    """
    idx = participant.log.index(qso)

    for q in participant.log[0:idx]:
        if qso.his_call == q.his_call and isIntervalSmallerThan(qso, q, qso_repeat_period) and q.isValid():
            qso.error_code = Qso.ERROR_DUPE
            qso.error_info = q.toCabrillo()  # Violating the "30min rule" - move to next Qso
            return True

    return False


def isExchangeCorrect(qso1, qso2):
    """
    Check if the serials from the two qso match

    :type qso1: Qso
    :type qso2: Qso
    :return: True if the two Qso entries match
    :rtype: bool
    """
    if qso1.snd1 != qso2.rcv1 or qso1.snd2 != qso2.rcv2:
        qso1.error_code = Qso.ERROR_PARTNER_RECEIVE
        qso1.error_info = qso2.toCabrillo()  # store the QSO from the other log for the Error report

        return False
    if qso2.snd1 != qso1.rcv1 or qso2.snd2 != qso1.rcv2:
        qso1.error_code = Qso.ERROR_RECEIVE
        qso1.error_info = qso2.toCabrillo()  # store the QSO from the other log for the Error report
        return False

    return True


def doCrossCheck(qso, participantA, participantB, qso_time_difference):
    """
    Check if the qso of participantA is available in the log of participantB
    :param qso_time_difference: cross-check allowed difference in minutes between two QSOs
    :type qso_time_difference: int
    :param qso: qso from the log of participantA that we would like to check with the participantB log
    :type qso: Qso
    :param participantA: Log of participantA which. The supplied "qso" is part of the participantA log
    :param participantB: Where we will checking if the qso is valid
    :return: True if the qso was found inside the log of participantB
    :rtype: bool
    """
    assert(qso.his_call == participantB.log[0].call)

    for q in participantB.log:
        if qso.call == q.his_call and isIntervalSmallerThan(qso, q, qso_time_difference):

            # QSO that we have found in correspondents log is marked as invalid
            # if q.isInvalid():
            #     # Store the reason for being invalid
            #     qso.error_code = q.translatePartnerError()
            #     qso.error_info = q.toCabrillo()
            #     return True
            if not isExchangeCorrect(qso, q):
                continue # We found a QSO with a wrong exchange - but we will continue to search for a valid one
            else:
                qso.error_code = Qso.NO_ERROR # Valid contact was found
                return True

    if qso.error_code == Qso.NO_ERROR:
        qso.error_code = Qso.ERROR_NOT_IN_LOG  # We didn't find any QSO with participantA in the log the participantB
    return False


def checkLog(participants, start_date_time, end_date_time, qso_repeat_period = 30, qso_time_difference=3):
    """
    This will check the validity of each QSO of every participant
    :param start_date_time: contest start time
    :param end_date_time: contest end time
    :param qso_time_difference: cross-check allowed difference in minutes between two QSOs
    :type qso_time_difference: int
    :param qso_repeat_period: period after which the QSO with the same station is allowed
    :type qso_repeat_period: int
    :param participants:
    :type participants: dict of Participant
    :return: none
    """
    rejectQsoOutdsideTheContest(participants, start_date_time, end_date_time)

    for p in participants:
        for qso in participants[p].log:

            if qso.isInvalid():
                continue # Stops verification in case the Qso has been rejected

            elif qso.his_call not in participants:
                qso.error_code = Qso.ERROR_PARTNER_LOG_MISSING # Missing log for this corresponded  - move to next Qso

            elif isDupe(qso, participants[p], qso_repeat_period):
                pass

            else:
                doCrossCheck(qso, participants[p], participants[qso.his_call], qso_time_difference)



def writeResults(participants, dir):
    """
    Writes the results in the supplied dir (this includes stuff like general results, UBN and maybe more)

    :param ep: If this is an Electron Progress contests (then we have to calculate also multipliers)
    :type ep: bool
    :param participants:
    :type participants: list of Participants
    :param dir: Directory where results must be written
    :rtype: str
    :return:
    """

    # Create the classification - results.csv
    # -----------------------------------------
    list_classification = []

    for p in participants:
        list_classification.append(participants[p].getResults())

    list_classification = sorted(list_classification,
                                 key=lambda list_classification: (list_classification[3], list_classification[4]),
                                 reverse=True)  # Sort by points

    # Add the rank
    for idx, entry in enumerate(list_classification):
        entry.insert(0, idx+1)

    # Print the results into a CSV file called results.csv
    filename = os.path.join(dir, "results.csv")
    with open(filename, "w+") as output:
        writer = csv.writer(output, lineterminator='\n')
        writer.writerows(list_classification)


    # Write the UBN reports
    # -----------------------------------------
    ubn_dir = os.path.join(dir, "UBN")
    if not os.path.exists(ubn_dir):
        os.makedirs(ubn_dir) # Create UBN directory if not existing

    for p in participants:
        filename = os.path.join(ubn_dir, participants[p].callsign.replace("/", "_") + ".UBN")
        ubn_file = open(filename, "w+")
        ubn_file.write(participants[p].getUbnReport())
        ubn_file.close()



def writeResultsElectronProgress(participants, dir):
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
    list_classification_A = []
    list_classification_B = []


    for p in participants:
        if participants[p].isElectronProgressStation():
            list_classification_A.append(participants[p].getResultsEP())
        else:
            list_classification_B.append(participants[p].getResultsEP())

        list_classification_A = sorted(list_classification_A,
                                       key=lambda list_classification_A: (list_classification_A[5], list_classification_A[6]),
                                       reverse=True)  # Sort by score and then by Accuracy

        list_classification_B = sorted(list_classification_B,
                                       key=lambda list_classification_B: (
                                       list_classification_B[5], list_classification_B[6]),
                                       reverse=True)  # Sort by score and then by Accuracy

    # Add the rank
    for idx, entry in enumerate(list_classification_A):
        entry.insert(0, idx+1)
    for idx, entry in enumerate(list_classification_B):
        entry.insert(0, idx+1)

    # Print the results into a CSV file called results.csv
    filename = os.path.join(dir, "results_A.csv")
    with open(filename, "w+") as output:
        writer = csv.writer(output, lineterminator='\n')
        writer.writerows(list_classification_A)

    filename = os.path.join(dir, "results_B.csv")
    with open(filename, "w+") as output:
        writer = csv.writer(output, lineterminator='\n')
        writer.writerows(list_classification_B)


    # Write the UBN reports
    # -------------------------
    ubn_dir = os.path.join(dir, "UBN")
    if not os.path.exists(ubn_dir):
        os.makedirs(ubn_dir) # Create UBN directory if not existing

    for p in participants:
        filename = os.path.join(ubn_dir, participants[p].callsign.replace("/", "_") + ".UBN")
        ubn_file = open(filename, "w+")
        ubn_file.write(participants[p].getUbnReport())
        ubn_file.close()


def main():

    start_date = "2016-12-26 0700"     #removeQsoOutdsideTheContest(participants, "2016-08-20 0800", "2016-08-20 1159")
    end_date = "2016-12-26 0859"
    log_directory = os.path.join("docs", "EP-2016")
    qso_repeat_period = 30  #in minutes
    qso_time_difference = 3  # cross-check allowed difference in minutes between two QSOs
    ep = True

    # Parse the logs
    participants = parseLogs(log_directory)

    # Check the logs
    checkLog(participants, start_date, end_date, qso_repeat_period, qso_time_difference)

    # Write the results into the "/results" dir
    results_dir = os.path.join(log_directory, "results")
    if not os.path.exists(results_dir):
        os.makedirs(results_dir)


    if not ep:  # Normal contest
        writeResults(participants, results_dir)
    else:  # Electron Progress contest
        writeResultsElectronProgress(participants, results_dir)



if __name__ == "__main__":
    main()
