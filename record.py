"""
System code to Record eight channel microphone array

Authors: Jordan Alwon @IHA, Jade Hochschule Oldenburg
Date: April 2021
License: Copyright (2021) Alwon. For full license text
    see Readme @ <TGMGit-Ref>
"""
from matrix_lite import led
from matrix_lite import gpio
from time import sleep
from threading import Thread
import pyaudio
import wave
import os

def init_pins():
    pins = [8,10,12]

    for pin in pins:
        gpio.setMode(pin,0) # 0 = input, 1 = output
        gpio.setFunction(pin,0) # 0 = digital, 1 = pwm

def set_static_color(color):
    led.set(color)

def set_decreasing_steps_color(color,time):
    step_time = time / led.length
    
    diodes = [color] * led.length
    led.set(diodes)
    for diode, _ in enumerate(diodes):
        sleep(step_time)
        diodes[diode] = 'black'
        led.set(diodes)

def get_pressed_button(stop_var=True):
    # loop until push button press and return button number
    while stop_var:
        # button 0 (front left)
        if gpio.getDigital(10):
            print('Button 0 pressed')
            return 0

        # button 1 (front right)
        if gpio.getDigital(8):
            print('Button 1 pressed')
            return 1

        # button 2 (side)
        if gpio.getDigital(12):
            print('Button 2 pressed')
            return 2

def state_standby():
    # set LED color to green
    set_static_color('green')
    
    return get_pressed_button()
    

def state_shutdown():
    t = Thread(target=set_decreasing_steps_color, args=('red',10,))
    t.start()

    sleep(1)
    boo = True
    while boo:
        boo = t.is_alive()

        # button 0 (front left)
        if gpio.getDigital(10):
            boo = False
            print('Button 0 pressed')
            button = 0

        # button 1 (front right)
        if gpio.getDigital(8):
            boo = False
            print('Button 1 pressed')
            button = 1

        # button 2 (side)
        if gpio.getDigital(12):
            boo = False
            print('Button 2 pressed')
            button = 2
        
    if button == None:
        print('test')

def record():
    # recording configs
    CHUNK = 2048
    FORMAT = pyaudio.paInt16
    CHANNELS = 8
    RATE = 32000
    RECORD_SECONDS = 5
    WAVE_OUTPUT_FILENAME = "output.wav"

    # create & configure microphone
    mic = pyaudio.PyAudio()
    stream = mic.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)

    print("* recording")

    # read & store microphone data per frame read
    frames = []
    for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK)
        frames.append(data)

    print("* done recording")

    # kill the mic and recording
    stream.stop_stream()
    stream.close()
    mic.terminate()

    # combine & store all microphone data to output.wav file
    outputFile = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
    outputFile.setnchannels(CHANNELS)
    outputFile.setsampwidth(mic.get_sample_size(FORMAT))
    outputFile.setframerate(RATE)
    outputFile.writeframes(b''.join(frames))
    outputFile.close()

init_pins()

# while True:
pushed_button = state_standby()

if pushed_button == 0:
    state_shutdown()

elif pushed_button == 1:
    print("Recording")
    record()

elif pushed_button == 2:
    print("No Function")# Add Reboot key
else:
    raise KeyError

set_static_color('black')
    