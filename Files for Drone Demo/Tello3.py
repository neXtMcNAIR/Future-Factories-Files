import threading 
import socket
import sys
import time
import numpy as np
import cv2
from pyzbar.pyzbar import decode
import os
from PIL import Image

class Tello:

    def __init__(self, host='', port=9000, tello_ip='192.168.10.1', tello_port=8889):
        self.host = host
        self.port = port
        self.locaddr = (self.host, self.port) 

        # Create a UDP socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        self.tello_address = (tello_ip, tello_port)

        self.sock.bind(self.locaddr)

        #recvThread create
        self.recvThread = threading.Thread(target=self.recv)
        self.recvThread.start()

        self.coord = np.array((0, 0))
        self.in_flight = False
        self.transformed = False
        self.angle = 0
        self.new_angle = 0
        self.c, self.s = np.cos(self.angle), np.sin(self.angle)
        self.r_ccw = np.array(((self.c, -self.s), (self.s, self.c)))
        self.r_cw = np.array(((self.c, self.s), (-self.s, self.c)))
        self.x = 0
        self.y = 0

    def recv(self):
        while True: 
            try:
                self.data, self.server = self.sock.recvfrom(1518)
                print(self.data.decode(encoding="utf-8"))
            except Exception:
                break

    def command(self, cmd):
        self.sock.sendto(cmd.encode(encoding='utf-8'), self.tello_address)

# print ('Tello: command takeoff land flip forward back left right \r\n       up down cw ccw speed speed?\r\n')
# print ('end -- quit demo.\r\n')

class Frame:
    def __init__(self, frame='frame.png'):
        self.frame = frame
        self.label = None
        self.seen = []
        self.detectedbarcode = []

    def calculatePos(self):
        self.image = cv2.imread(self.frame)
        # self.array = np.load('array.npy')
        # self.image = Image.fromarray(self.array)
        
        try:
            self.detectedBarcode = decode(self.image)
        except:
            print("Problem with image")
            time.sleep(1)

        if self.detectedBarcode:
            for barcode in self.detectedBarcode:

                self.label = barcode.data.decode('utf-8')

                (self.x, self.y, self.w, self.h) = barcode.rect
                self.midx = self.x + self.w/2
                self.midy = self.y + self.h/2
                self.middiff = (self.midx - (self.width/2))/(self.width/2)

    def qrscanner(self):
        self.barcode_found = False
        self.image = cv2.imread(self.frame)
        # self.array = np.load('array.npy')
        # self.image = Image.fromarray(self.array)
        time.sleep(0.1)
        try:
            self.detectedBarcode = decode(self.image)
        except:
            print("Problem with image")
            try:
                cv2.imshow("frame.png")
            except:
                print(os.path.exists("frame.png"))
                print("Trouble loading the image")
            print(self.image)
            time.sleep(1)

        if self.detectedBarcode:
            for barcode in self.detectedBarcode:

                self.label = barcode.data.decode('utf-8')

                if self.label not in self.seen:
                    (self.x, self.y, self.w, self.h) = barcode.rect
                    cv2.rectangle(self.image, (self.x, self.y), (self.x+self.w, self.y+self.h), (255, 0, 0), 5)

                    self.midx = self.x + self.w/2
                    self.midy = self.y + self.h/2
                    self.area = self.w * self.h

                    self.width = self.image.shape[1]
                    self.height = self.image.shape[0]
                    self.frame_area = self.width * self.height
                    self.seen.append(self.label)
                    self.middiff = (self.midx - (self.width/2))/(self.width/2)
                    self.area_ratio = self.area/self.frame_area

                    print('Barcode detected')
                    time.sleep(2)
                    self.barcode_found = True

                    # cv2.imshow('Image', self.image)
                    # cv2.waitKey(1000)
                    # cv2.destroyAllWindows()

                else:
                    time.sleep(1)
                    pass
            
            self.detectedBarcode.clear()

        else:
            print('No barcode detected')
            time.sleep(2)
            self.barcode_found = False

drone = Tello()
frame = Frame()

