#!/usr/bin/env python3

# Test the decode functions with known values
from eletrobras_decode import decode_8bit, decode_16bit, decode_32bit

def test_8bit():
    print("Testing 8-bit decoding:")

    # Test with standard ASCII values
    test_cases = [
        (65, 'A'),   # ASCII 'A'
        (90, 'Z'),   # ASCII 'Z'
        (48, '0'),   # ASCII '0'
        (32, ' '),   # ASCII space
        (127, '\x7f'), # DEL character
        (128, '?'),  # Extended ASCII - should return '?'
        (255, '?'),  # Extended ASCII - should return '?'
    ]

    for byte_val, expected_char in test_cases:
        word, char = decode_8bit(byte_val)
        status = "✓" if char == expected_char else "✗"
        print(f"  {status} Input: {byte_val}, Word: {word}, Char: '{char}' (expected '{expected_char}')")

def test_16bit():
    print("\nTesting 16-bit decoding:")

    test_cases = [
        # (b1, b2, expected_word, expected_chars)
        (65, 66, 16961, 'AB'),      # Little-endian 'AB'
        (32, 33, 8480, ' !'),       # Space and exclamation
        (0, 127, 32512, '\x00\x7f'), # Null and DEL
        (255, 255, -1, '??'),       # All bits set (negative)
        (128, 200, -14208, '??'),   # Extended ASCII bytes
    ]

    for b1, b2, expected_word, expected_chars in test_cases:
        word, chars = decode_16bit(b1, b2)
        status = "✓" if word == expected_word and chars == expected_chars else "✗"
        print(f"  {status} Input: ({b1}, {b2}), Word: {word}, Chars: '{chars}' (expected {expected_word}, '{expected_chars}')")

def test_32bit():
    print("\nTesting 32-bit decoding:")

    test_cases = [
        # (b1, b2, b3, b4, expected_word, expected_chars)
        (65, 66, 67, 68, 1145258561, 'ABCD'),   # Little-endian 'ABCD'
        (48, 49, 50, 51, 858927408, '0123'),    # Digits
        (32, 33, 34, 35, 590162976, ' !"#'),    # Symbols
        (255, 255, 255, 255, -1, '????'),       # All bits set
        (128, 150, 200, 250, -100335744, '????'), # Extended ASCII
    ]

    for b1, b2, b3, b4, expected_word, expected_chars in test_cases:
        word, chars = decode_32bit(b1, b2, b3, b4)
        status = "✓" if word == expected_word and chars == expected_chars else "✗"
        print(f"  {status} Input: ({b1}, {b2}, {b3}, {b4}), Word: {word}, Chars: '{chars}' (expected {expected_word}, '{expected_chars}')")

def test_edge_cases():
    print("\nTesting edge cases:")

    # Test chr() error handling
    try:
        word, char = decode_8bit(0)
        print(f"  ✓ Null byte handled: Word: {word}, Char: '{repr(char)}'")
    except Exception as e:
        print(f"  ✗ Null byte failed: {e}")

    # Test signed integer conversion
    word, _ = decode_16bit(255, 255)
    print(f"  ✓ 16-bit signed conversion: 0xFFFF -> {word} (should be -1)")

    word, _ = decode_32bit(255, 255, 255, 255)
    print(f"  ✓ 32-bit signed conversion: 0xFFFFFFFF -> {word} (should be -1)")

if __name__ == "__main__":
    test_8bit()
    test_16bit()
    test_32bit()
    test_edge_cases()
