# -*- coding: utf-8 -*-
"""
Created on Mon May  4 14:58:50 2020

@author: hannessuhr
"""

import pycrafter6500
import numpy
import PIL.Image
import time

images = [numpy.asarray(PIL.Image.open("./test_image_x_y0.png"))]

# create a DMD class object
dlp = pycrafter6500.DMD()

#dlp.get_minimum_led_pattern_exposure()

dlp.set_led_pwm(10)

# stop any already existing sequence
dlp.stop_sequence()

# change to pattern on the fly mode
dlp.change_mode(3)

# sequence parameters 
exposure_time = 3000000     # in [us]
repetition_number = 3
# list length must be always 30 ????
list_length = 24
exposure = [exposure_time] * list_length
dark_time = [0] * list_length
trigger_in = [False] * list_length
trigger_out = [1] * list_length

# define sequence
dlp.define_sequence(images, exposure, trigger_in, dark_time, trigger_out,
                    repetition_number)

# start sequence
dlp.start_sequence()

# stop any already existing sequence
if not repetition_number == 0:
    time.sleep(exposure_time/1e6 * repetition_number)
    dlp.stop_sequence()