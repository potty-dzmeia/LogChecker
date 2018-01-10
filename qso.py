from datetime import datetime


class Qso:

    MODE = 2
    FREQ = 1
    DATE = 3
    TIME = 4
    CALL = 5
    SND1 = 6
    SND2 = 7
    HIS_CALL = 8
    RCV1 = 9
    RCV2 = 10

    DATE_TIME_FORMAT = "%Y-%m-%d %H%M"
    DATE_FORMAT = "%Y-%m-%d"
    TIME_FORMAT = "%H%M"

    # Error codes
    NO_ERROR = 0
    ERROR_DUPE = -1
    ERROR_NOT_IN_LOG = -2
    ERROR_DATE_TIME = - 3
    ERROR_RECEIVE = -4
    ERROR_PARTNER_LOG_MISSING = -5
    ERROR_PARTNER_RECEIVE = -6
    ERROR_PARTNER_DATE_TIME = -7
    ERROR_PARTNER_DUPE = -8
    ERROR_PARTNER_QSO_ALREADY_CHECKED_AND_FAILED = -9
    ERROR_UNKNOWN_LINE_FORMATTING = -10



    def __init__(self, qso_list):
        """
        Parse list of the type QSO: 3531 CW 2017-08-18 1006 LZ0AC  130 199  LZ0DY  226 133

        :param qso_list:
        """

        self.call = qso_list[self.CALL]
        self.date_time = datetime.strptime(" ".join([qso_list[self.DATE], qso_list[self.TIME]]), self.DATE_TIME_FORMAT)
        self.mode = qso_list[self.MODE]
        self.freq = int(qso_list[self.FREQ])
        self.snd1 = qso_list[self.SND1]
        self.snd2 = qso_list[self.SND2]
        self.his_call = qso_list[self.HIS_CALL]
        self.rcv1 = qso_list[self.RCV1]
        self.rcv2 = qso_list[self.RCV2]

        self.error_code = self.NO_ERROR  # holds value identifying the type of error that has been found by log check
        self.error_info = "" # will hold additional info concerning errors (e.g. the QSO from the other log)

    def __repr__(self):
        return self.toCabrillo()


    def isInvalid(self):
        """
        Checks if the QSO has been marked as invalid during log checking (i.e. self.error_code != self.NO_ERROR)
        :return:
        :rtype: bool
        """
        if self.error_code == self.NO_ERROR:
            return False
        return True


    def isValid(self):
        """
        Checks if the QSO has not been marked as invalid during log checking (i.e. self.error_code == self.NO_ERROR)
        :return:
        :rtype: bool
        """
        if self.error_code == self.NO_ERROR:
            return True
        return False


    def toCabrillo(self):
        """
        Returns the QSO in Cabrillo representation.
        E.g.: QSO:  3531 CW 2017-08-19 0701 LZ0FJ         001 000       LZ0DY         004 003
        :return:
        :rtype: str
        """
        return "QSO:" + \
               "{:>6}".format(str(self.freq)) + \
               "{:>3}".format(self.mode) + \
               "{:>11}".format(self.date_time.date().isoformat()) + \
               "{:>5}".format(self.date_time.time().strftime(self.TIME_FORMAT)) + " " \
               "{:<13}".format(self.call) + \
               "{:<5}".format(str(self.snd1).zfill(3)) + \
               "{:<10}".format(str(self.snd2).zfill(3)) + \
               "{:<13}".format(self.his_call) + \
               "{:<5}".format(str(self.rcv1).zfill(3)) + \
               "{:<4}".format(str(self.rcv2).zfill(3))


    def isWithinDateTime(self, start_date_time, end_date_time):
        """
        Checks if the Qso is within the specified time interval
        :param start_date_time:
        :type start_date_time: datetime
        :param end_date_time:
        :type end_date_time: datetime
        :return:
        """
        if self.date_time.timestamp() < start_date_time.timestamp() or \
                self.date_time.timestamp() > end_date_time.timestamp():
            return True
        else:
            return False


    def errorCodeToString(self, error_code):
        """
        Translates error code to string
        :param self:
        :param error_code:
        :type error_code: int
        :return: String representing the error code
        :rtype: str
        """
        if error_code == self.NO_ERROR:
            return "OK"
        elif error_code == self.ERROR_DUPE:
            return "ERROR_DUPE"
        elif error_code == self.ERROR_NOT_IN_LOG:
            return "ERROR_NOT_IN_LOG"
        elif error_code == self.ERROR_DATE_TIME:
            return "ERROR_DATE_TIME"
        elif error_code == self.ERROR_RECEIVE:
            return "ERROR_RECEIVE"
        elif error_code == self.ERROR_PARTNER_LOG_MISSING:
            return "ERROR_PARTNER_LOG_MISSING"
        elif error_code == self.ERROR_PARTNER_RECEIVE:
            return "ERROR_PARTNER_RECEIVE"
        elif error_code == self.ERROR_PARTNER_DATE_TIME:
            return "ERROR_PARTNER_DATE_TIME"
        elif error_code == self.ERROR_PARTNER_DUPE:
            return "ERROR_PARTNER_DUPE"
        elif error_code == self.ERROR_UNKNOWN_LINE_FORMATTING:
            return "ERROR_UNKNOWN_LINE_FORMATTING"
        else:
            return "UNKNOWN ERROR"


    def translatePartnerError(self):
        """
        Translate an error from the correspondent's log into one that that can be written into the log currently being
        checked.

        e.g.: The correspondent has not not followed the 30min rule and his QSO is marked with ERROR_DUPE. In order
        to notify the person of the current log being check we would like to copy this error. So we change it into
        ERROR_PARTNER_DUPE and store it.

        :return: Returns error of the type ERROR_PARTNER_.....
        :rtype: str
        """
        if self.error_code == self.ERROR_DUPE:
            return self.ERROR_PARTNER_DUPE
        elif self.error_code == self.ERROR_NOT_IN_LOG:
            return self.ERROR_PARTNER_QSO_ALREADY_CHECKED_AND_FAILED
        elif self.error_code == self.ERROR_DATE_TIME:
            return self.ERROR_PARTNER_DATE_TIME
        elif self.error_code == self.ERROR_RECEIVE:
            return self.ERROR_PARTNER_QSO_ALREADY_CHECKED_AND_FAILED