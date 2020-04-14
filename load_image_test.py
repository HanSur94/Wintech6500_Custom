# -*- coding: utf-8 -*-
"""
Created on Tue Apr 14 15:20:26 2020

@author: Hannes
"""


import numpy
import PIL.Image
import pycrafter6500
import time


image_raw_1 = numpy.asarray(PIL.Image.open("test_image_0.tif")) / 129
image_raw_2 = numpy.asarray(PIL.Image.open("test_image_2.jpg"))[:,:,1] / 129

images = [image_raw_1, image_raw_2]






