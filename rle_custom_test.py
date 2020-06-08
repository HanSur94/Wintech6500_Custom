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
import binascii
import functools
from pymatbridge import pymatbridge

folder_name = "./test_image_x_y/"
image_format = ".png"



img1 = PIL.Image.open("./test_image_x_y/test_image_x_y0.png")
img2 = numpy.asarray(img1)
image = numpy.asarray(PIL.Image.open("./test_image_x_y/test_image_x_y0.png"))
#image = numpy.asarray(PIL.Image.open("./test_image_0.tif"))
#image = image.transpose()

#image = numpy.asarray(PIL.Image.open("./test_image_0.tif"))
images = [image]
#image_data, size = pycrafter6500.encode5(image)

file_object = open("./encoded.txt",'r')
encoded = file_object.read()
encoded = encoded.split(',')
encoded = list(map(int,encoded))

#payload = pycrafter6500.encode3(img2)

exposure_time = 10000000
dark_time = 0

brightness = [255]
exposure = [exposure_time] * 30
dark_time = [dark_time] * 30
trigger_in = [False] * 30
trigger_out = [1] * 30

        
arr = []
for i in images:
    arr.append(i)  
    #arr.append(numpy.ones((1080,1920),dtype='uint8'))

num = len(arr)
encoded_images = []
sizes = []

dlp = pycrafter6500.DMD()

#dlp.wake_up()

#dlp.idle_off()
dlp.stop_sequence()
dlp.set_led_pwm(255)
dlp.change_mode(3)

for i in range(int((num - 1) / 24 + 1)):

    encoded_images.append(encoded)
    sizes.append(len(encoded))
    """
    print('merging...')
    
    if i < ((num - 1) / 24):
        image_data = pycrafter6500.merge_images(arr[i * 24:(i + 1) * 24])
    else:
        image_data = pycrafter6500.merge_images(arr[i * 24:])
    
    merged_image = image_data

    print('encoding...')
  
    image_data_raw, size = pycrafter6500.encode(image_data)
    """
    """
    image_data = []
    for data in image_data_raw:
        # d = numpy.uint8(data)
        d = int(data)
        image_data.append(d)
       
    #image_data = numpy.uint8(image_data)
    encoded_images.append(image_data)
    sizes.append(size)
    #print(image_data)
    #print(size)
    """
# append enoded image data to a list for later uploading process
#self.encoded_images_list.append(encoded_images)
#self.sizes_list.append(sizes)

# here we define the pattern for the image
#dlp.define_pattern(1, 3000000, 8, '100',
#                            False, 0,
#                            True,1,1)
#dlp.set_bmp2(size)
#dlp.load_bmp(image_data,size)

    if i < ((num - 1) / 24):
        for j in range(i * 24, (i + 1) * 24):
            dlp.define_pattern(j, exposure[j], 8, '100',
                                trigger_in[j], dark_time[j],
                                trigger_out[j], i, j - i * 24)
    else:
        for j in range(i * 24, num):
            dlp.define_pattern(j, exposure[j], 8, '100',
                                trigger_in[j], dark_time[j],
                                trigger_out[j], i, j - i * 24)
        
# configure the look up table of the DLP900
dlp.configure_lut(num, 1)

for i in range(int((num - 1) / 24 + 1)):
            
    dlp.set_bmp(int((num - 1) / 24 - i),
                 sizes[int((num - 1) / 24 - i)])

    print('uploading...')

    dlp.load_bmp(encoded_images[int((num - 1) / 24 - i)],
                  sizes[int((num - 1) / 24 - i)])
    
    #
           
dlp.start_sequence()

#time.sleep(3)

#dlp.stop_sequence()
#dlp.stand_by()

#print(payload)


"""
orgimg = list(img1.getdata(0))
        
b = RLE.encodeImage(orgimg, img1.size[0], img1.size[1], img1.mode) 
#payload = int.from_bytes(b, byteorder='big', signed=False)
#payload = int(binascii.hexlify(b), 16)

payload_str = str(b) 

#payload_str = payload_str.split("x")
payload_str = payload_str.split("\\")
print(payload_str[len(payload_str)-1])
payload_str2 = []
payload_int = []

for index, string in enumerate(payload_str):
    if "@" in string:
        payload_str.insert(index,"0x00")
        payload_str.insert(index + 1,"0x00")

for index, string in enumerate(payload_str):
    
    if "@" in string:
        string = string.replace("@",'')

    string = string.replace("`",'')
    string = string.replace("'",'')
    string = string.replace(")",'')
    string = "0" + string
    payload_str2.append(string)
    
payload_str2[0] = "0"
for string in payload_str2:
    payload_int.append(int(string,16))


#payload_int = int(payload_str2)
#print(payload_str)

arr = []
for i in img2:
    arr.append(i)  
    #arr.append(numpy.ones((1080,1920),dtype='uint8'))

num = len(arr)
encoded_images = []
sizes = []

for i in range(int((num - 1) / 24 + 1)):
   
    print('merging...')

    if i < ((num - 1) / 24):
        image_data = pycrafter6500.merge_images(arr[i * 24:(i + 1) * 24])
    else:
        image_data = pycrafter6500.merge_images(arr[i * 24:])
    

    print('encoding...')
        
    image_data, size = pycrafter6500.encode(image_data)
    encoded_images.append(image_data)
    sizes.append(size)
    
"""

#payload2 = pycrafter6500.encode(img2)