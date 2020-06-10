"""
Pycrafter 6500 is a native Python controller for TI's dlplcr6500evm.

The script requires Pyusb and Numpy to be present in your Python environment.
The test script included requires the Python Image Library (PIL or pillow)
for opening a test image. The device must have libusb drivers installed,
for Windows users we suggest to install them through Zadig
 (http://zadig.akeo.ie/), and selecting the libusb_win32 driver.

If you use this library for scientific publications, please consider mentioning
the library and citing our work (https://doi.org/10.1364/OE.25.000949).

Features list:
--------------

Basic control of the evaluation module (modes selection, idle toggle,
start/pause/stop sequences).
Upload of a sequence of EXCLUSIVELY BINARY images for "patterns on the fly"
mode, with independent control of exposure times, dark times, triggers and
repetitions number.

"""
import usb.core
import usb.util
import time
import numpy
import PIL.Image
import os
import tkinter as tk
from tkinter import filedialog
import threading
import RLE
import encoding_functions

import matplotlib.pyplot as plt
import matplotlib.image as mpimg


def load_image_sequence(image_folder_name, print_image_name=False):
    """
    Loads in multiple images from a folder.

    Parameters
    ----------
    image_folder_name : str
         The local path to the folder. E.g.: Images are in the subfolder 
        "image_folder" in the local directory of the running script. Therefore
        the image_folder_name must be: "./image_folder/" .
    print_image_name : boolean, optional
        If True, then the image path will be printed in the console.
        The default is False.

    Returns
    -------
    image_sequence : numpy array list
        A list of numpy array's containing the image data.

    """
    # init image sequence list
    image_sequence = []
    
    # fetch all files of the image_folder_name
    for filename in os.listdir(image_folder_name):
        
        # print file name if needed
        if print_image_name:
            print(os.path.join(image_folder_name,filename))
            
        # load image and append to list
        image_sequence.append(
            load_image(os.path.join(image_folder_name,filename))[0])
        
    return image_sequence


def load_image(image_name):
    """
    Loads in a single image.

    Parameters
    ----------
    image_name : str
        The Path & Name of the image. E.g.: The images is in the subfolder 
        "image_folder" in the local directory of the running script and the 
        name of the image is "test_image.png". Therefore
        the image_name must be: "./image_folder/test_image.png" .

    Returns
    -------
    list
        The image as a numpy array in a list.

    """
    # load in a image and retrun as list of numpy arrays
    return [numpy.asarray(PIL.Image.open(image_name))]

def convert_num_to_bit_string(number, length):
    """
    Convert a number into a bit string of given length.

    Parameters:
    ----------
    number : int
        Number to convert
    length : int
        Length of the Number to convert

    Returns:
    -------
    bit_string : str
        String representing the number as bits.

    """
    # return binary representation (string) of integer number
    bit_string = bin(number)[2:]
    padding = length - len(bit_string)
    bit_string = '0' * padding + bit_string

    return bit_string


def bits_to_bytes(bit_string):
    """
    Convert a bit string into a given number of bytes.

    Parameters
    ----------
    bit_string : str
        String representing a number in bit representation.

    Returns
    -------
    byte_list : byte list
        List of bytes.

    """
    byte_list = []
    if len(bit_string) % 8 != 0:
        padding = 8 - len(bit_string) % 8
        bit_string = '0' * padding + bit_string
    for i in range(int(len(bit_string) / 8)):
        byte_list.append(int(bit_string[8 * i:8 * (i + 1)], 2))

    byte_list.reverse()

    return byte_list


def merge_images(images):
    """
    Encode a 8 bit numpy array matrix as a string of bits.

    Parameters
    ----------
    images : numpy array
        A numpy array with bit depth of 8.

    Returns
    -------
    merged_image : str
        String of numbers represented in bits.

    """
    merged_image = numpy.zeros((1080, 1920, 3), dtype='uint8')

    for i in range(len(images)):
        if i < 8:
            merged_image[:, :, 2] = merged_image[:, :, 2] + images[i] * (
                        2 ** i)
        if i > 7 and i < 16:
            merged_image[:, :, 1] = merged_image[:, :, 1] + images[i] * (
                        2 ** (i - 8))
        if i > 15 and i < 24:
            merged_image[:, :, 0] = merged_image[:, :, 0] + images[i] * (
                        2 ** (i - 16))

    return merged_image


