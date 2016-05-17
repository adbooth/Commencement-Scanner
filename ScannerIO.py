""" scanner.ScannerIO.py
Authors: Andrew D. Booth, Matthew T. Howard, Seth M. Karas
"""
import RPi.GPIO as io
from time import sleep


class ScannerIO:
    BUZZER          = 27
    WHITE           = 5
    GREEN           = 6
    RED             = 13
    STATUS_GREEN    = 26
    STATUS_RED      = 21

    def __init__(self, blinkTime=0.1, yellTime=0.3):
        self.blinkTime = blinkTime
        self.yellTime = yellTime
        io.setmode(io.BCM)
        io.setwarnings(False)
        for pin in [self.BUZZER, self.WHITE, self.GREEN, self.RED, self.STATUS_GREEN, self.STATUS_RED]:
            io.setup(pin, io.OUT)

    def deny(self):
        devices = [self.BUZZER, self.RED]
        self.turnOn(devices)
        sleep(self.yellTime)
        self.turnOff(devices)

    def confirm(self):
        devices = [self.BUZZER, self.GREEN]
        self.turnOn(devices)
        sleep(self.blinkTime)
        self.turnOff(devices)
        sleep(self.blinkTime)
        self.turnOn(devices)
        sleep(self.blinkTime)
        self.turnOff(devices)

    def statusGreen(self):
		self.turnOn(self.STATUS_GREEN)
		self.turnOff(self.STATUS_RED)

    def statusRed(self):
		self.turnOn(self.STATUS_RED)
		self.turnOff(self.STATUS_GREEN)

    def turnOn(self, devices):
        io.output(devices, io.HIGH)

    def turnOff(self, devices):
        io.output(devices, io.LOW)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.turnOff([self.BUZZER, self.WHITE, self.GREEN, self.RED,self.STATUS_GREEN, self.STATUS_RED])
        io.cleanup()
