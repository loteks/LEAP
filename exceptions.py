#! /usr/bin/env python

##############################################################################
#
#   LEAP - Library for Evolutionary Algorithms in Python
#   Copyright (C) 2004  Jeffrey K. Bassett
#
#   This program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; either version 2 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program; if not, write to the Free Software
#   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
##############################################################################

# Python 2 & 3 compatibility
from __future__ import print_function


#############################################################################
#
# class Error
#
#############################################################################
class LEAPerror(Exception):
    "LEAP exception base class."
    pass


#############################################################################
#
# class OperatorError
#
#############################################################################
class OperatorError(LEAPerror):
    "For errors in the operators or the pipeline."
    pass


#############################################################################
#
# unit_test
#
#############################################################################
def unit_test():
    passed = False

    print("There are no tests currently.")
    #if passed:
    #    print("Passed")
    #else:
    #    print("FAILED")


if __name__ == '__main__':
    unit_test()
