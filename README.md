# LogChecker
Log checker for LZ contests that use the [serial]+[first3digitsfr

supports:
- lzhfqrp
- Electron progress
- and others...


Example usage:
python logchecker_lzhfqrp.py --start="2016-08-20 0800" --end="2016-08-20 1159" --dir="C:\Development\LogChecker\docs\Plovdiv-2016-Logove" --qso_repeat=30 --crosscheck_diff=3


Example usage for ElectronProgress contest:
python logchecker_lzhfqrp.py --start="2016-12-26 0700" --end="2016-12-26 0859" --dir="C:\Development\LogChecker\docs\EP-2016" --qso_repeat=30 --crosscheck_diff=3 --ep=True