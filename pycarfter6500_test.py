# -*- coding: utf-8 -*-
"""
Created on Fri Jun 12 15:22:05 2020

@author: 52994
"""

import pycrafter6500
import usb

#usb.core.show_devices()
gui = pycrafter6500.PycrafterGUI()
#dlp = pycrafter6500.DMD()
dlp = gui.dlp
sq = gui.sequence_data