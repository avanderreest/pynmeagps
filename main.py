"""
nmeasocket.py

A simple example implementation of a GNSS socket reader
using the pynmeagps.NMEAReader iterator functions.

Created on 05 May 2022
@author: semu
"""
import sys

sys.path.append("src")

import socket
import json
from datetime import datetime
from pynmeagps.nmeareader import NMEAReader
from datetime import time
from datetime import date
import pynmeagps.nmeatypes_core as nmt  # so we can add talker device info to message
from pyais import decode  # decode AIS messages

# Set sentence to the first argument
# Set sentence to "!" if no argument is given
sentence = sys.argv[1] if len(sys.argv) > 1 else "!"


def decode_ais_message(sentence):
    decoded = None
    try:
        decoded = decode(sentence)
    except Exception as e:
        print(f"Error decoding sentence: {e}")

    if decoded is not None:
        return_json = decoded.to_json()
        return return_json
    else:
        return ""


# Call the decode_ais_message function with the sentence variable as input
# do if sentence is not "!"
if sentence != "!":
    decoded_message = decode_ais_message(sentence)
    # Print the decoded message to the console
    print(decoded_message)


SERVER = ""
PORT = 50120
# Set the broadcast IP and port
broadcast_ip = "255.255.255.255"
BROADCAST_PORT = 50121


def read(stream: socket.socket):
    """
    Reads and parses NMEA message from socket stream.
    """

    msgcount = 0
    start = datetime.now()

    nmr = NMEAReader(
        stream,
    )
    try:
        for _, parsed_data in nmr.iterate():
            print(parsed_data)
            msgcount += 1
    except KeyboardInterrupt:
        dur = datetime.now() - start
        secs = dur.seconds + dur.microseconds / 1e6
        print("Session terminated by user")
        print(
            f"{msgcount:,d} messages read in {secs:.2f} seconds:",
            f"{msgcount/secs:.2f} msgs per second",
        )


""" if sentence contains multiple messages, split them and parse them individually """


def print_fields(obj):
    json_obj = []
    for key, value in obj.__dict__.items():
        print(f"{key}: {value}")


def add_fields_to_json(obj, sentence):
    # prepare nmea message output to next module
    print_fields(obj)
    print("   ")
    json_obj = {}
    for key, value in obj.__dict__.items():
        if key not in ["_immutable", "_mode", "_hpnmeamode", "_payload", "_checksum"]:
            # case key is _talker_id then key = id or key is _msg_type then key = talker_type_id
            if key == "_talker":
                key = "id"  # key = "talker_id"
            if key == "_msgID":
                key = "talker_type_id"

            # if value is type time, convert to string
            if isinstance(value, time):
                value = value.strftime("%H:%M:%S.%f")
            if isinstance(value, date):
                value = value.strftime("%Y-%m-%d")

            json_obj[key] = value

    if obj._msgID in ["VDM", "VDO"]:
        print("AIS message")

        # Call the decode_ais_message function with dat variable as input
        # convert sentences string to binary string """
        # do if sentence is not "!" reverse the ! to $ ! is needed for PyAIS
        if sentence[0] == "$":
            sentence = "!" + sentence[1:]

        sentence_bytes = sentence.encode("utf-8")
        decoded_message = decode_ais_message(sentence_bytes)
        # Print the decoded message to the console
        print(decoded_message)

    # handle field talker_device
    if obj._talker in nmt.NMEA_TALKERS:
        value = nmt.NMEA_TALKERS[
            obj._talker
        ]  # get talker_type_desc from nmeatypes_core.py
    else:
        value = ""
    key = "talker_device"
    json_obj[key] = value  # add talker_device field to json_obj

    # handle field talker_type_desc
    if obj._msgID in nmt.NMEA_MSGIDS:
        # then the value of mnt.NMEA_MSGIDS[key] is value of talker_type_desc
        value = nmt.NMEA_MSGIDS[
            obj._msgID
        ]  # get talker_type_desc from nmeatypes_core.py
    else:
        value = ""
    key = "talker_type_desc"

    json_obj[key] = value  # add talker_type_desc field to json_obj

    return json_obj


def split_and_parse(sentence):
    sentences = sentence.split("\r\n")
    for s in sentences:
        if s != "":
            try:
                parsed_data = NMEAReader.parse(s)
                json_data = json.dumps(add_fields_to_json(parsed_data, sentence))

                # Create a UDP socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

                # Set the socket options to allow broadcasting
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

                # Send the JSON data over UDP to the broadcast IP and port
                sock.sendto(json_data.encode(), (broadcast_ip, BROADCAST_PORT))

                # Close the socket
                sock.close()

            except Exception as e:  # catch all exceptions
                print(f"Error handling data: {e}")


if __name__ == "__main__":
    print(f"Opening socket on port {PORT}...")
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.bind((SERVER, PORT))
        while True:
            data, addr = sock.recvfrom(1024)
            sentence = data.decode("utf-8")
            """ if first char of sentence is not $ replace char with $  this happens in case of VDM and VDO messages"""

            if sentence[0] != "$":
                sentence = (
                    "$" + sentence[1:]
                )  # replace ! with $ so validation check passes
            split_and_parse(sentence)
