from qso import Qso


class Participant:

    def __init__(self, callsign="", name="", category=""):
        self.callsign = callsign
        self.category = category
        self.name = name

        """:type : list of Qso"""
        self.log = [] #:type : list of Qso


    def __str__(self):

        return "Callsign: "+self.callsign+" Total: "+str(self.totalQsoCount())+" Conf: "+str(self.validQsoCount())


    def totalQsoCount(self):
        return len(self.log)


    def validQsoCount(self):
        """

        :return: Number of valid Qsos
        :rtype: int
        """
        i = 0
        for q in self.log:
            if q.error_code == Qso.NO_ERROR:
                i += 1
        return i


    def invalidQsoCount(self):
        """

        :return: Number of invalid Qsos
        :rtype: int
        """
        i = 0
        for q in self.log:
            if q.error_code != Qso.NO_ERROR:
                i += 1
        return i


    def printUbnReport(self):
        print("UBN for "+self.callsign)

        for q in self.log:
            if q.error_code != Qso.NO_ERROR:
                print(q.errorCodeToString(q.error_code)+" -------------> "+str(q))


    def getUbnReport(self):
        ubn = ""
        ubn += "UBN for: "+self.callsign+"\n"
        ubn += "Name: "+self.name+"\n"
        ubn += "\n"
        ubn += "--------------------------------------------------------------------------------"+"\n"
        ubn += "Total QSOs: "+str(self.totalQsoCount())+"\n"
        ubn += "Confirmed QSOs: "+str(self.validQsoCount())+"\n"
        ubn += "--------------------------------------------------------------------------------"+"\n"
        ubn += "\n"
        for q in self.log:
            if q.error_code != Qso.NO_ERROR:
                ubn += q.errorCodeToString(q.error_code) + ":\n"
                ubn += str(q) + "\n"
                if len(q.error_info) > 0:
                    ubn += q.error_info
                    ubn += "\n"
                ubn += "\n"

        return ubn