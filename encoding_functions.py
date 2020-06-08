# -*- coding: utf-8 -*-
"""
Created on Wed May 27 13:52:52 2020

@author: hannessuhr
"""

import PIL
import numpy
"""

#line_data = ['0x04','0x05']
line_data = [0x04,0x05,0x06,0x04,0x05,0x06,0x04,0x05,0x06,0x77,0x77,0x77,0x77,0x77,0x77,0x77,0x77,0x77,0x77,0x77,0x77,0x77,0x77,0x77,0x04,0x05,0x06,0x07,0x08,0x09,0x0A,0x0B,0x0C,0x78,0x9A,0xBC,0x78,0x9A,0xBC]
line_data_2 = [0x1D,0x1E,0x1F,0x1D,0x1E,0x1F,0x1D,0x1E,0x1F,0x1D,0x1E,0x1F,0x1D,0x1E,0x1F,0x1D,0x1E,0x1F,0x1D,0x1E,0x1F,0x21,0x22,0x23,0x21,0x22,0x23,0x21,0x22,0x23,0x21,0x22,0x23,0x21,0x22,0x23,0x21,0x22,0x23]
image_data = [line_data, line_data_2]

# do the decoding of the line
img1 = PIL.Image.open("./test_image_x_y/test_image_x_y0.png")
img2 = numpy.asarray(img1)

img3 = numpy.asarray(PIL.Image.open("./test_image_0.tif"))

"""

def encode_line(line):
    # encodes a line simple

    prev_byte = line[0]
    counter = 0
    encoding = []
    byte_count = 0
    
    # nested function for adding encoded and count bytes
    def append_and_count():
        encoding.append(counter)
        encoding.append([0,0,prev_byte])
        
    
    for byte in line:
        if byte == prev_byte:
            counter += 1
            if counter == 255:
                append_and_count()
                byte_count += 4
                prev_byte = byte
                counter = 0
        else:
            append_and_count()
            byte_count += 4
            prev_byte = byte
            counter = 0
    else:
        pass
        append_and_count()
        byte_count += 4
            
    return encoding, byte_count

def encode_singles(encoded_line):

    # encodes all single entries ones in an encoded line
    counter = 0
    # entries we have to save
    save_encoded = []
    # the new encoded list
    encoded_encoded = []
    byte_count = 0
    
    # nested function for appending double encoded data
    def append_double_encoded():
        encoded_encoded.append(0)
        encoded_encoded.append(counter)
        encoded_encoded.append(save_encoded)

    # iterate over every second entry
    for index in range(0, len(encoded_line), 2):
        if index+1 < len(encoded_line):
            # when we see that we have a entry with the numeber 1 count
            # and save it
            if encoded_line[index] == 1:
                counter += 1
                save_encoded.append(encoded_line[index+1])
            # when we dont have a single entry anymore
            else:
                # append the saved entries only when we counted at least 1
                if counter > 0:
                    append_double_encoded()
                    byte_count = byte_count + 2 + counter * 3
                # reset the counter
                counter = 0
                # reset the saved single entries
                save_encoded = []
                # append the already ecnoded entries
                encoded_encoded.append(encoded_line[index])
                encoded_encoded.append(encoded_line[index+1])
                byte_count += 4
    # if the for loop ends
    else:
        # append already saved single entries
        if counter > 0:
            append_double_encoded()
            byte_count = byte_count + 2 + counter * 3
            counter = 0
            save_encoded = []
   
    # return the new encoded and the original encoded list
    return encoded_encoded, byte_count,  encoded_line

def unwrap_encoded(encoded):
    unwrapped_encoded = []
    for double_wrapped in encoded:
        if type(double_wrapped) is list:
            for wrapped in double_wrapped:
                if type(wrapped) is list:
                    for encode in wrapped:
                        unwrapped_encoded.append(numpy.uint8(encode))
                else:
                    unwrapped_encoded.append(numpy.uint8(wrapped))
        else:
            unwrapped_encoded.append(numpy.uint8(double_wrapped))

    return unwrapped_encoded


def fully_encode_line(line):
    primary_encoding = encode_line(line)
    secondary_encoding = encode_singles(primary_encoding[0])
    final_encoding = unwrap_encoded(secondary_encoding[0])
    return final_encoding, secondary_encoding[1]

def fully_encode_image(image):
    byte_count = 0
    encoded_image = []
    counter = 0
    for line in image:
        encoded_line, line_byte_count = fully_encode_line(line)
        #print(encoded_line)
        encoded_image += encoded_line
        byte_count += line_byte_count
        # append end of line command + image padding
        if counter < 1079:
            encoded_image += [0,0,0,0,0]
            byte_count += 5
        counter += 1

        
    # append end of image command + end of file padding
    encoded_image += [0,1,0,1,0,0,0,0,0,0,0,0]
    byte_count += 12
    
    return encoded_image, len(encoded_image)
    

#encoded_line, byte_number = encode_line(line_data)
#print("\n")
#encoded_line2, byte_number2 = encode_line(line_data_2)
#print("\n")
#encoded_encoded_line = encode_singles(encoded_line)
#print("\n")
#encoded_encoded_line2 = encode_singles(encoded_line2)

#final_encoded = unwrap_encoded(encoded_encoded_line[0])
#final_encoded_2 = unwrap_encoded(encoded_encoded_line2[0])

#test = fully_encode_image(img3)
#print(test)