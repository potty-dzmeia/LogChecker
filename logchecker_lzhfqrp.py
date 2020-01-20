import csv

from participant import Participant
from qso import Qso
import glob
from datetime import datetime
import os
import logging
import logging.config
import my_utils
import argparse
import re
import sys

logging.config.fileConfig("logging.conf", disable_existing_loggers=False)
logger = logging.getLogger(__name__)
logger.setLevel(level=logging.INFO)


def parseLogs(logs_dir):
    """
    Reads all the logs in the supplied directory and parses the data into dictionary that is returned

    :param logs_dir: Directory where the log files are located
    :return: Dictonary of particpants. {callsign, participant object}
    :rtype: dict
    """
    participants = {}

    for filename in glob.glob(os.path.join(logs_dir, "*.*")):

        participant = Participant()

        logger.info("parsing log: " + filename)
        logfile = open(filename, "r", encoding=my_utils.getFileEncoding(filename))


        try:
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
                    logger.warning("Error in line (will be ignored): " + line)
                    pass # empty line
        except Exception as e:
            logger.warning("Error in file (will be ignored): " + filename)
            logger.warning("Error: " + str(e))
            pass

        if len(participant.callsign):
            participants[participant.callsign] = participant
            logger.info("Parsed log for: " + participant.callsign + "\n")
        else:
            logger.error("Couldn't parse the file: " + filename + "\n")

    return participants


def rejectQsoOutdsideTheContest(participants, start_date_time, end_date_time):

    for p in participants:
        print(participants[p].callsign)
        if not participants[p].log:
            continue
        date_format = participants[p].log[0].DATE_TIME_FORMAT # Date format used by the Qso class

        start = datetime.strptime(start_date_time, date_format)
        end = datetime.strptime(end_date_time, date_format)

        log = participants[p].log

        for qso in log:
            if qso.date_time.timestamp() < start.timestamp() or qso.date_time.timestamp() > end.timestamp():
                qso.error_code = Qso.ERROR_DATE_TIME


def isIntervalSmallerThan(qso1, qso2, time_delta):
    """
    Checks if the time interval between the two QSOs is less then delta

    :type qso1: Qso
    :type qso2: Qsolist
    :param time_delta: Time interval in miutes
    :type time_delta: int
    :rtype: bool
    """

    if qso1.date_time.timestamp() > qso2.date_time.timestamp():
        diff = qso1.date_time - qso2.date_time
    else:
        diff = qso2.date_time - qso1.date_time

    if diff.total_seconds() / 60 < time_delta:
        return True
    else:
        return False


def isDupe(qso, participant, qso_repeat_period):
    """
    Checks if the QSO did not meet the "30min rule"

    :param qso: Qso that is to be checked
    :type qso: Qso
    :param participant: The participant
    :type participant: Participant
    :param qso_repeat_period: The allowed period after which a Qso can be made again
    :type qso_repeat_period: int
    :rtype: bool
    """
    idx = participant.log.index(qso)

    for q in participant.log[0:idx]:
        if q.isValid() \
                and qso.his_call == q.his_call \
                and isIntervalSmallerThan(qso, q, qso_repeat_period) \
                and qso.mode == q.mode:  # There is separate 30min rule for each mode.
            qso.error_code = Qso.ERROR_DUPE # Violating the "30min rule"
            qso.error_info = q.toCabrillo()
            return True

    return False


def isExchangeMatching(qso1, qso2):
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


def doCrossCheck(qso, participant_a, participant_b, qso_time_difference):
    """
    Check if the qso of participantA is available in the log of participantB
    :param qso_time_difference: cross-check allowed difference for a QSO in the two logs [in minutes]
    :type qso_time_difference: int
    :param qso: qso from the log of participantA that we would like to check with the participantB log
    :type qso: Qso
    :param participant_a: Log of participantA which. The supplied "qso" is part of the participantA log
    :param participant_b: Where we will checking if the qso is valid
    :return: True if the qso was found inside the log of participantB
    :rtype: bool
    """
    assert(qso.his_call == participant_b.callsign)

    for q in participant_b.log:
        if qso.call == q.his_call and isIntervalSmallerThan(qso, q, qso_time_difference+1):

            # The rule below makes sense but it is not implemented in the official BFRA software.
            # ------------------
            # QSO that we have found in correspondents log is marked as invalid
            # if q.isInvalid():
            #     # Store the reason for being invalid
            #     qso.error_code = q.translatePartnerError()
            #     qso.error_info = q.toCabrillo()
            #     return True
            # ------------------

            if not isExchangeMatching(qso, q):
                continue # We found a QSO with a wrong exchange - but we will continue to search for a valid one
            else:
                qso.error_code = Qso.NO_ERROR # Valid contact was found
                return True

    if qso.error_code == Qso.NO_ERROR:
        qso.error_code = Qso.ERROR_NOT_IN_LOG  # We didn't find any QSO with participantA in the log the participantB
    return False


def checkLog(participants, start_date_time, end_date_time, qso_repeat_period=30, qso_time_difference=3):
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


