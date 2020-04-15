import pycrafter6500
import numpy
import PIL.Image
import time


def load_image_sequence(image_path, image_names, image_format, image_number,
                        start_sequence_index):
    
    # create arrays for image names
    image_names = [image_names] * image_number
    # create array for the image sequence
    image_sequence = []
    
    # iterate over the image names and modify the names
    for index, name in enumerate(image_names):
        name = image_path + name + "%d" % (index + start_sequence_index) + image_format
        # load in image name with modified image name
        image = load_image(name)
        # get numpy array out of the list and append in new List
        image_sequence.append(image[0])

    return image_sequence


def load_image(image_name):
    # load in a image and retrun as list of numpy arrays
    return [numpy.asarray(PIL.Image.open(image_name))]
    
"""        
images = load_image_sequence("./test_image_seq_single/",
                             "test_image_sequence",".png", 8, 1)
"""
images = load_image_sequence("./test_image_x_y/",
                             "/test_image_x_y",".png", 3, 0)



# load in the image
# divide by 129, to convert 8 bit picture to a binary picture ?
# images really must be a list


#image_raw = numpy.asarray(PIL.Image.open("test_image_0.tif"))
#image_raw_2 = numpy.asarray(PIL.Image.open("test_image_2.jpg"))[:,:,1]
#image_raw_1 = numpy.asarray(PIL.Image.open("./test_image_x_y/test_image_x_y1.png"))
#images = [image_raw_1]

# create a DMD class object
dlp = pycrafter6500.DMD()

# stop any already existing sequence
dlp.stop_sequence()

# change to pattern on the fly mode
dlp.change_mode(3)

# sequence parameters 
exposure_time = 1000000     # in [us]
repetition_number = 0
# list length must be always 30 ????
list_length = 24
exposure = [exposure_time] * list_length
dark_time = [1000000] * list_length
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
    
