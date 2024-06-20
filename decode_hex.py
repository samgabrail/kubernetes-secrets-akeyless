import binascii
import base64
import json

# Convert hex to bytes
hex_data = input("Enter hex data: ")
byte_data = binascii.unhexlify(hex_data)

# Decode the bytes to a UTF-8 string
decoded_str = byte_data.decode('utf-8', 'ignore')

# Print the decoded string
print("Decoded string:")
print(decoded_str)
