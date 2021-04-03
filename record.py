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
from math import pi, cos

class Recorder():
    def __init__(self,
                filename='recording',
                record_length=5,
                sample_rate=16000,
                debug_mode=[]):

        self.filename = filename
        self.record_length = record_length
        self.sample_rate = sample_rate
        self.debug_mode = debug_mode

        self.path = os.path.join(os.path.dirname(os.path.realpath(__file__)),'Recordings')
        self.loop = True

        if not os.path.isdir(self.path):
            os.mkdir(self.path)

        self._init_pins()

    def _init_pins(self):
        # Initalize button pin connection
        pins = [8,10,12]

        for pin in pins:
            gpio.setMode(pin,0) # 0 = input, 1 = output
            gpio.setFunction(pin,0) # 0 = digital, 1 = pwm

    def _init_flash_memory(self):
        # Initalize the USB memory and update the file directory 
        pass

    def activate(self):
        # Loop operation procedure
        while self.loop:
            self.mode_standby()

        self._set_color_static('black')

    def mode_standby(self):
        # Standby: Waiting for button input
        self._set_color_static('green')

        pressed_button = self._get_button_input()

        if pressed_button == 0:
            self.mode_shutdown()

        elif pressed_button == 1:
            print("Recording")
            self.mode_record()

        elif pressed_button == 2:
            print("No Function")# Add Reboot key
        else:
            raise KeyError

    def mode_shutdown(self):
        # Shutdown progress. 
        t = Thread(target=self._set_color_decreasing_steps, args=('red',10,))
        t.start()

        sleep(1)
        boo = True
        while boo:
            boo = t.is_alive()

            # button 0 (front left)
            if gpio.getDigital(10):
                boo = False
                print('Button 0 pressed')
                
                # Shutdown pi function

            # button 1 (front right)
            if gpio.getDigital(8):
                boo = False
                print('Button 1 pressed')
                self.loop = False
                # Stop Shutdown process

            # button 2 (side)
            if gpio.getDigital(12):
                boo = False
                print('Button 2 pressed')
                self.loop = False
                # Stop Python script

        t.join()
            


    def mode_record(self):
        # Build record progress
        self._set_color_windmill_transition(color=(0,0,255,0))
        
        t = Thread(target=self._set_color_pulsating, args=((0,0,225,0), self.record_length+0.5,))
        t.start()

        self._record_audio()
        t.join()

    def _set_color_static(self, color):
        led.set(color)

    def _set_color_pulsating(self,color,time):
        
        sleep_len = 0.01
        freq = 0.4
        for x in range(int(time/sleep_len)):
            b = cos(pi/50*x*freq) * 0.4 + 0.4
            diodes = [(int(b*color[0]),int(b*color[1]),int(b*color[2]),int(b*color[3]))] * led.length
            led.set(diodes)
            sleep(sleep_len)            

    def _set_color_decreasing_steps(self,color,time):
        #
        step_time = time / led.length
        
        diodes = [color] * led.length
        led.set(diodes)
        for diode, _ in enumerate(diodes):
            sleep(step_time)
            diodes[diode] = 'black'
            led.set(diodes)

            if not self.loop:
                return

    def _set_color_windmill_transition(self, color):
        def linear_gradient(x, shift=0):
            y = (x-shift)/100
            if y < 0:
                y = 0
            elif y > 1:
                y = 1
            
            return y

        direction = ['fill','drain']
        
        diodes = ['black'] * led.length
        for step in range(60):
            sleep(1/60)

            g_1 = linear_gradient(step,0)
            g_2 = linear_gradient(step,10)
            g_3 = linear_gradient(step,20)
            g_4 = linear_gradient(step,30)
            g_5 = linear_gradient(step,40)

            c_1 = (int(g_1*color[0]), int(g_1*color[1]), int(g_1*color[2]), int(g_1*color[3]))
            c_2 = (int(g_2*color[0]), int(g_2*color[1]), int(g_2*color[2]), int(g_2*color[3]))
            c_3 = (int(g_3*color[0]), int(g_3*color[1]), int(g_3*color[2]), int(g_3*color[3]))
            c_4 = (int(g_4*color[0]), int(g_4*color[1]), int(g_4*color[2]), int(g_4*color[3]))
            c_5 = (int(g_5*color[0]), int(g_5*color[1]), int(g_5*color[2]), int(g_5*color[3]))

            diodes[0] = c_1
            diodes[5] = c_1
            diodes[9] = c_1
            diodes[14] = c_1

            diodes[1] = c_2
            diodes[6] = c_2
            diodes[10] = c_2
            diodes[15] = c_2

            diodes[2] = c_3
            diodes[7] = c_3
            diodes[11] = c_3
            diodes[16] = c_3
            
            diodes[3] = c_4
            diodes[8] = c_4
            diodes[12] = c_4
            diodes[17] = c_4

            diodes[4] = c_5
            diodes[13] = c_5
            
            led.set(diodes)

    def _get_button_input(self):
        # loop until push button press and return button number
        while True:
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

    def _set_filename_number(self):
        # recording_2.wav
        files = sorted(os.listdir(self.path))
        if len(files):
            number = int(files[-1].rsplit('.')[0].rsplit('_')[1]) + 1
        else:
            number = 0

        self.filename = f"recording_{number}.wav"

    def _record_audio(self):
        # recording configs
        chunk = 2048
        format = pyaudio.paInt16
        channels = 8
        self.sample_rate
        self.record_length

        self._set_filename_number()
        print(self.filename)
        # create & configure microphone
        mic = pyaudio.PyAudio()
        stream = mic.open(format=format,
                        channels=channels,
                        rate=self.sample_rate,
                        input=True,
                        frames_per_buffer=chunk)

        # read & store microphone data per frame read
        frames = []
        for i in range(0, int(self.sample_rate / chunk * self.record_length)):
            data = stream.read(chunk)
            frames.append(data)

        stream.stop_stream()
        stream.close()
        mic.terminate()

        print("save file")
        outputFile = wave.open(os.path.join(self.path, self.filename), 'wb')
        outputFile.setnchannels(channels)
        outputFile.setsampwidth(mic.get_sample_size(format))
        outputFile.setframerate(self.sample_rate)
        outputFile.writeframes(b''.join(frames))
        outputFile.close()

if __name__ == "__main__":
    r = Recorder()
    r.activate()        
