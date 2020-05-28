from PIL import Image
from PIL import ImageTk
import Tkinter as tki
from Tkinter import Toplevel, Scale
import threading
import datetime
import time
import cv2
import os
import sys
import numpy as np

class TelloUI:

    def __init__(self, tello):
        self.tello = tello
        self.frame = None
        self.thread = None
        self.stopEvent = None

        #control variables
        self.distance = 20
        self.degree = 30

        self.root = tki.Tk()
        self.panel = None

        self.stopEvent = threading.Event()
        self.thread = threading.Thread(target=self.videoLoop, args=())
        # self.video_thread = threading.Thread(target=self.videoLoop, args=())
        # self.video_thread.start()
        self.thread.start()
        
        self.number = 0

    def videoLoop(self):
        try:
            print('c')
            while not self.stopEvent.is_set():
                
                self.frame = self.tello.read()
                if self.frame is None or self.frame.size == 0:
                    continue

                image = Image.fromarray(self.frame)
                print('e')
                if self.number % 20 == 0:
                
                    #np.save(r'C:\Users\localadmin\Documents\Drone\array', self.frame)
                    image.save(r"C:\Users\localadmin\Documents\Drone\frame.png")

                self.number += 1

                self._updateGUIImage(image)

        except RuntimeError as e:
            print("Caught a RuntimeError.")

    # Display barcode and QR code location

    def display(self, im, bbox):
        n = len(bbox)
        for j in range(n):
            cv2.line(im, tuple(bbox[j][0]), tuple(bbox[ (j+1) % n][0]), (255,0,0), 3)
        # Display results
        cv2.imshow("Results", im)

    def _updateGUIImage(self, image):
        image = ImageTk.PhotoImage(image)
        if self.panel is None:
            self.panel = tki.Label(image=image)
            self.panel.image = image
            self.panel.pack(side="left", padx=10, pady=10)
        else:
            self.panel.configure(image=image)
            self.panel.image = image

    def _sendingCommand(self):
        while True:
            self.tello.send('command', 0)
            time.sleep(5)

    def _sendingJob(self):
        self.tello.send('command', 0)
        time.sleep(5) 
        self.tello.send('mon', 1)
        time.sleep(5)
        self.tello.send('mdirection 0', 1)
        time.sleep(5)
        while True:
            cmd = str(input(""))
            self.tello.send(cmd, 2)
        