# Wintech6500_Custom

This is a library for the Wintech PRO6500 Digital Light Processing (DLP) Engine for Python.
The Wintech6500 DLP Engine can be found here: https://www.wintechdigital.com/PRO6500 .

The original base library is the Pycrafter6500 lib (https://github.com/csi-dcsc/Pycrafter6500).
Some functionality and a more advanced documentation was aded to the Pycrafter6500 lib featuing
a simple Python TKinter GUI.

### Table of contents
* [Prerequisites](#prerequisites)
* [Examples](#examples)
* [Built With](#built-with)
* [Contributing](#contributing)
* [Authors](#authors)

## Prerequisites

The library was written in Spyder in the Anaconda Environment.
For the usage of this library you will need the following Python modules:

1. usb.core
2. usb.util
3. time
4. numpy
5. PIL
6. os
7. sys
8. tkinter
9. matplotlib
10. datetime

The script requires Pyusb and Numpy to be present in your Python environment. The test script included requires the Python Image Library (PIL or pillow) for opening a test image. The device must have libusb drivers installed, for Windows users we suggest to install them through Zadig (http://zadig.akeo.ie/), and selecting the libusb_win32 driver.

## Examples

The Wintech6500 can be controlled programmatically via the Digital Mirror Class (DMD) class or the Pycrafter GUI class.
The DMD library supports the following functions:

To connect and setup up the system to a single exposure:

```python
self.dlp = DMD()
self.dlp.wake_up()
self.dlp.dmd_unpark()
self.dlp.set_led_pwm(0)
self.dlp.change_mode(3)
```
Set the DLP back int Standby mode:

```python
self.dlp.dmd_park()
self.dlp.stand_by()
```

Before a projection, the images must be encoded using the procedure described by Wintech6500 and texas Instruments.
Start a sequence of images to be projected:

```python
# stop any already existing sequence
self.dlp.stop_sequence()
self.dlp.set_led_pwm(0)
self.dlp.idle_off()
self.dlp.change_mode(3)

# Define Sequence from already encoded images with specified settngs
for index, enc in enumerate(encoded):
    for j in range(0,2,1):
        self.dlp.define_pattern(index, exposures[index],
                                bit_depths[index],'100',
                                trigger_ins[index],
                                dark_times[index],
                                trigger_outs[index], j, j)
                                
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

# turn off the led & stop the sequence
self.dlp.set_led_pwm(0)
self.dlp.stop_sequence()
```

You can also just call the Pycrafter GUI class in order to controll the Wintech6500 graphically:

```python
GUI = PycrafterGUI()

```

And the following GUI will appear:



## Built With

* [Anaconda](https:) - Version 2.0.3
* [Spyder](https:) - Version 5.1.5
* [Python](https:) - Version 3.8.5

## Contributing

Based on the Pycrafter6500 lib. Please visit the [Pycrafter6500](https://github.com/csi-dcsc/Pycrafter6500)
lib for further informations.


## Authors

* **HanSur94** - [HanSur94](https://github.com/HanSur94)
