""" scanner/qr.py
Authors: Matthew T. Howard, Andrew D. Booth
"""
from pyqrcode import create
from qrtools import QR
import qrcode

def qrencode(data, filename):
    create(data).png(filename, scale=6)


def qrdecode(filename):
    qr = QR()
    qr.decode(filename)
    return qr.data
