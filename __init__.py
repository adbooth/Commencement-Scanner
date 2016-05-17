""" scanner/__init__.py
Runs scanner software
Authors: Andrew D. Booth, Seth M. Karas, Matthew T. Howard

A few TODOs throughout the code, along with the following:
 - Orientation might have a noticeable effect on decode time
 - We should definitely test different encoding levels

 Also, to kill python processes:
 $ sudo kill -9 $(ps ax | grep '[p]ython __init__.py' | awk '{print $1}')
 And for aplay processes:
 $ sudo kill -9 $(ps ax | grep '[a]play' | awk '{print $1}')
"""
import subprocess
from multiprocessing import Manager, Lock, Process
import os
import io
import time

import zbar
from PIL import Image
import picamera

from ScannerIO import ScannerIO as SIO


def capture(stack, stackLock):
    sio = SIO()
    print 'Capture thread started'
    with picamera.PiCamera(sensor_mode=7) as camera:                    # TODO: Decide which sensor mode is best
        if ENABLE_CAMERA_PREVIEW:
            camera.start_preview(fullscreen=False)
            camera.vflip = True
            camera.hflip = True
        while True:
            # Capture image
            stream = io.BytesIO()
            sio.statusGreen()
            camera.capture(stream, format='jpeg', quality=100, use_video_port=ENABLE_CAMERA_PREVIEW)    # TODO: Decide which quality is best
            sio.statusRed()
            # Add data to stack
            stackLock.acquire()
            stack.append(stream)
            # Trim stack
            stack.reverse()
            while len(stack) > STACK_SIZE:
                stack.pop()
            stack.reverse()
            stackLock.release()
            time.sleep(LOOP_SLEEP)


def scan(stack, queue, stackLock, queueLock):
    print 'Scan thread started'
    scanner = zbar.ImageScanner()
    scanner.parse_config('enable')
    previousData = None
    while True:
        # Get data off stack
        stackLock.acquire()
        if not stack:
            stackLock.release()
            continue
        stream = stack.pop()
        stackLock.release()
        # Analyze data
        stream.seek(0)
        pil = Image.open(stream).convert('L')
        width, height = pil.size
        raw = pil.tostring()
        image = zbar.Image(width, height, 'Y800', raw)
        result = scanner.scan(image)
        if result != 0:
            # Decode data
            for symbol in image: pass
            data = symbol.data.decode(u'utf-8')
            if data != previousData:
                previousData = data
                # Add data to queue
                queueLock.acquire()
                queue.put(data)
                queueLock.release()

        # Clean up
        stream.close()
        del image
        time.sleep(LOOP_SLEEP)


def say(queue, queueLock):
    print 'Say thread started'
    # Create student data structures
    presentNames = {filename.split('.')[0]: None for filename in os.listdir('namewavs')}
    walkedStudents = set()

    # Make hardware controller object
    sio = SIO()
    if LIGHTS_ON: sio.turnOn(SIO.WHITE)
    previousUbit = None
    while True:
        # Get ubit off queue
        queueLock.acquire()
        if queue.empty():
            queueLock.release()
            continue
        ubit = queue.get()
        # Trim queue
        while not queue.empty() and queue.get() == ubit: pass
        queueLock.release()

        # Ignore duplicates
        if ubit == previousUbit:
            continue
        previousUbit = ubit

        if ubit not in walkedStudents and ubit in presentNames:
            # Output audio
            subprocess.Popen('aplay %s -Dplug:default -r192000 namewavs/%s.wav' % ('-q' if SUPRESS_APLAY else '', ubit), shell=True)
            Process(target=sio.confirm()).start()
            walkedStudents.add(ubit)
        else:
            Process(target=sio.deny()).start()
        time.sleep(LOOP_SLEEP)


if __name__ == '__main__':
    SCAN_THREAD_COUNT = 3                                        # TODO: Decide on thread count (3 is pretty good, not too different from 1 or 2 though)
    STACK_SIZE = SCAN_THREAD_COUNT*2
    LOOP_SLEEP = 0.00                                        # TODO: Decide if sleep harms/benefits speed (no idea currently). These sleeps are in every loop
    SUPRESS_APLAY = False
    LIGHTS_ON = True                                        # TODO: Decide if lights harm/benefit decode (I think no effect)
    ENABLE_CAMERA_PREVIEW = True

    print 'Initializing audio...'
    primerThread = subprocess.Popen('audio_primer')
    subprocess.call(['amixer', 'cset', 'numid=3', '2'])

    # Thread data structures
    manager = Manager()
    stack = manager.list()
    queue = manager.Queue()
    stackLock = manager.Lock()
    queueLock = manager.Lock()

    print 'Starting threads...'
    captureThread = Process(target=capture, args=(stack, stackLock))
    captureThread.start()
    scanThreads = []
    for count in range(SCAN_THREAD_COUNT):
        print 'Spawn scan thread %d' % count
        thread = Process(target=scan, args=(stack, queue, stackLock, queueLock))
        thread.start()
        scanThreads.append(thread)
    sayThread = Process(target=say, args=(queue, queueLock))
    sayThread.start()

    raw_input('\n> HIT ENTER TO EXIT <\n\n')

    print 'Terminating threads...'
    sayThread.terminate()
    for thread in scanThreads:
        thread.terminate()
    captureThread.terminate()
    SIO().turnOff([SIO.WHITE, SIO.STATUS_GREEN, SIO.STATUS_RED])
    print 'Exiting...'