def encode(image):
    """
    Encode a image into a bit string.

    Parameters
    ----------
    image : numpy array
        Image represented as an numpy array. Bit depth is 8.

    Returns
    -------
    bit_string : str
        Is the encoded image represented as bits.
    byte_count : int
        Is the number of bytes from the bit string.

    """
    #upload_time = time.process_time()
    
    # header creation
    byte_count = 48
    bit_string = []

    bit_string.append(0x53)
    bit_string.append(0x70)
    bit_string.append(0x6c)
    bit_string.append(0x64)

    width = convert_num_to_bit_string(1920, 16)
    width = bits_to_bytes(width)
    for i in range(len(width)):
        bit_string.append(width[i])

    height = convert_num_to_bit_string(1080, 16)
    height = bits_to_bytes(height)
    for i in range(len(height)):
        bit_string.append(height[i])

    total = convert_num_to_bit_string(0, 32)
    total = bits_to_bytes(total)
    for i in range(len(total)):
        bit_string.append(total[i])

    for i in range(8):
        bit_string.append(0xff)

    """
    Setting the background color to black.
    """
    for i in range(4):
        bit_string.append(0x00)

    bit_string.append(0x00)

    """
    Enhanced run length encoding
    To achieve higher compression ratios, this compression format takes
    advantage of the similarities from line-to-line and uses one or two
    bytes to encode the length.
    """
    bit_string.append(0x02)

    bit_string.append(0x01)

    for i in range(21):
        bit_string.append(0x00)

    n = 0
    i = 0
    j = 0

    while i < 1080:
        while j < 1920:
            if i > 0 and numpy.all(image[i, j, :] == image[i - 1, j, :]):
                while j < 1920 and numpy.all(
                        image[i, j, :] == image[i - 1, j, :]):
                    n = n + 1
                    j = j + 1

                bit_string.append(0x00)
                bit_string.append(0x01)
                byte_count += 2

                if n >= 128:
                    byte1 = (n & 0x7f) | 0x80
                    byte2 = (n >> 7)
                    bit_string.append(byte1)
                    bit_string.append(byte2)
                    byte_count += 2

                else:
                    bit_string.append(n)
                    byte_count += 1
                n = 0
            else:
                if j < 1919 and numpy.all(
                        image[i, j, :] == image[i, j + 1, :]):
                    n = n + 1
                    while j < 1919 and numpy.all(
                            image[i, j, :] == image[i, j + 1, :]):
                        n = n + 1
                        j = j + 1
                    if n >= 128:
                        byte1 = (n & 0x7f) | 0x80
                        byte2 = (n >> 7)
                        bit_string.append(byte1)
                        bit_string.append(byte2)
                        byte_count += 2

                    else:
                        bit_string.append(n)
                        byte_count += 1

                    bit_string.append(image[i, j - 1, 0])
                    bit_string.append(image[i, j - 1, 1])
                    bit_string.append(image[i, j - 1, 2])
                    byte_count += 3

                    j = j + 1
                    n = 0

                else:
                    if (j > 1917
                            or numpy.all(image[i, j + 1, :] ==
                                         image[i, j + 2, :])
                            or numpy.all(image[i, j + 1, :] ==
                                         image[i - 1, j + 1, :])):
                        bit_string.append(0x01)
                        byte_count += 1
                        bit_string.append(image[i, j, 0])
                        bit_string.append(image[i, j, 1])
                        bit_string.append(image[i, j, 2])
                        byte_count += 3

                        j = j + 1
                        n = 0

                    else:
                        bit_string.append(0x00)
                        byte_count += 1

                        toappend = []

                        while (numpy.any(image[i, j, :] != image[i, j + 1, :])
                               and numpy.any(
                                        image[i, j, :] != image[i - 1, j, :])
                               and j < 1919):
                            n = n + 1
                            toappend.append(image[i, j, 0])
                            toappend.append(image[i, j, 1])
                            toappend.append(image[i, j, 2])
                            j = j + 1

                        if n >= 128:
                            byte1 = (n & 0x7f) | 0x80
                            byte2 = (n >> 7)
                            bit_string.append(byte1)
                            bit_string.append(byte2)
                            byte_count += 2

                        else:
                            bit_string.append(n)
                            byte_count += 1

                        for k in toappend:
                            bit_string.append(k)
                            byte_count += 1
                        n = 0

        j = 0
        i = i + 1
        bit_string.append(0x00)
        bit_string.append(0x00)
        byte_count += 2

    bit_string.append(0x00)
    bit_string.append(0x01)
    bit_string.append(0x00)
    byte_count += 3

    while (byte_count) % 4 != 0:
        bit_string.append(0x00)
        byte_count += 1

    size = byte_count

    #print(size)

    total = convert_num_to_bit_string(size, 32)
    total = bits_to_bytes(total)
    for i in range(len(total)):
        print(total)
        bit_string[i + 8] = total[i]
        
        
    #upload_time = time.process_time() - upload_time
    #print('encoding time [s]: %f' % upload_time)

    return bit_string, byte_count