#control loop below
def main():

    drone.command('speed 10')
    drone.command('takeoff')
    time.sleep(5)

    while True:
        try:
            drone.command('right 20')
            time.sleep(3)
            frame.qrscanner()
            if frame.barcode_found == True:
            
                #Centering drone about barcode
                if (frame.middiff < 0.16) and (frame.middiff > -0.16):
                    pass

                else:
                    while True:
                        if frame.label != 'R01':
                            if frame.area_ratio > 0.04:
                                drone.command('back 20')
                                time.sleep(2)
                            elif frame.area_ratio < 0.03:
                                drone.command('forward 20')
                                time.sleep(2)
                            else:
                                pass

                        if frame.middiff <= -0.16:
                            print(frame.x, frame.w)
                            print('Centering: Box middle: {0}, Frame middle: {1}'.format(frame.midx, frame.width/2))
                            drone.command('left 20')
                            time.sleep(4)
                            frame.calculatePos()
                        
                        elif frame.middiff >= 0.16:
                            print(frame.x, frame.w, frame.middiff)
                            print('Centering: Box middle: {0}, Frame middle: {1}'.format(frame.midx, frame.width/2))
                            drone.command('right 20')
                            time.sleep(4)
                            frame.calculatePos()

                        else:
                            break

                #Robot inspection vertical flight
                drone.command('up 40')
                time.sleep(2)
                drone.command('up 40')
                time.sleep(2)
                drone.command('up 40')
                time.sleep(2)
                drone.command('down 40')
                time.sleep(2)
                drone.command('down 40')
                time.sleep(2)
                drone.command('down 40')
                time.sleep(2)

            else:
                continue

            if frame.label == 'R04':
                break

        except KeyboardInterrupt:
            print('Emergency pilot control initiated.')
            try:
                while True:
                    print('Enter command:')
                    msg = input('')
                    if msg == 'end':
                        msg = msg.encode(encoding="utf-8") 
                        drone.sock.sendto(msg, drone.tello_address)
                        print('Normal flight sequence continued.')
                        break
                    else:
                        msg = msg.encode(encoding="utf-8") 
                        drone.sock.sendto(msg, drone.tello_address)

            except EOFError or KeyboardInterrupt:
                os.abort()

    print('Flight sequence over.')
    drone.command('land')
    drone.sock.close()

if __name__ == "__main__":
    main()

# while True: 

#     try:
        
#         image = cv2.imread('frame.png')
#         detectedBarcode = decode(image)

#         if len(detectedBarcode) != 0:
#             for barcode in detectedBarcode:
#                 (x, y, w, h) = barcode.rect
#                 cv2.rectangle(image, (x, y), (x+w, y+h), (255, 0, 0), 5)
                
#                 frame_width = image.shape[1]
#                 frame_height = image.shape[0]

#         cv2.imshow('Image', image)

#         cv2.waitKey(0)
#         cv2.destroyAllWindows()

#         time.sleep(2)

        #msg = input("")

        # if not msg:
        #     break

        # if 'end' in msg:
        #     print ('...')
        #     drone.sock.close()  
        #     break

        # if msg == 'takeoff':
        #     if drone.in_flight == False:
        #         drone.altitude = 50
        #         drone.in_flight = True

        # if 'ccw' in msg and drone.in_flight == True:
        #     ang = ''
        #     for char in range(len(msg)-4,len(msg)-1):
        #         ang += msg[char]
        #     angle = int(ang)
        #     drone.angle = np.radians(angle)
        #     drone.new_angle += drone.angle
        #     drone.transformed = True

        #     drone.c, drone.s = np.cos(drone.angle), np.sin(drone.angle)
        #     drone.r_ccw = np.array(((drone.c, -drone.s), (drone.s, drone.c)))
        #     drone.coord = np.matmul(drone.r_ccw, drone.coord)

        #     drone.angle = 0

        # if 'cw' in msg and drone.in_flight == True:
        #     ang = ''
        #     for char in range(len(msg)-4,len(msg)-1):
        #         ang += msg[char]
        #     angle = int(ang)
        #     drone.angle = np.radians(angle)
        #     drone.new_angle -= drone.angle
        #     drone.transformed = True

        #     drone.c, drone.s = np.cos(drone.angle), np.sin(drone.angle)
        #     drone.r_cw = np.array(((drone.c, -drone.s), (drone.s, drone.c)))
        #     drone.coord = np.matmul(drone.r_ccw, drone.coord)

        #     drone.angle = 0

        # if 'forward' in msg:
        #     if drone.transformed == False:
        #         forw = ''
        #         for char in range(len(msg)-4,len(msg)-1):
        #             if msg[char].isdigit() == True:
        #                 forw += msg[char]
        #                 forward = int(forw)
        #         drone.coord[0] += forward

        # if 'back' in msg:
        #     if drone.transformed == False:
        #         forw = ''
        #         for char in range(len(msg)-4,len(msg)-1):
        #             if msg[char].isdigit() == True:
        #                 forw += msg[char]
        #                 forward = int(forw)
        #     drone.coord[1] += forward        
                
        # if 'x?' in msg:
        #     print(drone.coord[0])

        # if 'y?' in msg:
        #     print(drone.coord[1])

        # Send data
        # msg = msg.encode(encoding="utf-8") 
        # sent = drone.sock.sendto(msg, drone.tello_address)
    
    # except KeyboardInterrupt:
    #     print ('\n . . .\n')
    #     drone.sock.close()  
    #     break