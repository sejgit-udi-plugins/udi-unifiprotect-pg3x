#!/usr/bin/env python3
"""UniFi Protect NodeServer for Polyglot V3 (TaHoma-style layout)."""

import udi_interface

from nodes import Controller

VERSION = '1.1.0'

if __name__ == '__main__':
    polyglot = udi_interface.Interface([])
    polyglot.start(VERSION)
    polyglot.updateProfile()
    Controller(polyglot, 'controller', 'controller', 'UniFi Protect')
    polyglot.runForever()