class DMD():
    """
    DMD controller Class.

    Attributes
    ----------
    dev : usb class object
            Usb object to communicate with

    Methods
    -------
    usb_command()
        Send a command to the controler via usb.
    check_for_errors()
        Check if any error from the controler can be received.
    read_reply()
        Read incoming data from the controler via usb.
    idle_on()
        Activate the idle mode of the controler.
    idle_off()
        Deactivate the idle mode of the controler.
    stand_by()
        Set controler into standby mode.
    wake_up()
        Wake up controler from standby mode.
    reset()
        Reset the controler.
    test_read()
       Test to receive data from controler.
    test_write()
        Test to write data to the controler.
    change_mode()
        Set the operating mode of the controler.
    start_sequence()
        Start a image sequence.
    pause_sequence()
        Pause image sequence.
    stop_sequence()
        Stop image sequence.
    configure_lut()
        Configure LUT (Look Up Table) of the controler.
    define_pattern()
        Define a pattern to display.
    set_bmp()
        Prepare controler for uploading .bmp image.
    load_bmp()
        Upload .bmp image to controler.
    define_sequence()
        Define a image sequence to display.
        
        
    long_axis_image_flip()
    short_axis_image_flip()
    dmd_park()
    dmd_unpark()
    pwm_setup()
    blue_led_control()

    Planned Methods
    ---------------
    
    get_hardware_status()
    get_system_status()
    get_main_status()
    get_version

    """

    def __init__(self):
        """
        DMD class constructor.

        Returns
        -------
        None.

        """
        self.dev = usb.core.find(idVendor=0x0451, idProduct=0xc900)
        # was it found?
        if self.dev is None:
            raise ValueError('Device not found')
        self.dev.set_configuration()
        self.ans = []
        self.encoded_image = []
        self.encoded_images_list = []
        self.sizes = []
        self.sizes_list = []
        self.num_list = []
        self.i_list = []
        self.pattern_payload_list = []

    def usb_command(self, mode, byte_sequence, com1, com2, data=None):
        """
        USB command function. Sends and receives data/commands via USB.

        Parameters
        ----------
        mode : str
            Read or write mode. Choose eiter 'r' (read) or 'w' (write)
        byte_sequence : byte
            ?.
        com1 : byte
            COM Port 1.
        com2 : byte
            COM Port 2.
        data : byte list, optional
            Data to write as a list of bytes. The default is None.

        Returns
        -------
        None.

        """
        buffer = []
        flag_string = ''
        if mode == 'r':
            flag_string += '1'
        else:
            flag_string += '0'
        flag_string += '1000000'
        buffer.append(bits_to_bytes(flag_string)[0])
        buffer.append(byte_sequence)
        temp = bits_to_bytes(convert_num_to_bit_string(len(data) + 2, 16))
        buffer.append(temp[0])
        buffer.append(temp[1])
        buffer.append(com2)
        buffer.append(com1)

        if len(buffer) + len(data) < 65:

            for i in range(len(data)):
                buffer.append(data[i])

            for i in range(64 - len(buffer)):
                buffer.append(0x00)

            self.dev.write(1, buffer)

        else:
            for i in range(64 - len(buffer)):
                buffer.append(data[i])

            self.dev.write(1, buffer)

            buffer = []

            j = 0
            while j < len(data) - 58:
                buffer.append(data[j + 58])
                j = j + 1
                if j % 64 == 0:
                    self.dev.write(1, buffer)

                    buffer = []

            if j % 64 != 0:

                while j % 64 != 0:
                    buffer.append(0x00)
                    j = j + 1

                self.dev.write(1, buffer)

        self.ans = self.dev.read(0x81, 64)

    def check_for_errors(self):
        """
        Check error reports in the DLP module answer.

        Returns
        -------
        None.

        """
        self.usb_command('r', 0x22, 0x01, 0x00, [])
        if self.ans[6] != 0:
            print(self.ans[6])

    def read_reply(self):
        """
        Print all of the dlp answer.

        Returns
        -------
        None.

        """
        for i in self.ans:
            message = str(i) +  "\t" + chr(i) + "\t" + (bin(i))
            print(message)

    def idle_on(self):
        """
        Activate idle mode.

        Returns
        -------
        None.

        """
        self.usb_command('w', 0x00, 0x02, 0x01, [int('00000001', 2)])
        self.check_for_errors()

    def idle_off(self):
        """
        Deactivate idle mode.

        Returns
        -------
        None.

        """
        self.usb_command('w', 0x00, 0x02, 0x01, [int('00000000', 2)])
        self.check_for_errors()

    def stand_by(self):
        """
        Activate standby mode.

        Returns
        -------
        None.

        """
        self.usb_command('w', 0x00, 0x02, 0x00, [int('00000001', 2)])
        self.check_for_errors()

    def wake_up(self):
        """
        Activate from stand by mode.

        Returns
        -------
        None.

        """
        self.usb_command('w', 0x00, 0x02, 0x00, [int('00000000', 2)])
        self.check_for_errors()

    def reset(self):
        """
        Reset the DLP controler.

        Returns
        -------
        None.

        """
        self.usb_command('w', 0x00, 0x02, 0x00, [int('00000010', 2)])
        self.read_reply()

    def test_read(self):
        """
        Test read operation. Testing to receive data from the DLP controler.

        Returns
        -------
        None.

        """
        self.usb_command('r', 0xff, 0x11, 0x00, [])
        self.read_reply()

    def test_write(self):
        """
        Test write operation. Testing to send data to the DLP controler.

        Returns
        -------
        None.

        """
        self.usb_command('w', 0x22, 0x11, 0x00,
                         [0xff, 0x01, 0xff, 0x01, 0xff, 0x01])
        self.check_for_errors()

    def change_mode(self, mode):
        """
        Select the operating mode of the DLP controler.

        Changes the dmd operating mode:
            mode=0 for normal video mode
            mode=1 for pre stored pattern mode
            mode=2 for video pattern mode
            mode=3 for pattern on the fly mode

        Parameters
        ----------
        mode : int
            The operating mode.

        Returns
        -------
        None.

        """
        self.usb_command('w', 0x00, 0x1a, 0x1b, [mode])
        self.check_for_errors()

    def start_sequence(self):
        """
        Start a image sequence.

        Returns
        -------
        None.

        """
        self.usb_command('w', 0x00, 0x1a, 0x24, [2])
        self.check_for_errors()

    def pause_sequence(self):
        """
        Pause current displayed sequence.

        Returns
        -------
        None.

        """
        self.usb_command('w', 0x00, 0x1a, 0x24, [1])
        self.check_for_errors()

    def stop_sequence(self):
        """
        Stop current displayed sequence.

        Returns
        -------
        None.

        """
        self.usb_command('w', 0x00, 0x1a, 0x24, [0])
        self.check_for_errors()

    def configure_lut(self, image_number, repetition_number):
        """
        Configure the LUT (Look Up Table) of the controler.

        For the Pattern On-The-Fly mode. The bit depth of the images has to be
        inserted here.

        Parameters
        ----------
        image_number : int
            Number of images of a image sequence.
        repetition_number : int
            Number, how often a image seqence has to be repeated.

        Returns
        -------
        None.

        """
        img = convert_num_to_bit_string(image_number, 11)
        repeat = convert_num_to_bit_string(repetition_number, 32)

        string = repeat + '00000' + img

        bytes = bits_to_bytes(string)

        self.usb_command('w', 0x00, 0x1a, 0x31, bytes)
        self.check_for_errors()

    def define_pattern(self, index, exposure, bit_depth, color, trigger_in,
                       dark_time, trigger_out, pat_ind, bit_pos):
        """
        Define a pattern that has to be displayed.

        Parameters
        ----------
        index : int
            Index from the image sequence to display.
        exposure : int numpy array
            Numpy array containing exposure time values in [us].
        bit_depth : int
            Bit depth of the images.
        color : str
            Color to display. Seems like it should be '111' for the blue
            color (UV Led).
        trigger_in : boolean numpy array
            Numpy array of boolean values determine wheter to wait for an
            external Trigger before exposure.
        dark_time : int numpy array
            Numpy array containing dark time values in [us].
        trigger_out : int
            Numpy array of boolean values determine wheter to wait for an
            external Trigger after exposure.
        pat_ind : int
            Pattern index?
        bit_pos : int
            Bit position?

        Returns
        -------
        None.

        """
        print('def pattern')
        payload = []
        index = convert_num_to_bit_string(index, 16)
        index = bits_to_bytes(index)
        for i in range(len(index)):
            payload.append(index[i])

        exposure = convert_num_to_bit_string(exposure, 24)
        exposure = bits_to_bytes(exposure)

        for i in range(len(exposure)):
            payload.append(exposure[i])

        options_byte = ''
        options_byte += '1'
        bit_depth = convert_num_to_bit_string(bit_depth - 1, 3)
        options_byte = bit_depth + options_byte
        options_byte = color + options_byte

        if trigger_in:
            options_byte = '1' + options_byte
        else:
            options_byte = '0' + options_byte

        payload.append(bits_to_bytes(options_byte)[0])

        dark_time = convert_num_to_bit_string(dark_time, 24)
        dark_time = bits_to_bytes(dark_time)

        for i in range(len(dark_time)):
            payload.append(dark_time[i])

        trigger_out = convert_num_to_bit_string(trigger_out, 8)
        trigger_out = bits_to_bytes(trigger_out)
        payload.append(trigger_out[0])

        pat_ind = convert_num_to_bit_string(pat_ind, 11)
        bit_pos = convert_num_to_bit_string(bit_pos, 5)
        last_bits = bit_pos + pat_ind
        last_bits = bits_to_bytes(last_bits)

        for i in range(len(last_bits)):
            payload.append(last_bits[i])
            
        self.usb_command('w', 0x00, 0x1a, 0x34, payload)
        self.check_for_errors()    
            
        return payload

    def set_bmp(self, index, size):
        """
        Send message to controler, that a .bmp will be uploaded.

        Not Sure about that.

        Parameters
        ----------
        index : int
            Current index of the image sequence.
        size : int
            Length of the image as bytes.

        Returns
        -------
        None.

        """
        payload = []

        index = convert_num_to_bit_string(index, 5)
        index = '0' * 11 + index
        index = bits_to_bytes(index)
        for i in range(len(index)):
            payload.append(index[i])

        total = convert_num_to_bit_string(size, 32)
        total = bits_to_bytes(total)
        for i in range(len(total)):
            #print('total=%d' %(total[i]))
            payload.append(total[i])

        #self.usb_command('w', 0x00, 0x1a, 0x2a, payload)
        self.usb_command('w', 0x00, 0x1a, 0x2a, payload)
        self.check_for_errors()

    def load_bmp(self, image, size, debug=True):
        """
        Upload a .bmp image.

        BMP loading function, divided in 56 bytes packages.
        Max  hid package size = 64, flag bytes = 4, usb command bytes = 2.
        Size of package description bytes = 2. 64 - 4 - 2 - 2 = 56.

        Parameters
        ----------
        image : str numpy array
            Numpy array representing the image. Bit depth 8. As bit string due
            to encoding beforehand.
        size : int
            Number of bytes of the image.
        debug : boolean, optional
            If True, than debug messages will be displayed in the console.
            The default is False.

        Returns
        -------
        None.

        """
        #t = time.clock()  # count time

        # print("Image Length: %d" % len(image))
        
        #print(len(image))
        #size += 1
        
        size = len(image)
        pack_num = int(size / 504 + 1)
        
        #print(size)
        #print(pack_num)

        counter = 0

        for i in range(pack_num):
            
            
            if i % 100 == 0:
                if debug:
                    print(i, pack_num)

            payload = []

            if i < pack_num - 1:
                leng = convert_num_to_bit_string(504, 16)
                bits = 504
            else:
                leng = convert_num_to_bit_string(size % 504, 16)
                bits = size % 504

            leng = bits_to_bytes(leng)

            for j in range(2):
                payload.append(leng[j])

            for j in range(bits):

                """
                This if statement blocks the index counter if it gets too
                big.
                """
                
                if counter < len(image):
                    payload.append(image[counter])

                counter += 1

            self.usb_command('w', 0x11, 0x1a, 0x2b, payload)
            self.check_for_errors()


    def define_sequence(self, images, exposure, trigger_in, dark_time,
                        trigger_out, repetition_number):
        """
        Define a sequence of images to display.

        Parameters
        ----------
        images : int numpy array
            Numpy array containing the image information. Bit depth is 8.
        exposure : int numpy array
            Exposure time values in a numpy array in [us].
        trigger_in : boolean numpy array
            Numpy array of boolean values determine wheter to wait for an
            external Trigger before exposure.
        dark_time : int numpy array
            Numpy array containing dark time values in [us]..
        trigger_out : boolean numpy array
            Numpy array of boolean values determine wheter to wait for an
            external Trigger after exposure..
        repetition_number : int
            Value defininf how often the image sequence is repeated. Set this
            value to 0 for an infinit loop.

        Returns
        -------
        None.

        """
        self.stop_sequence()

        arr = []

        for i in images:
            arr.append(i)  
            #arr.append(numpy.ones((1080,1920),dtype='uint8'))

        num = len(arr)

        encoded_images = []
        sizes = []

        for i in range(int((num - 1) / 24 + 1)):
            print('merging...')

            if i < ((num - 1) / 24):
                image_data = merge_images(arr[i * 24:(i + 1) * 24])
            else:
                image_data = merge_images(arr[i * 24:])

            print('encoding...')
            image_data, size = encode(image_data)

            encoded_images.append(image_data)
            sizes.append(size)

            if i < ((num - 1) / 24):
                for j in range(i * 24, (i + 1) * 24):
                    self.define_pattern(j, exposure[j], 8, '100',
                                        trigger_in[j], dark_time[j],
                                        trigger_out[j], i, j - i * 24)
            else:
                for j in range(i * 24, num):
                    self.define_pattern(j, exposure[j], 8, '100',
                                        trigger_in[j], dark_time[j],
                                        trigger_out[j], i, j - i * 24)

        self.configure_lut(num, repetition_number)

        for i in range(int((num - 1) / 24 + 1)):
            
            self.set_bmp(int((num - 1) / 24 - i),
                         sizes[int((num - 1) / 24 - i)])

            print('uploading...')

            """
            Seems like that the size index is too big. This results
            in a error in the bmpload() function.
            A if statement in the bmpload() function was implemented.
            This if statement blocks index, that is too long!
            """

            self.load_bmp(encoded_images[int((num - 1) / 24 - i)],
                          sizes[int((num - 1) / 24 - i)])
            
    def show_image_sequence_3(self, encoding, brightness, exposures, dark_times,
                              trigger_ins, trigger_outs, debug=False):
        
        
        
        
        # stop any already existing sequence
        self.stop_sequence()
        self.set_led_pwm(0)
        self.idle_off()
        self.change_mode(3)
        
        for index, enc in enumerate(encoding):
            
            for j in range(0,2,1):
                self.define_pattern(index, exposures[index], 8, '100',
                                        trigger_ins[index], dark_times[index],
                                        trigger_outs[index], j, j)
                
        
        for index, enc in enumerate(encoding):
            
            display_time = 0
            wait_time = 0
            
            if debug:
                print("- DEBUG PARAMETERS -")
                print("\n image Index %d " % index)
                print('\n current image settings:')
                print('\n brightness: %d' % brightness[index])
                print('\n exposure [us]: %d' % exposures[index] )
                print('\n dark time [us]: %d' % dark_times[index])
                print('\n trigger in: %s' %  trigger_ins[index])
                print('\n trigger out: %s' % trigger_outs[index])
                
            self.configure_lut(len(encoding), 1)
            
            self.set_bmp(0, len(enc))
            
            self.load_bmp(enc,len(enc))
            
            self.set_led_pwm(brightness[index])
            
            self.start_sequence()
            
            st = time.clock();
            
            while display_time <= exposures[index]:
                display_time = (time.clock()-st)*1e6
                #print(display_time)


            self.set_led_pwm(0)
            self.stop_sequence()
            
            start_time = time.process_time()*1e6
            
            if dark_times[index] > 0:
                while wait_time <= dark_times[index]:
                    wait_time = time.process_time()*1e6 - start_time
                    #print(wait_time)
            
            self.stop_sequence()
        
            start_time = time.process_time()*1e6
            
            while wait_time <= dark_times[index]:
                wait_time = time.process_time()*1e6 - start_time
            
            if debug:
                print("\n- DISPLAY IMAGE -")
                print('\ndisplay time: %f' %(display_time))
                print('\nwaited time [s]: %f' %(wait_time))
            
            print('\n')
        
        self.stop_sequence()
        self.set_led_pwm(0)

    def get_minimum_led_pattern_exposure(self):
        """
        This should get the minimum LED PWM value.

        Returns
        -------
        None.

        """
        self.usb_command('r', 0xff, 0x1A, 0x42, [])
        self.read_reply()

    def read_control_command(self):
        
        self.usb_command('r', 0xff, 0x00, 0x15, [])
        self.read_reply()
        
    def read_status(self):
        """
        Prints the current status in the console. Check the DLPC900 Programming
        Guide fro more detailed informations.
        https://www.ti.com/tool/DLPC900REF-SW#descriptionArea

        Returns
        -------
        None.

        """
        self.usb_command('r', 0xff, 0x00, 0x00, [])
        self.read_reply()
        
    def read_firmware(self):
        """
        Prints the current firmware in the console.
        Check the DLPC900 Programming
        Guide fro more detailed informations.
        https://www.ti.com/tool/DLPC900REF-SW#descriptionArea

        Returns
        -------
        None.

        """
        self.usb_command('r', 0xff, 0x02, 0x06, [])
        self.read_reply()
        
    def set_led_pwm(self, current_pwm, enable_disable='enable',
                    pwm_polarity='normal'):
        """
        Enables or Disables the blue LED and sets PWM value and PWM polarity.
        
        LED driver operation is a function of the individual red, green, and
        blue LED-enable software-control
        parameters. The recommended order for initializing LED drivers is to:
        1. Program the individual red, green, and blue LED driver currents.
        2. Program the LED PWM polarity.
        3. Enable the individual LED enable outputs.

        Parameters
        ----------
        current_pwm : int
            Is the PWM current value of the blue LED. This will affect the 
            duty cycle of the pwm modulated current through the blue LED.
            PWM value is in 8Bit 0...255 .
        enable_disable : str, optional
            Enables or disables the blue LED. To enable the blue led set to
            'enable'. To disbale set to 'disable'. The default is 'enable'.
        pwm_polarity : str, optional
            Is the PWM polarity of blue LED. If set to 'normal', then the
            lowest PWM current value is 0 and the highest is 255. If set to 
            'inverse', then the lowest PWM value is 255 and the highest is 0.
            The default is 'normal'.

        Returns
        -------
        None.
        """
        self.set_led_driver_current(current_pwm)
        self.set_led_pwm_polarity(pwm_polarity)
        self.enable_disable_blue_led(enable_disable)
    
    def enable_disable_blue_led(self, enable_disable):
        """
        Enables or disables the blue LED.
        
        Parameters
        ----------
        enable_disable : str, optional
            Enables or disables the blue LED. To enable the blue led set to
            'enable'. To disbale set to 'disable'. The default is 'enable'.
            
        Returns
        -------
        None.
        """
        if enable_disable == 'enable':
            payload = 0b00000100
        elif enable_disable == 'disable':
            payload = 0b00000000
        else:
            print('No valid input. Choose either "enable" or "disable".')
            
        self.usb_command('w', 0xff, 0x1A, 0x07, [payload])
        
    def set_led_pwm_polarity(self, pwm_polarity):
        """
        Set's the PWM polarity mode.

        Parameters
        ----------
        pwm_polarity : str, optional
            Is the PWM polarity of blue LED. If set to 'normal', then the
            lowest PWM current value is 0 and the highest is 255. If set to 
            'inverse', then the lowest PWM value is 255 and the highest is 0.
            The default is 'normal'.

        Returns
        -------
        None.
        """
        if pwm_polarity == 'normal':
            payload = 0b00
        elif pwm_polarity == 'invert':
            payload = 0b00
        else:
            print('No valid input. Choose either "normal" or "invert".')
            
        self.usb_command('w', 0xff, 0x1A, 0x05, [payload])
        
    def set_led_driver_current(self, current_pwm):
        """
        Set's the blue LED PWM current.

        Parameters
        ----------
        current_pwm : int
            Is the PWM current value of the blue LED. This will affect the 
            duty cycle of the pwm modulated current through the blue LED.
            PWM value is in 8Bit 0...255 .

        Returns
        -------
        None.

        """
        # in the following order: red, green, blue
        payload =  [0x00, 0x00, current_pwm]
        self.usb_command('w', 0xff, 0x0B, 0x01, payload)
        
    def long_axis_image_flip(self):
        """
        Flips an image alongs it's long axis. Call this method before an
        image is shown with the define_sequence method.

        Returns
        -------
        None.
        """
        payload = 0b00000001
        self.usb_command('w', 0xff, 0x10, 0x08, [payload])
        
    def short_axis_image_flip(self):
        """
        Flips an image alongs it's short axis. Call this method before an
        image is shown with the define_sequence method.

        Returns
        -------
        None.
        """
        payload = 0b00000001
        self.usb_command('w', 0xff, 0x10, 0x09, [payload])
        
    def dmd_park(self):
        """
        Put's the DMD mirrors in a parking position, therefore not so much
        light can enter the optics. Therefore no image is displayed. Always
        make sure, before sending the DMD park command, that no sequence is
        running. Also when removing power from the projector, please go into
        standby mode!

        Returns
        -------
        None.
        """
        self.stop_sequence()
        payload = 0b00000001
        self.usb_command('w', 0xff, 0x06, 0x09, [payload])
        
    def dmd_unpark(self):
        """
        Unparks the DMD mirrors.

        Returns
        -------
        None.

        """
        payload = 0b00000000
        self.usb_command('w', 0xff, 0x06, 0x09, [payload])
        
    def set_gpio_channels_pwm(self):
        """
        DLPC900 provides four general-purpose PWM channels that can be used
        for a variety of control applications, such as fan speed. If the PWM
        functionality is not needed, these signals can be programmed as
        GPIO pins. To enable the PWM signals:
        1. Program the PWM signal using the PWM Setup command.
        2. Enable the PWM signal with the PWM Enable command.

        Returns
        -------
        None.

        """
        # TODO
        self.usb_command('r', 0xff, 0x1A, 0x11, [])
        self.read_reply()
        
    def get_hardware_status(self):
        """
        Reads the current hardware status of the DLPC900 and prints it in the
        console. Check the DLPC900 Programming
        Guide fro more detailed informations.
        https://www.ti.com/tool/DLPC900REF-SW#descriptionArea

        Returns
        -------
        None.

        """
        self.usb_command('r', 0xff, 0x1A, 0x0A, [])
        self.read_reply()
    
    def get_system_status(self):
        """
        Reads the current system status of the DLPC900 and prints it in the 
        console. Check the DLPC900 Programming
        Guide fro more detailed informations.
        https://www.ti.com/tool/DLPC900REF-SW#descriptionArea

        Returns
        -------
        None.

        """
        self.usb_command('r', 0xff, 0x1A, 0x0B, [])
        self.read_reply()
    
    def get_main_status(self):
        """
        Reads the main status of the DLPC900 controller and prilnts it in the 
        console. Check the DLPC900 Programming
        Guide fro more detailed informations.
        https://www.ti.com/tool/DLPC900REF-SW#descriptionArea

        Returns
        -------
        None.

        """
        self.usb_command('r', 0xff, 0x1A, 0x0C, [])
        self.read_reply()
        
    
        
