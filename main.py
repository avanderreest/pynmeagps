"""
nmeasocket.py

A simple example implementation of a GNSS socket reader
using the pynmeagps.NMEAReader iterator functions.

Created on 05 May 2022
@author: semu
"""

import socket
from datetime import datetime
from pynmeagps.nmeareader import NMEAReader


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
        for (_, parsed_data) in nmr.iterate():
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


def split_and_parse(sentence):
    sentences = sentence.split("\r\n")
    for s in sentences:
        if s != "":
            try:
                parsed_data = NMEAReader.parse(s)
                print(parsed_data)
            except Exception as e:  # catch all exceptions
                print(f"Error handling data: {e}")


if __name__ == "__main__":

    SERVER = ""
    PORT = 50120

    print(f"Opening socket on port {PORT}...")
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.bind((SERVER, PORT))
        while True:
            data, addr = sock.recvfrom(1024)
            sentence = data.decode("utf-8")
            """
            nmr = NMEAReader(sentence)
            parsed_data = nmr.parse()
            print(parsed_data)
            """

            split_and_parse(sentence)
