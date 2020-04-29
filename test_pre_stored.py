# -*- coding: utf-8 -*-
"""
Created on Wed Apr 29 15:53:58 2020

@author: hannessuhr
"""


import pycrafter6500
import numpy
import PIL.Image


# divide by 129, to convert 8 bit picture to a binary picture ?
images = [numpy.asarray(PIL.Image.open("./testimage.tif")) / 129]

# create a DMD class object
dlp = pycrafter6500.DMD()

# stop any already existing sequence
dlp.stop_sequence()

# change to pattern on the fly mode
dlp.change_mode(3)

# sequence parameters
exposure = [1000000] * 30
dark_time = [0] * 30
trigger_in = [False] * 30
trigger_out = [1] * 30

# define sequence
dlp.define_sequence(images, exposure, trigger_in, dark_time, trigger_out, 0)

# start sequence
dlp.start_sequence()