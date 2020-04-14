import pycrafter6500
import numpy
import PIL.Image
import time

# load in the image
# divide by 129, to convert 8 bit picture to a binary picture ?
# images really must be a list



image_raw_1 = numpy.asarray(PIL.Image.open("test_image_0.tif"))
#image_raw_2 = numpy.asarray(PIL.Image.open("test_image_2.jpg"))[:,:,1]

images = [image_raw_1]

#images = [images[0][:,:,1]]

# create a DMD class object
dlp = pycrafter6500.DMD()

# stop any already existing sequence
dlp.stop_sequence()

# change to pattern on the fly mode
dlp.change_mode(3)

# sequence parameters 
exposure_time = 1000000
repetition_number = 100
# list length must be always 30 ????
list_length = 30
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
time.sleep(exposure_time/1e6 * repetition_number)
dlp.stop_sequence()
