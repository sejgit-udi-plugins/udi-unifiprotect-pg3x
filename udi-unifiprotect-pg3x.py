#!/usr/bin/env python3
"""UniFi Protect NodeServer for Polyglot V3 on EISY/Polisy.

UniFi Protect cameras as motion and smart detection sensors for ISY.

Version history: see git log.
"""

import os
import sys
from pathlib import Path

os.chdir(Path(__file__).resolve().parent)

import udi_interface

from nodes import Controller

VERSION = "1.1.0"

if __name__ == "__main__":
    polyglot = None
    try:
        polyglot = udi_interface.Interface([])
        polyglot.start(VERSION)
        Controller(polyglot, "controller", "controller", "UniFi Protect")
        polyglot.runForever()
    except (KeyboardInterrupt, SystemExit):
        udi_interface.LOGGER.warning("Received interrupt or exit...")
        if polyglot is not None:
            polyglot.stop()
    except Exception:
        udi_interface.LOGGER.error("Fatal error starting plugin", exc_info=True)
    sys.exit(0)
