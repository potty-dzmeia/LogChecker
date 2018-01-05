from datetime import datetime




class Qso:

    MODE = 2
    FREQ = 1
    DATE = 3
    TIME = 4
    CALL = 5
    SND1 = 6
    SND2 = 7
    HISCALL = 8
    RCV1 = 9
    RCV2 = 10

    DATE_TIME_FORMAT = "%Y-%m-%d %H%M"

    # Error codes
    NO_ERROR = 0
    ERROR_DUPE = -1
    ERROR_NOT_IN_LOG = -2
    ERROR_TIME_DATE = - 3
    ERROR_RECEIVE = -4
    ERROR_PARTNER_LOG_MISSING = -5
    ERROR_PARTNER_RECEIVE = -6
    ERROR_PARTNER_DATETIME = -7
    ERROR_PARTNER_DUPE = -8
    ERROR_UNKNOWN_FORMATTING = -9


    def __init__(self, qso_list):
        """
        Parse list of the type QSO: 3531 CW 2017-08-18 1006 LZ0AC  130 199  LZ0DY  226 133

        :param qso_list:
        """

        self.call = qso_list[self.CALL]
        self.date_time = datetime.strptime(" ".join([qso_list[self.DATE], qso_list[self.TIME]]), self.DATE_TIME_FORMAT)
        self.mode = qso_list[self.MODE]
        self.snd1 = int(qso_list[self.SND1])
        self.snd2 = int(qso_list[self.SND2])
        self.his_call = qso_list[self.HISCALL]
        self.rcv1 = int(qso_list[self.RCV1])
        self.rcv2 = int(qso_list[self.RCV2])

        self.is_valid = True  # False if during log check the QSO is not accepted
        self.error_code = self.NO_ERROR  # holds value identifying the type of error that has been found by log check


    def __repr__(self):
        return "QSO: "+self.mode+" "+self.mode+" "+self.date_time.date().isoformat()+" "+ \
               self.date_time.time().isoformat()+" "+self.call+"         "+str(self.rcv1).zfill(3)+" "+str(self.rcv2).zfill(3)+\
               "       "+self.his_call+"         "+str(self.snd1).zfill(3)+" "+str(self.snd2).zfill(3)


    def isWithinDateTime(self, start_date_time, end_date_time):
        """

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
        elif error_code == self.ERROR_TIME_DATE:
            return "ERROR_TIME_DATE"
        elif error_code == self.ERROR_RECEIVE:
            return "ERROR_RECEIVE"
        elif error_code == self.ERROR_PARTNER_LOG_MISSING:
            return "ERROR_PARTNER_LOG_MISSING"
        elif error_code == self.ERROR_PARTNER_RECEIVE:
            return "ERROR_PARTNER_RECEIVE"
        elif error_code == self.ERROR_PARTNER_DATETIME:
            return "ERROR_PARTNER_DATETIME"
        elif error_code == self.ERROR_PARTNER_DUPE:
            return "ERROR_PARTNER_DUPE"
        elif error_code == self.ERROR_UNKNOWN_FORMATTING:
            return "ERROR_UNKNOWN_FORMATTING"
        else:
            return "UNKNOWN ERROR"
