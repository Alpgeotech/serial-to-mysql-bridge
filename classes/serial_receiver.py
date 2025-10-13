import time
import queue
import serial
import threading

import logging

logger = logging.getLogger(__name__)

class SerialReceiver:
    def __init__(self, serialSettingsDict):
        self.settings = serialSettingsDict
        self.__constructSerialConnection()
        self.__openSerialConnection()


    """
    This function configures the serial connection, using the
    settings in the dictionary supplied on initialization.
    The serial connection is not opened here.

    Args: 
        None
    Returns:
        ser: The configured serial connection as an object.
    """
    def __constructSerialConnection(self):
        ser = serial.serial_for_url(self.settings['port'], do_not_open=True)
        ser.baudrate = int(self.settings['baudrate'])
        ser.bytesize = int(self.settings['bytesize'])
        ser.parity = self.settings['parity']
        ser.stopbits = int(self.settings['stopbits'])
        ser.timeout = None
        return ser


    """
    This function opens the serial connection.
    After successfully opening the connection, __connectionState 
    is set to "up" and the callback function is executed.
    In case of an exception, the function sleeps, to limit 
    connection attempts to one per second.

    Args: 
        None
    Returns:
        None
    """
    def __openSerialConnection(self):
        try:
            self.ser = self.__constructSerialConnection()
            self.ser.open()
            self.__connectionState = "up"
            self.__scannerStateChangeCallback(self.__connectionState)
        except:
            self.__connectionState = "down"
            logging.debug("Connection to serial device could not be opened! Ignoring!")
            time.sleep(1)
            pass
 
    def read(self):
        try:
            return self.ser.readline().decode()
        except Exception as e:
            logger.error(f"Cannot read from serial device!")
            logger.error(e)
              
    def close(self):
        self.ser.close()
