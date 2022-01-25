#!/usr/bin/env python3
import selectors
import socket
import struct
import threading
import time

from ethernet import *

start_time = 0

def frame_receive(target_mac, interface, client_socket):
  global start_time

  # Create a layer 2 raw socket that receives any Ethernet frames (= ETH_P_ALL)
  with selectors.DefaultSelector() as selector:
    # Resister the socket for selection, monitoring it for I/O events
    selector.register(client_socket.fileno(), selectors.EVENT_READ)
    while True:
      # Wait until the socket becomes readable
      ready = selector.select()
      if ready:
        # Receive a frame
        frame = client_socket.recv(ETH_FRAME_LEN)
        # Extract a header
        header = frame[:ETH_HLEN]
        payload = frame[ETH_HLEN:]
        # Unpack an Ethernet header in network byte order
        dst, src, proto = struct.unpack('!6s6sH', header)
        if target_mac == bytes_to_eui48(src):
          if payload[:len('Layer2_mac_address_echo_response!')] == 'Layer2_mac_address_echo_response!'.encode(): # signiture check
            # Extract a payload
            time_diff = time.time()- start_time
            print(f'dst: {bytes_to_eui48(dst)}, '
                    f'src: {bytes_to_eui48(src)}, '
                    f'type: 0x{proto:04x}, '
                    f'length: {len(payload)}, '      # Return_Layer2_pong!
                    f'payload: {payload[:len("Layer2_mac_address_echo_response!")]}, '
                    f'Time={(time_diff * 1000):.3g}msec'
                  )
            break   # only one frame is expected.

def frame_receive_from_all(interface: str, done: threading.Event):  # main is waiting: Event -> true
  global start_time
  recv_frame_number = 0
    # Create a layer 2 raw socket that receives any Ethernet frames (= ETH_P_ALL)
  with socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(ETH_P_ALL)) as client2_socket:
    # Bind the interface
    client2_socket.bind((interface, 0))
    with selectors.DefaultSelector() as selector:
      # Resister the socket for selection, monitoring it for I/O events
      selector.register(client2_socket.fileno(), selectors.EVENT_READ)
      done.set()  # threading.Event -> true, tell main that I am ready to receive.
      while True:
        # Wait until the socket becomes readable
        ready = selector.select()
        if ready:
          # Receive a frame
          frame = client2_socket.recv(ETH_FRAME_LEN)
          # Extract a header
          header = frame[:ETH_HLEN]
          payload = frame[ETH_HLEN:]
          # Unpack an Ethernet header in network byte order
          # print(header)
          dst, src, proto = struct.unpack('!6s6sH', header)
          if dst == get_hardware_address(interface):
            if payload[:len('Layer2_mac_address_echo_response!')] == 'Layer2_mac_address_echo_response!'.encode(): # signiture check
              # Extract a payload
              time_diff = time.time()- start_time
              recv_frame_number += 1
              print(f'dst: {bytes_to_eui48(dst)}, '
                      f'src: {bytes_to_eui48(src)}, '
                      f'type: 0x{proto:04x}, '
                      f'length: {len(payload)}, '      # Return_Layer2_pong!
                      f'payload: {payload[:len("Layer2_mac_address_echo_response!")]}, '
                      f'Time={(time_diff * 1000):.3g}msec, '
                      f'No.{recv_frame_number}'
                    )
