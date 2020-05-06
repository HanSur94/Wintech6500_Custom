# -*- coding: utf-8 -*-
"""
Created on Wed Apr 29 17:19:17 2020

@author: hannessuhr
"""

import pycrafter6500
import numpy
import PIL.Image
import os
import time

# load in all images

#  create sequence parameters for per image

# for each image do
    # load up image and define sequence
    # start exposure time
    # stop after exposure time

folder_name = "./test_image_x_y"
image_format = ".png"

exposure_time = 1000000
dark_time = 0

brightness = [255,255,255,255]
exposure = [exposure_time] * 30
dark_time = [dark_time] * 30
trigger_in = [False] * 30
trigger_out = [1] * 30

images = []
exposures = []
dark_times = []
trigger_ins = []
trigger_outs = []

for file in os.listdir(folder_name):
    if file.endswith(image_format):
        file_name = os.path.join(folder_name, file)
        print("fetching image %s " % file_name)
        image = [numpy.asarray(PIL.Image.open(file_name))]
        images.append(image)
        
for image in images:
    exposures.append(exposure)
    dark_times.append(dark_time)
    trigger_ins.append(trigger_in)
    trigger_outs.append(trigger_out)
    
# create a DMD class object
dlp = pycrafter6500.DMD()

dlp.show_image_sequence(images, brightness, exposures, dark_times, trigger_ins, 
                        trigger_outs, True)    
    
    
"""
# create a DMD class object
dlp = pycrafter6500.DMD()

# stop any already existing sequence
dlp.stop_sequence()

# change to pattern on the fly mode
dlp.change_mode(3)

for index, image in enumerate(images):
    print("image Index %d " % index)
    
    # stop any already existing sequence
    dlp.stop_sequence()
    
    t = time.clock()
    # define sequence
    dlp.define_sequence(image, exposures[index], trigger_ins[index],
                        dark_times[index], trigger_outs[index], 1)
    print("upload time: %f" % t)

    # start sequence
    dlp.start_sequence()
    print("display image")
       
    # wait some time, therefore projector can finish displaying the image
    waiting_time = (exposure_time +  dark_time) / 1000000
    time.sleep(waiting_time + 1)
    
dlp.stop_sequence()
"""

