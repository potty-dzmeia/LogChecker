#!/usr/bin/env python
logfile = open("docs/Plovdiv-2016-Logove/LZ0AC.CBR", "r")
for line in logfile:
    line_split = line.split()
    print(line_split)
    # for
    # list = line_split[0], line_split[1], line_split[2], line_split[4]
    # print(list)