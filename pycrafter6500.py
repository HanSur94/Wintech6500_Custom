import usb
import usb.core
import usb.util
import time
import numpy


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

    for i in range(4):  # black curtain
        bit_string.append(0x00)

    bit_string.append(0x00)

    bit_string.append(0x02)  # enhanced rle

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
    check_for_errors()
    read_reply()
    idle_on()
    idle_off()
    stand_by()
    wake_up()
    reset()
    test_read()
    test_write()
    change_mode()
    start_sequence()
    pause_sequence()
    stop_sequence()
    configure_lut()
    define_pattern()
    set_bmp()
    load_bmp()
    define_sequence()
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

    # standard usb command function

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

    ## functions for checking error reports in the dlp answer

    def checkforerrors(self):
        self.command('r', 0x22, 0x01, 0x00, [])
        if self.ans[6] != 0:
            print(self.ans[6])

        ## function printing all of the dlp answer

    def readreply(self):
        for i in self.ans:
            print(hex(i))

    ## functions for idle mode activation

    def idle_on(self):
        self.command('w', 0x00, 0x02, 0x01, [int('00000001', 2)])
        self.checkforerrors()

    def idle_off(self):
        self.command('w', 0x00, 0x02, 0x01, [int('00000000', 2)])
        self.checkforerrors()

    ## functions for power management

    def standby(self):
        self.command('w', 0x00, 0x02, 0x00, [int('00000001', 2)])
        self.checkforerrors()

    def wakeup(self):
        self.command('w', 0x00, 0x02, 0x00, [int('00000000', 2)])
        self.checkforerrors()

    def reset(self):
        self.command('w', 0x00, 0x02, 0x00, [int('00000010', 2)])
        self.checkforerrors()

    ## test write and read operations, as reported in the dlpc900 programmer's guide

    def testread(self):
        self.command('r', 0xff, 0x11, 0x00, [])
        self.readreply()

    def testwrite(self):
        self.command('w', 0x22, 0x11, 0x00,
                     [0xff, 0x01, 0xff, 0x01, 0xff, 0x01])
        self.checkforerrors()

    ## some self explaining functions

    def changemode(self, mode):
        self.command('w', 0x00, 0x1a, 0x1b, [mode])
        self.checkforerrors()

    def startsequence(self):
        self.command('w', 0x00, 0x1a, 0x24, [2])
        self.checkforerrors()

    def pausesequence(self):
        self.command('w', 0x00, 0x1a, 0x24, [1])
        self.checkforerrors()

    def stopsequence(self):
        self.command('w', 0x00, 0x1a, 0x24, [0])
        self.checkforerrors()

    def configurelut(self, imgnum, repeatnum):
        img = convert_num_to_bit_string(imgnum, 11)
        repeat = convert_num_to_bit_string(repeatnum, 32)

        string = repeat + '00000' + img

        bytes = bits_to_bytes(string)

        self.command('w', 0x00, 0x1a, 0x31, bytes)
        self.checkforerrors()

    def definepattern(self, index, exposure, bitdepth, color, triggerin,
                      darktime, triggerout, patind, bitpos):
        payload = []
        index = convert_num_to_bit_string(index, 16)
        index = bits_to_bytes(index)
        for i in range(len(index)):
            payload.append(index[i])

        exposure = convert_num_to_bit_string(exposure, 24)
        exposure = bits_to_bytes(exposure)
        for i in range(len(exposure)):
            payload.append(exposure[i])
        optionsbyte = ''
        optionsbyte += '1'
        bitdepth = convert_num_to_bit_string(bitdepth - 1, 3)
        optionsbyte = bitdepth + optionsbyte
        optionsbyte = color + optionsbyte
        if triggerin:
            optionsbyte = '1' + optionsbyte
        else:
            optionsbyte = '0' + optionsbyte

        payload.append(bits_to_bytes(optionsbyte)[0])

        darktime = convert_num_to_bit_string(darktime, 24)
        darktime = bits_to_bytes(darktime)
        for i in range(len(darktime)):
            payload.append(darktime[i])

        triggerout = convert_num_to_bit_string(triggerout, 8)
        triggerout = bits_to_bytes(triggerout)
        payload.append(triggerout[0])

        patind = convert_num_to_bit_string(patind, 11)
        bitpos = convert_num_to_bit_string(bitpos, 5)
        lastbits = bitpos + patind
        lastbits = bits_to_bytes(lastbits)
        for i in range(len(lastbits)):
            payload.append(lastbits[i])

        self.command('w', 0x00, 0x1a, 0x34, payload)
        self.checkforerrors()

    def setbmp(self, index, size):
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

        self.command('w', 0x00, 0x1a, 0x2a, payload)
        self.checkforerrors()

    ## bmp loading function, divided in 56 bytes packages
    ## max  hid package size=64, flag bytes=4, usb command bytes=2
    ## size of package description bytes=2. 64-4-2-2=56

    def bmpload(self, image, size):

        t = time.clock()

        print("Image Length: %d" % len(image))
        packnum = size / 504 + 1

        counter = 0

        for i in range(int(packnum)):
            if i % 100 == 0:
                print(i, packnum)
            payload = []
            if i < packnum - 1:
                leng = convert_num_to_bit_string(504, 16)
                bits = 504
            else:
                leng = convert_num_to_bit_string(size % 504, 16)
                bits = size % 504
            leng = bits_to_bytes(leng)
            for j in range(2):
                payload.append(leng[j])
            for j in range(bits):
                # print(j)

                """
                    This if statement blocks the index counter if it gets too
                    big
                """
                if counter < len(image):
                    payload.append(image[counter])
                counter += 1
                # print("Counter: %d" % counter)
            self.command('w', 0x11, 0x1a, 0x2b, payload)

            self.checkforerrors()
        print(time.clock() - t)

    def defsequence(self, images, exp, ti, dt, to, rep):

        self.stopsequence()

        arr = []

        for i in images:
            arr.append(i)

        ##        arr.append(numpy.ones((1080,1920),dtype='uint8'))

        num = len(arr)

        encodedimages = []
        sizes = []

        for i in range(int((num - 1) / 24 + 1)):
            print('merging...')
            if i < ((num - 1) / 24):
                imagedata = merge_images(arr[i * 24:(i + 1) * 24])
            else:
                imagedata = merge_images(arr[i * 24:])
            print('encoding...')
            imagedata, size = encode(imagedata)

            encodedimages.append(imagedata)
            sizes.append(size)

            if i < ((num - 1) / 24):
                for j in range(i * 24, (i + 1) * 24):
                    self.definepattern(j, exp[j], 1, '111', ti[j], dt[j],
                                       to[j], i, j - i * 24)
            else:
                for j in range(i * 24, num):
                    self.definepattern(j, exp[j], 1, '111', ti[j], dt[j],
                                       to[j], i, j - i * 24)

        self.configurelut(num, rep)

        for i in range(int((num - 1) / 24 + 1)):
            self.setbmp(int((num - 1) / 24 - i),
                        sizes[int((num - 1) / 24 - i)])

            print('uploading...')

            """
                Seems like that the size index is too big. This results
                in a error in the bmpload() function.
                A if statement in the bmpload() function was implemented.
                This if statement blocks index, that is too long!
            """
            self.bmpload(encodedimages[int((num - 1) / 24 - i)],
                         sizes[int((num - 1) / 24 - i)])