def writeResults(participants, to_dir):
    """
    Writes the results in the supplied dir (this includes stuff like general results, UBN and maybe more)

    :param ep: If this is an Electron Progress contests (then we have to calculate also multipliers)
    :type ep: bool
    :param participants:
    :type participants: list of Participants
    :param to_dir: Directory where results must be written
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
    filename = os.path.join(to_dir, "results.csv")
    with open(filename, "w+", encoding="utf-8") as output:
        writer = csv.writer(output, lineterminator='\n')
        writer.writerows(list_classification)

    # Write the UBN reports
    # -----------------------------------------
    ubn_dir = os.path.join(to_dir, "UBN")
    if not os.path.exists(ubn_dir):
        os.makedirs(ubn_dir) # Create UBN directory if not existing

    for p in participants:
        filename = os.path.join(ubn_dir, participants[p].callsign.replace("/", "_") + ".UBN")
        ubn_file = open(filename, "w+", encoding="utf-8")
        ubn_file.write(participants[p].getUbnReport())
        ubn_file.close()


def writeResultsElectronProgress(participants, to_dir):
    """
    Writes the results in the supplied dir (this includes stuff like general results, UBN and maybe more)

    :param participants:
    :type participants: list of Participants
    :param to_dir: Directory where results must be written
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
    filename = os.path.join(to_dir, "results_A.csv")
    with open(filename, "w+", encoding="utf-8") as output:
        writer = csv.writer(output, lineterminator='\n')
        writer.writerows(list_classification_A)

    filename = os.path.join(to_dir, "results_B.csv")
    with open(filename, "w+", encoding="utf-8") as output:
        writer = csv.writer(output, lineterminator='\n')
        writer.writerows(list_classification_B)

    # Write the UBN reports
    # -------------------------
    ubn_dir = os.path.join(to_dir, "UBN")
    if not os.path.exists(ubn_dir):
        os.makedirs(ubn_dir)  # Create UBN directory if not existing

    for p in participants:
        filename = os.path.join(ubn_dir, participants[p].callsign.replace("/", "_") + ".UBN")
        ubn_file = open(filename, "w+", encoding="utf-8")
        ubn_file.write(participants[p].getUbnReport())
        ubn_file.close()


def is_valid_date_time_format(date_time_string):
    """
    Validate that date_time_string has the following format "yyyy-mm-dd hhmm" (See Qso.DATE_TIME_FORMAT)

    :param date_time_string:
    :type date_time_string: str
    :return: True if the string is formatted properly.
    :rtype: bool
    """

    date_pattern = re.compile(r'\d{4}-\d{2}-\d{2} \d{2}\d{2}')
    if date_pattern.match(date_time_string):
        return True
    else:
        return False


def main(start_date, end_date, log_directory, qso_repeat_period_in_mins=30, qso_time_difference_in_mins=3, ep=0):
    """

    :param start_date: Date and time when the contest begins. Format is specified in qso.DATE_TIME_FORMAT (Example: "2016-12-26 0700")
    :type start_date: str
    :param end_date: Date and time when the contest ends. Format is specified in qso.DATE_TIME_FORMAT (Example: "2016-12-26 0700")
    :type end_date: str
    :param log_directory: Full path to the directory containing the cabrilo files
    :type log_directory: str
    :param qso_repeat_period_in_mins: Period (in minutes) after which the QSO with the same station is allowed
    :type qso_repeat_period_in_mins: int
    :param qso_time_difference_in_mins: Allowed cross-check difference (in minutes) in two logs for a given QSO
    :type qso_time_difference_in_mins: int
    :param ep: If this is an "ElctronProgress" contest
    :type ep: bool
    :return:
    """

    if not is_valid_date_time_format(start_date):
        raise ValueError("Incorrect --start param format, should be: yyyy-mm-dd hhmm")
    if not is_valid_date_time_format(end_date):
        raise ValueError("Incorrect --end param format, should be: yyyy-mm-dd hhmm")

    # Parse the logs
    participants = parseLogs(log_directory)

    # Check the logs
    checkLog(participants, start_date, end_date, qso_repeat_period_in_mins, qso_time_difference_in_mins)

    # Write the results into the "/results" dir
    results_dir = os.path.join(log_directory, "results")
    if not os.path.exists(results_dir):
        os.makedirs(results_dir)

    if not ep:  # Normal contest
        writeResults(participants, results_dir)
    else:  # Electron Progress contest
        writeResultsElectronProgress(participants, results_dir)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Log checking program for LZ contests. Written by LZ1ABC.')
    parser.add_argument("--start", type=str, required=True, help="Contest start time. Example: --start=\"2016-08-20 0800\"")
    parser.add_argument("--end", type=str, required=True, help="Contest end time. Example: --end=\"2016-08-20 1159\"")
    parser.add_argument("--dir", type=str, required=True, help="Full path to the directory with the cabrilo logs. Example: --dir=\"C:\Plovdiv-2016-Logove\"")
    parser.add_argument("--qso_repeat", type=int, default=30,  required=False, help="QSO repeat interval in minutes. Default is 30mins. Example: --qso_repeat=20")
    parser.add_argument("--crosscheck_diff", type=int, default=3, required=False, help="Allowed cross-check difference (in minutes) for QSO. Default is 3mins. Example: --crosscheck_diff=4")
    parser.add_argument("--ep", type=bool, default=False, required=False, help="Se to True if this is an ElectronProgress contest. Default is Flase. Example: --ep=True");
    args = parser.parse_args()
    argsdict = vars(args)

    main(argsdict["start"], argsdict["end"], argsdict["dir"], argsdict["qso_repeat"], argsdict["crosscheck_diff"], argsdict["ep"])

    # is_ep = False
    # start = "2016-08-20 0800"
    # end = "2016-08-20 1159"
    # log_dir = "C:\Development\LogChecker\docs\Plovdiv-2016-Logove"
    # qso_repeat_after = 30  # in minutes
    # qso_crosscheck_time_difference = 3  # cross-check allowed difference in minutes between two QSOs
    # main(start, end, log_dir, qso_repeat_after, qso_crosscheck_time_difference, is_ep)
