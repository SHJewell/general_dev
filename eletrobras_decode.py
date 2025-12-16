#!/usr/bin/env python3
import sys
import struct
import numpy as np
import pyxtf
from dataclasses import dataclass


def decode_8bit(b):
    """Decode a single byte in 8-bit encoding."""
    # For standard ASCII, no offset needed
    word = b

    # Ensure the byte value is valid for ASCII (0-127)
    if 0 <= word <= 127:
        return word, chr(word)
    else:
        # For extended ASCII or invalid values, return the byte value and a replacement char
        return word, '?'

def decode_16bit(b1, b2):
    """Decode two bytes in 16-bit encoding."""
    # Little-endian: b1 is LSB, b2 is MSB
    word = (b2 << 8) + b1

    # check sign bit for signed 16-bit integer
    if word & 0x8000:  # If sign bit is set
        word = word - 0x10000  # Convert to negative

    # convert each byte to char, ensuring they're valid ASCII
    char1 = chr(b1) if 0 <= b1 <= 127 else '?'
    char2 = chr(b2) if 0 <= b2 <= 127 else '?'
    decode_str = char1 + char2

    return word, decode_str

def decode_32bit(b1, b2, b3, b4):
    """Decode four bytes in 32-bit encoding."""
    # Little-endian: b1 is LSB, b4 is MSB
    word = (b4 << 24) + (b3 << 16) + (b2 << 8) + b1

    # check sign bit for signed 32-bit integer
    if word & 0x80000000:  # If sign bit is set
        word = word - 0x100000000  # Convert to negative

    # convert each byte to char, ensuring they're valid ASCII
    char1 = chr(b1) if 0 <= b1 <= 127 else '?'
    char2 = chr(b2) if 0 <= b2 <= 127 else '?'
    char3 = chr(b3) if 0 <= b3 <= 127 else '?'
    char4 = chr(b4) if 0 <= b4 <= 127 else '?'
    decode_str = char1 + char2 + char3 + char4

    return word, decode_str

def read_file(fname):
    with open(fname, 'rb') as f:
        raw = f.read()

    # 1. Identify file type
    delim = raw[:8]

    print(delim.decode(errors='ignore'))

    b8_bytes = []
    b8_words = ""
    b16_bytes = []
    b16_words = ""
    b32_bytes = []
    b32_words = ""

    for n, byte_val in enumerate(raw):
        # Process 8-bit
        word_8, char_8 = decode_8bit(byte_val)
        b8_bytes.append((word_8, char_8))
        b8_words += char_8

        # Process 16-bit (every 2 bytes)
        if n % 2 == 1 and n > 0:  # Process on odd indices (we have a pair)
            word_16, chars_16 = decode_16bit(raw[n-1], raw[n])
            b16_bytes.append((word_16, chars_16))
            b16_words += chars_16

        # Process 32-bit (every 4 bytes)
        if n % 4 == 3 and n >= 3:  # Process on indices 3, 7, 11, etc.
            word_32, chars_32 = decode_32bit(raw[n-3], raw[n-2], raw[n-1], raw[n])
            b32_bytes.append((word_32, chars_32))
            b32_words += chars_32

    segments = raw.split(delim)

    decoded_segs = [seg.decode(encoding="UTF-8", errors='ignore') for seg in segments]

    if len(segments) > 3:
        payload = segments[3]
    else:
        payload = b''

    return b8_bytes, b16_bytes, b32_bytes, decoded_segs

def read_xtf(fname):

    (header, packets) = pyxtf.xtf_read(fname)

    return header, packets

def read_jsf(fname):
    # file:///C:/Users/scott/Downloads/Edgetech_jsf_rev1.13.pdf

    with open(fname, 'rb') as f:
        raw = f.read()

    decoded = raw.decode(encoding="UTF-8",  errors='ignore')

    header = {"marker": decode_16bit(raw[1], raw[0])[1],
              "version": decoded[2],
              "session_id": decoded[3],
              "message_type": decode_16bit(raw[5], raw[4])[1],
              "subsystem_number": decoded[7],
              "channel_number": decoded[8],
              "sequence_number": decoded[9],
              "reserved1": decoded[10:12],
              "size_of_message": decode_32bit(raw[15], raw[14], raw[13], raw[12])[0]
              }

    message = decoded[16:16+header["size_of_message"]]


    return raw


if __name__ == "__main__":
    # https://www.hydroffice.org/posts/hydrographic-formats/

    # fname = sys.argv[1]
    hfc_file = r"E:\JGS\Willowstick\Processing\ElectroBras Seismic\20250906_013239.HFC"
    lfc_file = r"E:\JGS\Willowstick\Processing\ElectroBras Seismic\20250906_013239.LFC"
    srp_file = r"E:\JGS\Willowstick\Processing\ElectroBras Seismic\20250906_013239.SRP"
    xtf_file = r"E:\JGS\Willowstick\Processing\ElectroBras Seismic\20250907104615H.xtf"

    # xtf_header, xtf_packets = read_xtf(xtf_file)
    # jsf_data = read_jsf(jsf_file)

    # ft, data = read_file(hfc_file)
