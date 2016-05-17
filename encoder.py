""" scanner/encoder.py
Authors: Matthew T. Howard
"""
from qr import *
from os import listdir
import re
from os.path import isfile, join

mypath='namewavs'
onlyfiles = [f for f in listdir(mypath) if isfile(join(mypath, f))]
##onlyfiles = ["adbooth"]
for audio_file in onlyfiles:
    audio_file = re.sub(".wav", "", audio_file)
    filename = "qrs/" + audio_file + ".png"
    qrencode(audio_file,filename)
