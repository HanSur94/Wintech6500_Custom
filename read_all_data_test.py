#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun 10 14:39:19 2020

@author: hannessuhr
"""

import matplotlib.pyplot as plt
import PIL
import numpy
import os

is_matlab_encoded = False
sequence_data = []

sequence_folder_name = './test_image_numbered_greyscale'
file_name = sequence_folder_name + '/sequence_param.txt'

try:
    file = open(file_name, 'r')
    lines = file.readlines()
    file.close()
except:
    raise Exception('No "sequence_param.txt" could be' + 
                    ' found in the image folder.')

filtered_line = []

# filte out blank line and comments (lines with #)
for line in lines:
    if not '#' in line:
        if not len(line) <= 3:
            filtered_line.append(line)
            
# split the line with ; and put them in 2D matrix
for line in filtered_line:
    splitted_line = line.split(';')
    
    # remove everything after 7th entry
    del splitted_line[7:len(splitted_line)]
    
    # save data in sequence data
    sequence_data.append(splitted_line)

# for each entry now load the image
for index, line in enumerate(sequence_data):
    
    # image nam is always the first one
    image_name = line[0]
    
    # load in the images as a numpy array with datatype uint8
    try:
        image_data = numpy.asarray(
            PIL.Image.open(sequence_folder_name + '/' + image_name),
            dtype=numpy.uint8)
    except:
        raise Exception('Image %s could not be found or loaded'%(image_name) + 
                        'Check that the image is existing or remove it' + 
                        'from the sequence_param.txt list.' )
        
        
    # also check here that the image data is single matrix and does not have 
    # multiple color channels!
    # also check that the images have the correct format
    if not image_data.shape == (1080, 1920):
        raise Exception('The size of the images you are using is wrong.' + 
                        'The images must be the in the size of (1080,1920).' + 
                        'Also they have to be 8 Bit grayscale images.')
    
    # append the image data at the 8th entry of the sequence data
    sequence_data[index].append(image_data)
    
    # plot the load images in the console
    fig = plt.figure()
    plt.imshow(image_data, cmap='gray')
    plt.colorbar()
    plt.show()

# check if we have the encoded_images.txt, because it is not necessary
files = os.listdir(sequence_folder_name)
if 'encoded_images.txt' in files:
    is_matlab_encoded = True
    print('MATLAB Encoding was found.')
else:
    is_matlab_encoded = False
    print('No MATLAB encoding was found.')
    
# if the encoded data exists, we load them in a seperate array
if is_matlab_encoded == True:
    
    # read in all lines
    file_name = sequence_folder_name + '/encoded_images.txt'
    file = open(file_name, 'r')
    encoded_raw = file.readlines()
    file.close()
    encoded = []

    # iterate over each line, split up filter elements
    for index in range(1, len(encoded_raw), 1):
        print(index)
        if index % 2 == 0:
            print(index)
            enc_raw_splitted = encoded_raw[index].split(',')
            enc_raw_filtered = []
            
            for element in enc_raw_splitted:
                if not element == '' and not element == '\n':
                    enc_raw_filtered.append(element)
                    
            encoded.append(list(map(int,enc_raw_filtered)))
        else:
            image_name = encoded_raw[index].split(',')[0]
            encoded.append(image_name)
            
    # check here, that the number of encoded entries is double the number of
    # images. It has to be double, since encodin data contains also the image
    # names
    if not len(encoded) == len(sequence_data) * 2:
        raise Exception('The number of encded image data found is not the' +
                        'same as the number of images found. ' +
                        '# images = %d' %(len(sequence_data)) + 
                        '# encoded images = %d'%(len(encoded)/2))
        
            
    # now save the data in the sequence_data array to the corresponding image
    for index, line in enumerate(sequence_data):
        image_name = line[0]
        encoded_index = encoded.index(image_name)
        sequence_data[index].append(encoded[encoded_index+1])
        print(encoded[encoded_index])
        


# soring function that reurns the index of a list in the sequence_data list
def sort_index(element):
    return element[1]

# now we can sort sequence_data according to the index of the images
sequence_data.sort(reverse=False, key=sort_index)

encoded_raw = []
filtered_line= []
