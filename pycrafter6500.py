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
import codecs


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

    print(size)

    total = convert_num_to_bit_string(size, 32)
    total = bits_to_bytes(total)
    for i in range(len(total)):
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
        self.dev.set_configuration()
        self.ans = []
        self.encoded_image = []

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
        print(bytes)

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
            payload.append(total[i])

        self.usb_command('w', 0x00, 0x1a, 0x2a, payload)
        self.check_for_errors()

    def load_bmp(self, image, size):
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

        Returns
        -------
        None.

        """
        t = time.clock()  # count time

        # print("Image Length: %d" % len(image))
        pack_num = size / 504 + 1

        counter = 0

        for i in range(int(pack_num)):
            if i % 100 == 0:
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
                # print("Counter: %d" % counter)
                # print(j)
            self.usb_command('w', 0x11, 0x1a, 0x2b, payload)

            self.check_for_errors()
        
        print(time.clock() - t)  # print time

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
            
            
            
    def show_image_sequence(self, images, brightness, exposures, dark_times,
                            trigger_ins,  trigger_outs):
        """
        Defines and start's a sequence of always a single image from a list of
        images.

        Parameters
        ----------
        images : list list numpy array
            A List containing list's each containing a single image 
            represented by a numpy array.
        brightness : list int
            A List containing the brightness value as the blue LED PWM current,
            for each picture. Must have the same length like images.
        exposure : list of list's of int
            A List of list's of each containing 30 entries with the same 
            value. Couldn't find a explanation for this data structure.
        dark_time : list list int
            List of list's each containing 30 entries with the same 
            value. Couldn't find a explanation for this data structure.
        trigger_in : list list bool
            List of list's each containing if a trigger in signal is 
            used or not represented as an boolean.
        trigger_out : list of list's of bool
            List of list's each containing if a trigger out signal is 
            used or not represented as an boolean.

        Returns
        -------
        None.

        """
        # minimum wait time in sec to have enough time for a single image to 
        # be displayed
        minimum_wait_time = 1

        # stop any already existing sequence
        self.stop_sequence()
        
        # change to pattern on the fly mode
        self.change_mode(3)
        
        for index, image in enumerate(images):
            print("image Index %d " % index)
            
            # stop any already existing sequence
            self.stop_sequence()
            
            #self.dmd_unpark()
            
            self.set_led_pwm(brightness[index])
            
            #self.long_axis_image_flip()
            #self.short_axis_image_flip()
            
            t = time.clock()
            # define sequence
            self.define_sequence(image, exposures[index], trigger_ins[index],
                                dark_times[index], trigger_outs[index], 1)
            print("upload time: %f" % t)
        
            # start sequence
            self.start_sequence()
            print("display image")
               
            # wait some time, therefore projector can finish displaying the image
            waiting_time = (exposures[index][0] +  dark_times[index][0]) / 1000000
            time.sleep(waiting_time + minimum_wait_time)
            
            self.set_led_pwm(0)
            #self.dmd_park()
            
        self.stop_sequence()
        self.set_led_pwm(0)
        
    def get_minimum_led_pattern_exposure(self):
         self.usb_command('r', 0xff, 0x1A, 0x42, [])
         self.read_reply()


    def read_control_command(self):
        self.usb_command('r', 0xff, 0x00, 0x15, [])
        self.read_reply()
        
    def read_status(self):
        """
        Prints the current status in teh console......??????

        Returns
        -------
        None.

        """
        self.usb_command('r', 0xff, 0x00, 0x00, [])
        self.read_reply()
        
    def read_firmware(self):
        """
        Prints the current firmware in the console.

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