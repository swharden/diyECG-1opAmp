# diyECG-1opAmp
A surprisingly good ECG is possible from a single op-amp. This project contains circuit and software.

* Project page: http://www.swharden.com/wp/2016-08-08-diy-ecg-with-1-op-amp/
* YouTube demo of project in action: https://www.youtube.com/watch?v=AfirWls9Sys

## Setup
This software needs certain libraries like PyQt4 and numpy, so the easiest way to make sure you have versions of everything that get along is to download a pre-packaged Python distribution. This software has been tested and works with WinPython 3.5.2.1 (not the Qt5 one)

* install [WinPython-64bit-3.5.2.1](https://sourceforge.net/projects/winpython/files/WinPython_3.5/3.5.2.1/) _(not the Qt5 one)_
* download this project and modify go.bat to reflect where your python.exe is
* build the circuit, plug it into your microphone hole, and run go.bat

## Demo Output
<img src="software/demo.png" width="500">

## Circuit
<img src="circuit/circuit.jpg" width="300">
<img src="circuit/design.jpg" width="300">
