import pycrafter6500
import numpy
import PIL.Image
import time
import os

folder_name = "./test_image_x_y"
image_format = ".png"

exposure_time = 3000000
dark_time = 0

brightness = [255,128,128,255]
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
    