class PycrafterGUI():
    
    def __init__(self):
        """
        Initializing the Pycrafter GUI class, which also starts the Pycraffter 
        GUI.

        Returns
        -------
        None.

        """
        
        try:
            # create a DMD class object
            self.dlp = DMD()
            # send wakeup to controller
            self.dlp.wake_up()
            #time.sleep(1)
            # set to idle mode to preserve DMD lifetime
            #self.dlp.idle_on()
            #set led to 0
            self.set_led_pwm(0)
            # change to pattern on the fly mode
            self.dlp.change_mode(3)
        except:
            print('No usb connection to projector at start up.')
        
        
        # the parameters for the imagae sequences
        self.image_file_name_list = []
        self.sequence_param_file_name = "empty"
        self.images = []
        self.parameters = []
        self.image_names = []
        self.image_index = []
        self.image_brightness = []
        self.image_exposure = []
        self.image_dark_time = []
        self.image_trigger_in = []
        self.image_trigger_out = []
        self.encoded = []
        self.sequence_data = []
        
        # variables for the gui logic
        self.is_data_loaded = False
        self.is_idle = False
        self.is_encoded = False
        self.is_matlab_encoded = False
        
        # tkinter settings
        self.windowDimension = "200x200"
        self.Gui = tk.Tk()
        self.Gui.title("PycrafterGUI")
        self.Gui.geometry(self.windowDimension)
        
        # run startup functions and gui loop
        self.Gui.update_idletasks()
        self.create_widgets()
        self.gui_logic()
        self.Gui.mainloop()
        
        # write a function that pings the projector in a time intervall, which
        # prevents the usb connection from falling asleep
        # let it runs in a seperate process
        #self.keep_dlp_awake()
        
    def create_widgets(self):
        """
        Creates the widgets of the pycrafter gui.

        Returns
        -------
        None.

        """
        
        # button for selecting image folder
        self.select_sequence_folder_button = tk.Button(master=self.Gui,
                                                       text="Select Image Folder",
                        command=self.select_sequence_folder,
                        background="blue")
        self.select_sequence_folder_button.grid(column=1, row=1)
        
         # button for encoding a image sequence
        self.encode_image_sequence_button = tk.Button(master=self.Gui,
                                                      text="Encode Python",
                       command=self.encoding_image_sequence,
                       background="red")
        self.encode_image_sequence_button.grid(column=1, row=2)
        
         # button for enable disable idle mode of the projector
        self.encode_matlab_button = tk.Button(master=self.Gui,
                                                       text="Encode MATLAB",
                        command=self.encode_matlab,
                        background="green")
        self.encode_matlab_button.grid(column=1, row=3)
        
        # button for starting a sequence
        self.start_image_sequence_button = tk.Button(master=self.Gui,
                                                       text="Start Image Sequence",
                        command=self.start_image_sequence,
                        background="red")
        self.start_image_sequence_button.grid(column=1, row=4)
        
        # button for enable disable idle mode of the projector
        self.activate_standby_button = tk.Button(master=self.Gui,
                                                       text="Activate Standby",
                        command=self.activate_standby,
                        background="green")
        self.activate_standby_button.grid(column=1, row=5)
        
    def gui_logic(self):
        """
        This function runs the gui logic and enables or diables the needed 
        buttons.

        Returns
        -------
        None.

        """
        # controll the encode image sequence button
        if self.is_data_loaded == False or self.is_idle == True :
            self.encode_image_sequence_button.config(state='disabled', background='red')
        else:
            self.encode_image_sequence_button.config(state='normal', background='green')
            
        # controlls the start image sequence button
        if  self.is_matlab_encoded == False or self.is_idle == True or self.is_data_loaded == False:
            self.start_image_sequence_button.config(state='disabled', background='red')
        else:
            self.start_image_sequence_button.config(state='normal', background='green')
        
        # controlls the standby/awake button    
        if self.is_idle == False:
            self.activate_standby_button.config(background='green', text="Activate Standby")
        else:
            self.activate_standby_button.config(background='red', text="Wake Up")
            
        """    
        try:    
            self.dlp.test_read()
        except:
            print('No usb connection to projector.')
         """   
         
         # let this function run once every second
        self.Gui.after(1000, self.gui_logic)
        
    def keep_dlp_awake(self):
        """
        Function that pings the projector to keep the usb connection awake.

        Returns
        -------
        None.

        """
        pass
            
        
        
    def activate_standby(self):
        """
        Function that toggles the standby mode of the projector

        Returns
        -------
        None.

        """
        if self.is_idle == False:
            self.dlp.dmd_park()
            self.dlp.stand_by()
            self.is_idle = True
        else:
            self.dlp.wake_up()
            self.dlp.dmd_unpark()
            self.is_encoded = False
            self.is_idle = False
        

    def select_sequence_folder(self, debug=False):
        """
        Function that opens a dialog window in order to select the folder, that
        contains the images and sequence parameter .txt file.

        Parameters
        ----------
        debug : boolean, optional
            If True, than debug messages will be displayed in the console.
            The default is False.

        Returns
        -------
        None.

        """
        # open dialog window to select folder with images and sequence
        # parameter file
        self.sequence_folder_name = filedialog.askdirectory(initialdir = "./", 
                                          title = "Select Image Folder")
        if debug:
            print(self.sequence_folder_name)
            
        self.load_all_data()
            
        # calls function to load in parameter and image data
        #self.load_image_sequence_data(True)
        
    def load_all_data(self, debug=True):
        
        self.sequence_data = []
        
        file_name = self.sequence_folder_name + '/sequence_param.txt'
        
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
            self.sequence_data.append(splitted_line)
        
        # for each entry now load the image
        for index, line in enumerate(self.sequence_data):
            
            # image nam is always the first one
            image_name = line[0]
            
            # load in the images as a numpy array with datatype uint8
            try:
                image_data = numpy.asarray(
                    PIL.Image.open(self.sequence_folder_name + '/' + image_name),
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
            self.sequence_data[index].append(image_data)
            
            # plot the load images in the console
            fig = plt.figure()
            plt.imshow(image_data, cmap='gray')
            plt.colorbar()
            plt.show()

        # check if we have the encoded_images.txt, because it is not necessary
        files = os.listdir(self.sequence_folder_name)
        if 'encoded_images.txt' in files:
            self.is_matlab_encoded = True
            print('MATLAB Encoding was found.')
        else:
            self.is_matlab_encoded = False
            print('No MATLAB encoding was found.')
            
        # if the encoded data exists, we load them in a seperate array
        if self.is_matlab_encoded == True:
            
            # read in all lines
            file_name = self.sequence_folder_name + '/encoded_images.txt'
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
            if not len(encoded) == len(self.sequence_data) * 2:
                raise Exception('The number of encded image data found is not the' +
                                'same as the number of images found. ' +
                                '# images = %d' %(len(self.sequence_data)) + 
                                '# encoded images = %d'%(len(encoded)/2))
                
                    
            # now save the data in the sequence_data array to the corresponding image
            for index, line in enumerate(self.sequence_data):
                image_name = line[0]
                encoded_index = encoded.index(image_name)
                self.sequence_data[index].append(encoded[encoded_index+1])
                print(encoded[encoded_index])
                
        # soring function that reurns the index of a list in the sequence_data list
        def sort_index(element):
            return element[1]
        
        # now we can sort sequence_data according to the index of the images
        self.sequence_data.sort(reverse=False, key=sort_index)
        
        encoded_raw = []
        filtered_line= []
        
        self.is_data_loaded = True
        
        print(self.is_data_loaded)
        print(self.is_matlab_encoded)

    def encode_matlab(self):
        #works for mac
        #os.system('open ./encoding_gui.exe')
        # works for windoof, but not sure
        os.startfile('encoding_gui.exe')
        
                
    def encoding_image_sequence(self, debug=False):
        """
        Function that starts the encoding of the images and send the 
        information to the DLP900 chip.

        Parameters
        ----------
        debug : boolean, optional
             If True, than debug messages will be displayed in the console.
             The default is False.

        Returns
        -------
        None.

        """
        
        # reset lists from the dlp class for the encoded image data
        self.dlp.size_list = []
        self.dlp.encoded_images_list = []
        
        exposures = []
        dark_times = []
        trigger_ins = []
        trigger_outs = []
        images_sorted = []
        
        #n1 = numpy.zeros((1080,1920),dtype=float)
        #n2 = n1
        if debug:
            print('number of images to encode: %d' %(len(self.images)))
        
        # sort the images sequence according to the index numbers from the 
        # txt parameter file.
        for i, index in  enumerate(self.image_index):
            print('i=%d' %(i))
            print('indey=%d'%(index))
            # find all paramter entries for the needed index
            if i + 1 in self.image_index:
                im_index = self.image_index.index(i + 1)
                print(im_index)
                print(self.image_names[im_index]+ '\n')
                exposures.append( [self.image_exposure[im_index]] * 30 )
                dark_times.append( [self.image_dark_time[im_index]] * 30 )
                trigger_ins.append( [self.image_trigger_in[im_index]] * 30 )
                trigger_outs.append( [self.image_trigger_out[im_index]] * 30 )
                images_sorted.append(self.images[im_index])
                
        if debug:
            print(exposures)
            print(dark_times)
            print(trigger_ins)
            print(trigger_outs)
                
        # TODO: is it here needed
        # change to pattern on the fly mode just for safety
        self.dlp.idle_off()
        self.dlp.change_mode(3)
        
        print("\n- ENCODING IMAGES -")
               
        # take all sorted lists and encode them and send to DLP900
        for index, image in enumerate(images_sorted):
            print("\nencoding image %d" % index)
            print(exposures[index])
            print(dark_times[index])
            print(trigger_ins[index])
            print(trigger_outs[index])
            self.dlp.encoding_merging_image(image, exposures[index],
                                        trigger_ins[index], dark_times[index],
                                        trigger_outs[index], 1, True)
            
        # if successfull enable start of the sequence
        self.is_encoded = True
        
                
    def start_image_sequence(self, debug=False):
        """
        This function will start the image sequence.

        Parameters
        ----------
        debug : boolean, optional
             If True, than debug messages will be displayed in the console.
             The default is False.

        Returns
        -------
        None.

        """
        
        brightness= []
        encoded = []
        exposures = []
        dark_times = []
        trigger_ins = []
        trigger_outs = []
        image = []
        
        if self.is_matlab_encoded:
        
            # convert the sequence data in a format for the dlp
            for image_data in self.sequence_data:
                
                brightness.append(image_data[2])
                exposures.append(image_data[3])
                dark_times.append(image_data[4])
                trigger_ins.append(image_data[5])
                trigger_outs.append(image_data[6])
                image.append(image_data[7])
                encoded.append(image_data[8])

            self.dlp.show_image_sequence_3(encoded, brightness, 
                                 exposures,  dark_times, trigger_ins,
                                 trigger_outs, True) 
        
GUI = PycrafterGUI()