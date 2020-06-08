# -*- coding: utf-8 -*-
"""
Created on Fri Jun  5 15:10:27 2020

@author: hannessuhr
"""

import numpy
import pycrafter6500
import PIL
from for_redistribution_files_only import formatrep

def dec2hex(d):
    return hex(d).split('x')[-1]

def formatrep_(n):
    if n < 128:
        x = dec2hex(n)
    else:
        bitand = n & 127
        bitor = bitand | 128
        x1 = dec2hex(bitor)
        x2 = dec2hex(n >> 7)
        x = x1 + x2
        
    return x


image = PIL.Image.open('./test_image_x_y0.png')
image = numpy.asarray(image, dtype=numpy.uint8)
#image = numpy.zeros((1920,1080),dtype=numpy.uint8)
bit_depth = 8
signature = [0x53,0x70,0x6C,0x64]

image_width = image.shape[1]
image_width = pycrafter6500.convert_num_to_bit_string(image_width,16)
image_width = pycrafter6500.bits_to_bytes(image_width)

image_height = image.shape[0]
image_height = pycrafter6500.convert_num_to_bit_string(image_height,16)
image_height = pycrafter6500.bits_to_bytes(image_height)

num_of_bytes = image.shape[0]*image.shape[1]*bit_depth
background_color = [0x00, 0x00, 0x00, 0x00]
compression = 2
    
header = [signature, image_width, image_height, num_of_bytes,
          0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, background_color, 
          0x00, compression, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
          0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
          0x00, 0x00, 0x00];

image = image.transpose()

img = numpy.zeros([image.shape[0]*image.shape[1],2],dtype=numpy.uint8)
image24 = image.reshape(image.shape[0]*image.shape[1],1)
image24 = numpy.concatenate((image24,img),axis=1)




image_new = numpy.array(image24, dtype=str)

#image_new = numpy.add(image_new, numpy.array(img, dtype='<U1'))
"""
for i in image24:
    image_new = '00' + str(i)
"""
szy, szx = image.shape
"""
for i in range(0,szx):
    u, ic = numpy.unique(image_new[:,:], return_counts=True)
    print(ic)
    print(u)
"""
