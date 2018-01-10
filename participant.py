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


    def getAccuracy(self):
        """
        :return: Percenage of successful QSOs
        :rtype: float
        """
        return (self.validQsoCount() / self.totalQsoCount()) * 100.0


    def getPoints(self):
        """
        Returns the final score of the participant.
        :return: Final score.
        :rtype: int
        """
        return self.validQsoCount()*2


    def isElectronProgressStation(self):
        for q in self.log:
            if str(q.snd2).upper() == "EP":
                return True
            else:
                return False

    def getResults(self):
        """
        List of strings: "Call, Total QSO, Confirmed QSO , Points, Accuracy"
        :return:
        :rtype: list of str
        """
        return [self.callsign, self.totalQsoCount(), self.validQsoCount(), self.getPoints(), "{0:.2f}".format(self.getAccuracy())]


    def getResultsEP(self):
        """
        List of strings: "Call, Total QSO, Confirmed QSO , Points, Multipliers, Score, Accuracy"
        :return:
        :rtype: list of str
        """
        worked_ep_stations = []

        for q in self.log:
            if str(q.rcv2).lower() == "ep" and q.isValid():  # QSO with EP station
                if q.his_call not in worked_ep_stations:
                    worked_ep_stations.append(q.his_call)

        mult = len(worked_ep_stations)

        return [self.callsign, self.totalQsoCount(), self.validQsoCount(),
                self.getPoints(), mult, self.getPoints() * mult,
                self.getAccuracy()]


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