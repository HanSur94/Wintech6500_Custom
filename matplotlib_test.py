# -*- coding: utf-8 -*-
"""
Created on Fri May 15 13:43:03 2020

@author: hannessuhr
"""
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import numpy
import PIL

image_name = "./test_image_0.tif"
#img = mpimg.imread(image_name)
img = [numpy.asarray(PIL.Image.open(image_name))]

print(img)

imgplot = plt.imshow(img[0])
print(imgplot)