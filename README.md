# Dew Point Fan Control

This project provides intelligent control of a fan based on the dew point. It utilizes a Wemos D1 mini with an ESP8266 microcontroller and is programmed in MicroPython. Two BME280 sensors, connected via the I2C protocol, provide the necessary temperature and humidity readings.  With MQTT connectivity, the fan can be easily controlled and monitored over a network.

**Key Features:**

* Dew point calculation using data from two BME280 sensors
* Automatic fan control
* MQTT integration for remote control and monitoring

**Benefits:**

* Efficient ventilation control to prevent mold growth
* Easy integration into existing smart home systems
* Convenient operation and monitoring via MQTT

**Getting Started**
To get this project running, you'll first need to install the following software:
1. esptool: For flashing the firmware to the microcontroller.
2. The appropriate firmware is available here.: https://micropython.org/download/ESP8266_GENERIC/
3. Copying the Files. You can transfer the files using any tool for copying files to the microcontroller, such as rshell, ampy, or Thonny.
4. Configuration the config.json file contains all the necessary settings for fan control and the MQTT connection. Adjust the values in this file to your needs.
