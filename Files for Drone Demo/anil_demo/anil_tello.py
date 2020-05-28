import threading
import socket
import time
import sys
import os
import libh264decoder
import numpy as np

# host = ''
# port = 9000
# local_address = (host,port)

# sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# sock.bind(local_address)

# tello_address = ('192.168.10.1', 8889)

class Tello:

    def __init__(self, local_ip='', local_port=9000, command_timeout=0.3, tello_ip='192.168.10.1', tello_port=8889):
        self.decoder= libh264decoder.H264Decoder()
        self.command_timeout = command_timeout
        self.abort_flag = False
        self.response = None
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) #socket to send cmd
        self.socket_video = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) #socket to receive video
        self.tello_address = (tello_ip, tello_port)
        self.local_address = (local_ip, local_port)
        self.local_video_port = 11111 #port to receive video stream
        self.socket.bind((local_ip, local_port))

        self.frame = None
        self.is_freeze = False
        self.last_frame = None

        #default control variables
        self.distance = 0.1
        self.degree = 30

        #thread to receive cmd ack
        self.receive_thread = threading.Thread(target=self._receive_thread)
        self.receive_thread.daemon = True
        self.receive_thread.start()

        #start the SDK
        self.socket.sendto(b'command', self.tello_address)
        print('Sent: command')

        #commands to start streaming
        self.socket.sendto(b'streamon', self.tello_address)
        print('Sent: streamon')

        self.socket_video.bind((local_ip, self.local_video_port))

        #thread to receive video
        self.receive_video_thread = threading.Thread(target=self._receive_video_thread)
        self.receive_video_thread.daemon = True
        self.receive_video_thread.start()
        print('a')

    def __del__(self):
        self.socket.close()
        self.socket_video.close()

    def _receive_thread(self):
        while True:
            try:
                self.response, ip = self.socket.recvfrom(128)
                print(self.response)
            except socket.error as e:
                print('Socket error: {}'.format(e))
    
    def _receive_video_thread(self):
        packet_data = ''
        while True:
            try:
                print('1')
                self.socket_video.recvfrom(2048)
                print('2')
                res_string, ip = self.socket_video.recvfrom(2048)
                print('3')
                packet_data += res_string
                if len(res_string) != 1460:
                    print('2')
                    for frame in self._h264_decode(packet_data):
                        print('3')
                        self.frame = frame
              
                    packet_data = ''

            except socket.error as e:
                print('Socket error: {}'.format(e))

    def _h264_decode(self, packet_data):
        res_frame_list = []
        frames = self.decoder.decode(packet_data)
        for framedata in frames:
            (frame, w, h, ls) = framedata
            if frame is not None:
                # print 'frame size %i bytes, w %i, h %i, linesize %i' % (len(frame), w, h, ls)

                frame = np.fromstring(frame, dtype=np.ubyte, count=len(frame), sep='')
                frame = (frame.reshape((h, ls / 3, 3)))
                frame = frame[:, :w, :]
                res_frame_list.append(frame)

        return res_frame_list

    def read(self):
        if self.is_freeze:
            return self.last_frame
        else:
            return self.frame

    def send(self, message, delay):
        try:
            self.abort_flag = False
            self.socket.sendto(message.encode('utf-8'), self.tello_address)
            print("Sending message: " + message)

            timer = threading.Timer(self.command_timeout, self.set_abort_flag)
            
            timer.start()
            while self.response is None:
                if self.abort_flag == True:
                    break

            if self.response is None:
                response = 'none_response'
            else:
                response = self.response.decode('utf-8')

            self.response = None

            return response
                
        except Exception as e:
            print("Error sending: " + str(e))

    def set_abort_flag(self):
        self.abort_flag = True

    def takeoff(self):
        self.send('takeoff', 0)

    def set_speed(self, speed):
        speed = float(speed)
        self.send('speed {}'.format(speed), 0)

    def rotate_cw(self, degrees):
        self.send('cw {}'.format(degrees), 0)

    def rotate_ccw(self, degrees):
        self.send('ccw {}'.format(degrees), 0)

    def get_response(self):
        response = self.response
        return response

    def get_height(self):
        height = self.send('height?', 0)
        height = str(height)
        height = filter(str.isdigit, height)
        try:
            height = int(height)
            self.last_height = height
        except:
            height = self.last_height
            pass

        return height

    def get_battery(self):
        battery = self.send('battery?', 0)
        try:
            battery = int(battery)
        except:
            pass

        return battery

    def get_flight_time(self):
        flight_time = self.send('time?', 0)
        try:
            flight_time = int(flight_time)
        except:
            pass

        return flight_time

    def get_speed(self):
        speed = self.send('speed?', 0)
        try:
            speed = float(speed)
        except:
            pass

        return speed

    def land(self):
        self.send('land', 0)

    def move(self, direction, distance):
        distance = float(distance)
        
        self.send('{0} {1}'.format(direction, distance), 0)

    def move_backward(self, distance):
        self.move('back', distance)

    def move_down(self, distance):
        self.move('down', distance)

    def move_forward(self, distance):
        self.move('forward', distance)

    def move_left(self, distance):
        self.move('left', distance)

    def move_right(self, distance):
        self.move('right', distance)

    def move_up(self, distance):
        self.move('up', distance)

# def main():

#     startThread()

#     send('command', 3)
#     send('mon', 2)
#     send('mdirection 0', 2)

#     send('takeoff', 1)
#     send('go 0 0 0 10 m1', 1)

#     send('land', 5)

#     sock.close()

    # while True:

    #     cmd = input("")

    #     if cmd == 'end':
    #         sock.close()
    #         print('\nProgram ended.\n')
    #         break

