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

Basic control of the Lightcrafter (modes selection, idle toggle,
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
import sys
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import filedialog
import matplotlib.pyplot as plt
import datetime

def convert_num_to_bit_string(number, length):
    """
    Convert a number into a bit string.

    Parameters:
    ----------
    number : int
        Number to convert
    length : int
        Number of bytes used to convert the number.

    Returns:
    -------
    bit_string : str
        String representing the number as bytes.

    """
    # return binary representation (string) of integer number
    bit_string = bin(number)[2:]
    padding = length - len(bit_string)
    bit_string = '0' * padding + bit_string

    return bit_string


def bits_to_bytes(bit_string):
    """
    Convert a bit string into a  bytes.

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
    Creates a 3D numpy array out of the 2D numpy array representing a image.

    Parameters
    ----------
    images : numpy array 2D
        A 2D numpy array with bit depth of 8 representing a image.

    Returns
    -------
    merged_image : numpy array 3D
        A 3D numpy array with bit depth of 8 representing a image.

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

    total = convert_num_to_bit_string(size, 32)
    total = bits_to_bytes(total)
    for i in range(len(total)):
        print(total)
        bit_string[i + 8] = total[i]

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
    show_image_sequence()
        Starts a image sequence.
    read_status()
        Prints the current status in the console.
    read_firmware()
        Prints the current firmware in the console.
    set_led_pwm()
        Enables or Disables the blue LED and sets PWM value and PWM polarity.
    enable_disable_blue_led()
        Enables or disables the blue LED.
    set_led_pwm_polarity()
        Set's the PWM polarity mode.
    set_led_driver_current()
        Set's the blue LED PWM current.
    long_axis_image_flip()
        Flips an image alongs it's long axis.
    short_axis_image_flip()
        Flips an image alongs it's short axis.
    dmd_park()
        Put's the DMD mirrors in a parking position.
    dmd_unpark()
        Unparks the DMD mirrors.
    get_hardware_status()
        Reads the current hardware status.
    get_system_status()
         Reads the current system status.
    get_main_status()
        Reads the main status.
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
            Command Byte 1.
        com2 : byte
            Command Byte 2.
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
        inserted here. This has to be called for each image.

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
        Define a pattern that has to be displayed. For 8 Bit greyscale images,
        call this function 3 times for each image and iterate over pattern 
        index and bit position

        Parameters
        ----------
        index : int
            Index from the image sequence to display.
        exposure : int numpy array
            Numpy array containing exposure time values in [us].
        bit_depth : int
            Bit depth of the images.
        color : str
            Color to display. Seems like it should be '100' for the blue
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
            Index in the pattern.
        bit_pos : int
            Bit position.

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
        Send message to controler, what .bmp (pattern index) will be uploaded
        and which size the encoded bitmap will have.

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
            payload.append(total[i])

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
        
        size = len(image)
        pack_num = int(size / 504 + 1)

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
            
    def show_image_sequence(self, encoding, brightness, exposures, dark_times,
                              trigger_ins, trigger_outs, debug=False):
        """
        Start imae sequence.

        Parameters
        ----------
        encoding : list
            List containing the encoded image data of each image.
        brightness : list
            List containing the broghtness data of each image.
        exposures : list
            List containing the exposure time in [us] of each image.
        dark_times : list
             List containing the dark time in [us] of each image.
        trigger_ins : list
            List containing if we use input trigger for each image.
        trigger_outs : list
            List containing if we use output trigger for each image.
        debug : str, optional
            Prints debug messages in the console. The default is False.

        Returns
        -------
        None.

        """
        
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
    """
    Pycrafter GUI class.


    Methods
    -------
    write_message()
        Writes a string in the console and in the GUI Listbox.
    update_progressbar()
         Controls the progressbar.
    create_widgets()
        Creates the widgets of the pycrafter gui.
    set_dark_mode()
        Sets visual darkmode of the GUI.
    gui_logic()
         Runs the gui logic. Enables & Disables widgets.
    on_closing()
        Show Dialog Window, before closing GUI.
    activate_standby()
        Toggles the standby mode of the projector.
    select_sequence_folder()
        Opens a dialog window in order to select a folder.
    load_all_data()
        Loads relevant data from the sequence_param.txt file & images.
    check_data()
        Checks that the loaded image sequence data is valid.
    encode_matlab()
        Starts the MATLAB encoding program.
    encode_python()
        Encodes images using the pycrafter encoding function. (slow)
    start_image_sequence()
        Start image sequence.
    """
    
    def __init__(self):
        """
        Initializing the Pycrafter GUI class, which also starts the Pycraffter 
        GUI.

        Returns
        -------
        None.

        """
        try:
            self.dlp = DMD()
            self.dlp.wake_up()
            self.dlp.set_led_pwm(0)
            self.dlp.change_mode(3)
            self.is_connected = True
        except:
            self.is_connected = False
            print('no connection')
        
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
        
        # gui darkmode style colour
        self.bg_cl = 'gray20'
        self.btn_bg_cl = 'gray30'
        self.btn_fg_cl = 'gray99'
        self.btn_bg_disabled_cl = 'gray50'
        self.btn_fg_disabled_cl = 'black'
        
        # to count for the listbox entries
        self.listbox_character_length = 115
        
        # variables for the gui logic
        self.is_data_loaded = False
        self.is_idle = False
        self.is_encoded = False
        #self.is_connected = False
        
        # tkinter settings
        self.windowDimension = "820x200"
        self.Gui = tk.Tk()
        self.Gui.title("PycrafterGUI")
        self.Gui.geometry(self.windowDimension)
        
        # run startup functions and gui loop
        self.Gui.update_idletasks()
        self.create_widgets()
        self.set_dark_mode()
        # write welcome message
        self.write_message('action','Hello and Welcome!')
        if self.is_connected == False:
            self.write_message('warning','No Connection to the DLP controler.'+
                               ' If nothing helps, try to hard reset DLP.')
        else:
            self.write_message('report',('Connection to the DLP controler' + 
                                          ' established.'))
        self.gui_logic()
        self.Gui.protocol("WM_DELETE_WINDOW",self.on_closing)
        self.Gui.mainloop()
        
    def write_message(self, message_type, message_string):
        """
        Writes a string in the console and in the GUI Listbox.
        
        Strings for the GUI Listbox will be formatted according to the message
        type. Use following Types: "warning" , "report", "action".
        Listbox text will be formatted according to:
            "warning"   ->  bg='red',   fg='white'
            "report"    ->  bg='green'  fg='white'
            "action"    ->  bg='dark'   fg='white'

        Parameters
        ----------
        message_type : str
            Type of the message. Chosse: "warning" , "report", "action".
        message_string : str
            String that will be printed in the GUI listbox & console.

        Returns
        -------
        None.
        
        """
 
        # Nested function
        def split_message_chunks(message_string):
            """
            Splits up message_string to fit in the lisbox.
            
            Chunk length is determined by a GUI property.

            Parameters
            ----------
            message_string : str
                String that will be printed in the GUI listbox & console.

            Returns
            -------
            message_chunks : list
                Splitted message strings.

            """
            step = self.listbox_character_length
            message_chunks = []
            
            for index in range(0, len(message_string),
                               self.listbox_character_length):
                # for specific interval append string in chunk
                message_chunks.append(message_string[index:step])
                step += self.listbox_character_length
                
            return message_chunks
        
        # get current timestamp
        self.currentDateTime = datetime.datetime.now()
        currentDateTimeString = self.currentDateTime.strftime("%d-%b-%Y "
                                                              "(%H:%M:%S)")
        message_string = currentDateTimeString + ':  ' + message_string
        
        # print unsplitted message string in console
        print(message_string)

        # depending on the message type, set background and font color
        if message_type == "warning":
            bgColor = 'red'
            textColor = 'white'
        elif message_type == "report":
            bgColor = 'green'
            textColor = 'white'
        elif message_type == "action":
            bgColor = self.btn_bg_cl
            textColor = self.btn_fg_cl
        else:
            bgColor = self.btn_bg_cl
            textColor = self.btn_fg_cl
            
        # call nested function to split message in chunks
        message_string = split_message_chunks(message_string)
        
        # format and display message string in listbox
        for message in message_string:
            self.message_listbox.insert(tk.END, message)
            self.message_listbox.itemconfig(tk.END, {'bg': bgColor})
            self.message_listbox.itemconfig(tk.END, {'fg': textColor})
            
        # refresh GUI
        self.Gui.update()
            
    def update_progressbar(self, current_step, maximum_step):
        """
        Controls the progressbar.

        Parameters
        ----------
        current_step : int, float
            Fraction value of the maximum_step to be displayed in the 
            progressbar.
        maximum_step : int, float
            Maximum value of the progress.

        Returns
        -------
        None.

        """
        # compute progress in %
        value = ((current_step+1)/maximum_step)*100
        # updatte progressbar with currewnt value
        self.progressbar['value'] = value
        self.Gui.update()
        if value == 100:
            time.sleep(0.5)
            self.progressbar['value'] = 0
            self.Gui.update()

    def create_widgets(self):
        """
        Creates the widgets of the pycrafter gui.

        Returns
        -------
        None.

        """
        
        # define grid size for window here
        self.Gui.rowconfigure(5,weight=1)
        self.Gui.columnconfigure(5,weight=1)
        
        # button for selecting image folder
        self.select_sequence_folder_button = tk.Button(master=self.Gui,
                                                   text="Select Image Folder",
                        command=self.select_sequence_folder)
        self.select_sequence_folder_button.grid(column=1, row=1)
        
         # button for encoding a image sequence
        self.encode_image_sequence_button = tk.Button(master=self.Gui,
                                                      text="Encode Python",
                       command=self.encode_python)
        self.encode_image_sequence_button.grid(column=1, row=2)
        
         # button for enable disable idle mode of the projector
        self.encode_matlab_button = tk.Button(master=self.Gui,
                                                       text="Encode MATLAB",
                        command=self.encode_matlab)
        self.encode_matlab_button.grid(column=1, row=3)
        
        # button for starting a sequence
        self.start_image_sequence_button = tk.Button(master=self.Gui,
                                                 text="Start Image Sequence",
                        command=self.start_image_sequence)
        self.start_image_sequence_button.grid(column=1, row=4)
        
        # button for enable disable idle mode of the projector
        self.activate_standby_button = tk.Button(master=self.Gui,
                                                 text="Activate Standby",
                        command=self.activate_standby,
                        background="green")
        self.activate_standby_button.grid(column=1, row=5)
        

        # scrollbar for the listbox
        self.listbox_scrollbar = tk.Scrollbar(master=self.Gui)
        self.listbox_scrollbar.grid(column=2, row=1, rowspan=4)
        
        # listbox for messages for debugging
        self.message_listbox = tk.Listbox(master=self.Gui,
                                  yscrollcommand=self.listbox_scrollbar.set)
        self.message_listbox.grid(column=3, row=1,columnspan=5, rowspan=4,
                                  sticky=tk.EW)
        
        self.listbox_scrollbar.config(command=self.message_listbox.yview)
        
        
        # add a progressbar
        self.progressbar = ttk.Progressbar(master=self.Gui,
                                           orient="horizontal",
                                           mode="determinate",
                                           maximum=100, value=0)
        self.progressbar.grid(column=3,row=5)

        
    def set_dark_mode(self):
        """
        Sets visual darkmode of the GUI.

        Returns
        -------
        None.

        """
        self.Gui.configure(background=self.bg_cl)
        
        self.select_sequence_folder_button.configure(
            bg=self.btn_bg_cl, fg=self.btn_fg_cl,)
        
        self.activate_standby_button.configure(
            bg=self.btn_bg_cl, fg=self.btn_fg_cl,)
        
        self.start_image_sequence_button.configure(
            bg=self.btn_bg_cl, fg=self.btn_fg_cl,)
        
        self.encode_matlab_button.configure(
            bg=self.btn_bg_cl, fg=self.btn_fg_cl,)
        
        self.encode_image_sequence_button.configure(
            bg=self.btn_bg_cl, fg=self.btn_fg_cl,)
        
        self.message_listbox.configure(bg=self.btn_bg_cl)
        
        
    def gui_logic(self):
        """
        Runs the gui logic. Enables & Disables widgets.

        Returns
        -------
        None.

        """
        # controll the encode image sequence button
        if self.is_data_loaded == False:
            self.encode_image_sequence_button.config(state='disabled',
                                                 bg=self.btn_bg_disabled_cl,
                                                 fg=self.btn_fg_cl)
        else:
            self.encode_image_sequence_button.config(state='normal',
                                                 bg=self.btn_bg_cl,
                                                 fg=self.btn_fg_cl)
            
        # controlls the start image sequence button
        if  self.is_encoded == False or self.is_idle == True or self.is_data_loaded == False:
            self.start_image_sequence_button.config(state='disabled',
                                    bg=self.btn_bg_disabled_cl,
                                    fg=self.btn_fg_cl)
        else:
            self.start_image_sequence_button.config(state='normal',
                                                    bg=self.btn_bg_disabled_cl,
                                                    fg=self.btn_fg_cl)
        
        # controlls the standby/awake button    
        if self.is_idle == False:
            self.activate_standby_button.config(background='green',
                                                text="Activate Standby")
        else:
            self.activate_standby_button.config(background='red',
                                                text="Wake Up")
            
        """    
        try:    
            self.dlp.test_read()
        except:
            print('No usb connection to projector.')
         """   
         
         # let this function run once every second
        self.Gui.after(100, self.gui_logic)
        
    def on_closing(self):
        """
        Show Dialog Window, before closing GUI.

        Returns
        -------
        None.

        """
        message_string = ('Do you want to quit?\n' +
                          'Please make sure, that you set Lightcrafter\n' +
                          'in Standby mode before closing the App!')
        if tk.messagebox.askokcancel("Quit", message_string):
            self.Gui.destroy()
        
    def activate_standby(self):
        """
        Toggles the standby mode of the projector. This function can be used
        to test the connectivity to the DLPC900 controler.

        Returns
        -------
        None.

        """
        try:
            if self.is_idle == False:
                # put mirrors in parking position for power cut off
                self.dlp.dmd_park()
                self.dlp.stand_by()
                self.is_idle = True
                self.write_message('report','DLP is now in standby mode.')
                self.is_connected = True
            else:
                self.dlp.wake_up()
                self.dlp.dmd_unpark()
                # set led to zero as fast as possible, can flash for some ms.
                self.dlp.set_led_pwm(0)
                # turn on pattern on the fly mode
                self.dlp.change_mode(3)
                self.is_encoded = False
                self.is_idle = False
                self.is_connected = True
                self.write_message('report','DLP is now awake.')
        except Exception as exception:
            self.write_message('warning', str(exception))
        

    def select_sequence_folder(self, debug=False):
        """
        Opens a dialog window in order to select the folder, that
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
        
        #check if user actually selected a folder
        if len(self.sequence_folder_name) == 0:
            message_string = ('No Image folder was selected.')
            self.write_message('action', message_string)
        else:
            self.load_all_data()
            
        # calls function to load in parameter and image data
        #self.load_image_sequence_data(True)
        
    def load_all_data(self, debug=True):
        """
        Loads relevant data from the sequence_param.txt file & images.

        Parameters
        ----------
        debug : TYPE, optional
            DESCRIPTION. The default is True.

        Raises
        ------
        Exception
            DESCRIPTION.

        Returns
        -------
        TYPE
            DESCRIPTION.

        """
        
        self.sequence_data = []
        
        # open and read file
        file_name = self.sequence_folder_name + '/sequence_param.txt'
        try:
            file = open(file_name, 'r')
            lines = file.readlines()
            file.close()
            self.write_message('report', 'Found sequence_param.txt file.')
        except Exception as exception:
            self.write_message('warning',str(exception))
            message_string = ('Make sure "sequence_param.txt" file does' + 
                              'exist in the specified folder.' + 
                              'Check file name spelling.')
            self.write_message('warning', message_string)
            self.is_data_loaded = False
            self.is_encoded = False
        
        filtered_line = []
        # filter out blank line and comments (lines with #)
        for line in lines:
            if not '#' in line:
                if not len(line) <= 3:
                    filtered_line.append(line)
                    
        # split the line with ; and put them in 2D matrix
        for line in filtered_line:
            splitted_line = line.split(';')
            
            # remove everything after 8th entry
            del splitted_line[8:len(splitted_line)]
            
            # save data in sequence data
            self.sequence_data.append(splitted_line)
        
        # for each entry now load the image
        for index, line in enumerate(self.sequence_data):
            
            # image nam is always the first one
            image_name = line[0]
            
            # load in the images as a numpy array with datatype uint8
            try:
                image_data = numpy.asarray(
                    PIL.Image.open(self.sequence_folder_name + '/' +
                                   image_name),
                    dtype=numpy.uint8)
            except Exception as exception:
                self.write_message('warning', str(exception))
                message_string = ('Image %s could not be found or loaded'%(image_name) + 
                                'Check that the image is existing or remove it' + 
                                'from the sequence_param.txt list.' )
                self.write_message('warning', message_string)
                self.is_data_loaded = False
                self.is_encoded = False
                
                
            # also check here that the image data is single matrix and does
            # not have multiple color channels!
            # also check that the images have the correct format
            if not image_data.shape == (1080, 1920):
                message_string = ('The size of the images you are using' + 
                                'is wrong. The images must be the in' + 
                                'the size of (1080,1920). Also they have' +
                                'to be 8 Bit grayscale images.')
                self.write_message('warning',message_string)
                #Exception(message_string)
                self.is_data_loaded = False
                self.is_encoded = False
            
            # append the image data at the 8th entry of the sequence data
            self.sequence_data[index].append(image_data)
            
            # plot the load images in the console
            plt.imshow(image_data, cmap='gray')
            plt.colorbar()
            plt.show()

        # check if we have the encoded_images.txt, because it is not necessary
        # to be in the folder right away.
        files = os.listdir(self.sequence_folder_name)
        if 'encoded_images.txt' in files:
            self.is_encoded = True
            self.write_message('report','Encoding was found.')
        else:
            self.is_encoded = False
            message_string = ('No encoding was found. You have to encode' + 
                              ' images using MATLAB or Python.' + 
                              ' MATLAB method is faster.')
            self.write_message('report',message_string)
            
        # if the encoded data exists, we load them in a seperate array
        if self.is_encoded == True:
            
            # read in all lines
            file_name = self.sequence_folder_name + '/encoded_images.txt'
            file = open(file_name, 'r')
            encoded_raw = file.readlines()
            file.close()
            encoded = []
        
            # iterate over each line, split up & filter elements
            for index in range(1, len(encoded_raw), 1):
                # even numbered elements is encoded data
                if index % 2 == 0:
                    enc_raw_splitted = encoded_raw[index].split(',')
                    enc_raw_filtered = []
                    
                    # filer -> only append elements that fit the condition
                    for element in enc_raw_splitted:
                        if not element == '' and \
                            not element == '\n' and \
                             not element == ' \n' and \
                              not element == ' ':
                                  enc_raw_filtered.append(element)
                            
                    encoded.append(list(map(int,enc_raw_filtered)))
                    
                # uneven numbered elements (image names)
                else:
                    image_name = encoded_raw[index].split(',')[0]
                    encoded.append(image_name)
                    
            # check here, that the number of encoded entries is double the 
            # number of images. It has to be double, since encodin data 
            # contains also the image names
            if not len(encoded) == len(self.sequence_data) * 2:
                message_string = ('The number of encded image data found is' + 
                                'not the same as the number of images found.'+
                                ' # images = %d' %(len(self.sequence_data)) + 
                                '# encoded images = %d'%(len(encoded)/2))
                self.write_message('warning', message_string)
                raise Exception(message_string)
                self.is_data_loaded = False
                self.is_encoded = False
                
            # now save the data in the sequence_data array to the 
            # corresponding image
            for index, line in enumerate(self.sequence_data):
                image_name = line[0]
                encoded_index = encoded.index(image_name)
                self.sequence_data[index].append(encoded[encoded_index+1])
                print(encoded[encoded_index])
                
        # soring function that reurns the index of a list in the sequence_data
        # list
        def sort_index(element):
            """
            Returns the index of a entry from the sequence data.

            Parameters
            ----------
            element : list
                List containing the image data. Comes from the sequence data.

            Returns
            -------
            int
                The element 1 of the list, which is the index of the image.

            """
            return element[1]
        
        # now we can sort sequence_data according to the index of the images
        self.sequence_data.sort(reverse=False, key=sort_index)
        
        # convert some data which is still a string to int 
        for index,image_data in enumerate(self.sequence_data):
            self.sequence_data[index][1] = int(image_data[1])
            self.sequence_data[index][2]  = int(image_data[2])
            self.sequence_data[index][3]  = int(image_data[3])
            self.sequence_data[index][4]  = int(image_data[4])
            self.sequence_data[index][5]  = int(image_data[5])
            self.sequence_data[index][6]  = int(image_data[6])
            self.sequence_data[index][7]  = int(image_data[7])
        
        encoded_raw = []
        filtered_line= []
        
        self.is_data_loaded = True
        self.write_message('report',('%d Images where loaded successfully.'
                                     %(len(self.sequence_data))))
        
    def check_data(self):
        """
        Checks that the loaded image sequence data is valid.

        Returns
        -------
        None.
        """
        pass
        
        
    def encode_matlab(self):
        """
        Starts the MATLAB encoding program.

        Returns
        -------
        None.

        """
        # depending on the used platform start MATLAB encoding app differently
        self.write_message('action',('Make sure you have the MATLAB runtime ' +
                                     'engine installed. Should work with' +
                                     ' version R2017b.'))
        if sys.platform == 'win32':
            # on windoof
            self.write_message('action','Start MATLAB Encoding App.')
            os.startfile('encoding_gui.exe')
        elif sys.platform == 'darwin':
            # on mac os
            self.write_message('action','Start MATLAB Encoding App.')
            os.system('open ./encoding_gui.app')
        else:
            self.write_message('warning',('Could not indetify the operating'+
                                          ' systsm. Use Mac or Windows.'))
        
    def encode_python(self):
        """
        Encodes images using the pycrafter encoding function. (slow)

        Returns
        -------
        None.

        """
        # clear existing encoded data
        self.encoded = []
        
        # write data in "encoded_images.txt" and overwrite everything
        file_name = self.sequence_folder_name + '/encoded_images.txt'
        file = open(file_name,'w')
        file.write('First Line will be ignored\n')
        file.close()
        
        message_string = ('Start Python Encodig, please wait a moment.')
        self.write_message('action', message_string)
        
        # get already saved images
        # call pycrafter encoding method for each image and save them in the
        # image sequence data array --> overwrite if existing
        for index, image_data in enumerate(self.sequence_data):
            
            # merge the image here
            image_data_merged = merge_images(image_data[8])
            
            # encode image here
            encoded_image, encoded_size = encode(image_data_merged)
            self.encoded.append(encoded_image)
            
            message_string = ('Encode image %d.'%(index))
            self.write_message('action',message_string)
    
            # append data in sequence data
            if len(self.sequence_data[index]) == 10:
                self.sequence_data[index][9] = encoded_image
            elif len(self.sequence_data[index]) == 9:
                self.sequence_data[index].append(encoded_image)
            
            # save all encoding in the encoded images file
            file = open(file_name,'a')
            # write the image name
            file.write(self.sequence_data[index][0])
            file.write(',')
            file.write('\n')
            # write encoding data
            for encoded_data in encoded_image:
                file.write(str(encoded_data) + ', ')
            file.write('\n')
            file.close()
            
            self.update_progressbar(index, len(self.sequence_data))
            
        self.is_encoded = True
        self.write_message('report','Finished encoding with Python.')
        
    def start_image_sequence(self, debug=True):
        """
        Start image sequence.

        Parameters
        ----------
        debug : boolean, optional
            Print debugging messages in the console. The default is True.

        Returns
        -------
        None.

        """
        
        # create seperate arrays with the image_data
        brightness= []
        encoded = []
        exposures = []
        dark_times = []
        trigger_ins = []
        trigger_outs = []
        bit_depths = []
        image = []
        
        # only start when image data was encoded
        if self.is_encoded:
            
            # convert the sequence data in a format for the dlp
            for image_data in self.sequence_data:
                brightness.append(image_data[2])
                exposures.append(image_data[3])
                dark_times.append(image_data[4])
                trigger_ins.append(image_data[5])
                trigger_outs.append(image_data[6])
                bit_depths.append(image_data[7])
                image.append(image_data[8])
                encoded.append(image_data[9])

            self.write_message('action', ('Start imaging process'+
                                          ' of %d images' %(len(encoded))))

            # stop any already existing sequence
            self.dlp.stop_sequence()
            self.dlp.set_led_pwm(0)
            self.dlp.idle_off()
            self.dlp.change_mode(3)
            
            for index, enc in enumerate(encoded):
                for j in range(0,2,1):
                    self.dlp.define_pattern(index, exposures[index],
                                            bit_depths[index],'100',
                                            trigger_ins[index],
                                            dark_times[index],
                                            trigger_outs[index], j, j)

            for index, enc in enumerate(encoded):
                
                display_time = 0
                wait_time = 0
                
                message_string = ('Image #%d with parameters; :'%(index) +
                                  'index: %d; ' %(index) +
                                  'brightness: %d; ' %(brightness[index]) +
                                  'exposure time : %d; ' %(exposures[index])+
                                  'dark time: %d; ' %(dark_times[index]) +
                                  'trigger in: %d; ' %(trigger_ins[index]) + 
                                  'trigger out: %d; ' %(trigger_outs[index]) )
                
                self.write_message('action',message_string)

                self.dlp.stop_sequence()

                # Here we configure the look up table of the DMD
                # We say, how many images we have and that every image is
                # repeated just once
                self.dlp.configure_lut(len(encoded), 1)
                
                # Tell the DMD the sub index of the image, and how many
                # bytes it has
                self.dlp.set_bmp(0, len(enc))
                
                # Here we upload the encoded image
                self.dlp.load_bmp(enc, len(enc))
                
                # Set the LED Brightness to the specific value
                self.dlp.set_led_pwm(brightness[index])
                
                # start to display the image
                self.dlp.start_sequence()
                
                # start the time clock
                st = time.clock();
                
                # wait until the exposure time is over
                while display_time <= exposures[index]:
                    display_time = (time.clock()-st)*1e6
    
                # turn off the led & stop the sequence
                self.dlp.set_led_pwm(0)
                self.dlp.stop_sequence()
                
                # get the new start time for the dark times to come
                st = time.clock();
                
                # wait until the dark time is over
                if dark_times[index] > 0:
                    while wait_time <= dark_times[index]:
                        wait_time = (time.clock()-st)*1e6

                if debug:
                    print("\n- DISPLAY IMAGE -")
                    print('\ndisplay time: %f' %(display_time))
                    print('\nwaited time [s]: %f' %(wait_time))
                    print('\n')
                
                message_string = ('Displayed the image %d; ' %(index) + 
                                  'Real Exposure Time: %d; ' %(display_time)+
                                  'Real Dark Time: %d; ' %(wait_time))
                
                self.write_message('action',message_string)
                self.update_progressbar(index, len(encoded))
            
            self.dlp.set_led_pwm(0)
            self.dlp.stop_sequence()

            message_string = ('Finished to display Image Sequence.')
            self.write_message('report', message_string)
        
        
GUI = PycrafterGUI()
sq = GUI.sequence_data
enc = GUI.encoded