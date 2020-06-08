#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun  3 21:18:30 2020

@author: hannessuhr
"""


import pycrafter6500
import PIL
import numpy
import time
import multiprocessing as mp
import threading

image = numpy.asarray(PIL.Image.open("./test_image_x_y/test_image_x_y0.png"))
images = [image] * 1
counter = 0

def multi_ecnode(image):
    image_data = pycrafter6500.merge_images(image)
    encoded_image, byte_count = pycrafter6500.encode(image_data)
    return encoded_image, byte_count, counter


# first single processed
start_time = time.perf_counter()
for image in images:

    image_data = pycrafter6500.merge_images(image)
    encoded_image = pycrafter6500.encode(image_data)

end_time = time.perf_counter() - start_time

cpu_count = mp.cpu_count()

print(encoded_image[0])
"""
# multi processed
pool = mp.Pool(processes=cpu_count)

start_time2 = time.perf_counter()

result_list = pool.map_async(multi_ecnode, images)

results = result_list.get()

end_time2 = time.perf_counter() - start_time2

"""

"""
# try threading

start_time3 = time.perf_counter()

thread_list = []

for image in images:
    thread = threading.Thread(target=multi_ecnode, args=(image,))
    thread.start()
    thread.join()
    thread_list.append(thread)
    

end_time3 = time.perf_counter() - start_time3
"""