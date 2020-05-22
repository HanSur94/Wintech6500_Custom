# -*- coding: utf-8 -*-
"""
Created on Fri May 22 17:07:07 2020

@author: hannessuhr
"""


import pycrafter6500
import numpy
import PIL.Image
import time
import os
import RLE

folder_name = "./test_image_x_y/"
image_format = ".png"

images = []

img1 = PIL.Image.open("./test_image_x_y/test_image_x_y0.png")

orgimg = list(img1.getdata(0))
        
payload = RLE.encodeImage(orgimg, img1.size[0], img1.size[1], img1.mode)  
print(str(payload))