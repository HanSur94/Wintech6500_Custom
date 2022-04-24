# Wintech6500_Custom

This is a library for the Wintech PRO6500 Digital Light Processing (DLP) Engine for Python.
The Wintech6500 DLP Engine can be found here: https://www.wintechdigital.com/PRO6500 .

The original base library is the Pycrafter6500 lib (https://github.com/csi-dcsc/Pycrafter6500).
Some functionality and a more advanced documentation was aded to the Pycrafter6500 lib featuing
a simple Python TKinter GUI.

### Table of contents
* [Prerequisites](#prerequisites)
* [Installing](#installing)
* [Examples](#examples)

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

## Examples

The Wintech6500 can be controlled programmatically via the Digital Mirror Class (DMD) class or the Pycrafter GUI class.
The DMD library supports the following functions:

To connect and setup up a single exposure:


`self.dlp = DMD()
self.dlp.wake_up()
self.dlp.set_led_pwm(0)
self.dlp.change_mode(3)`



## Built With

* [MATLAB](https://www.mathworks.com/products/matlab.html) - Version R2019b

## Contributing

Please read [CONTRIBUTING.md](https://gist.github.com/PurpleBooth/b24679402957c63ec426) for details on our code of conduct, and the process for submitting pull requests to us.


## Authors

* **HanSur94** - [HanSur94](https://github.com/HanSur94)
