"""Socket Assigment cosc264, Sam McMillan, 87685388, client"""

import socket
import sys


class Client:
    """This is a client, which sends a request packet for a time stamp to a server. It takes three parameters,
    request type is ether 'date' or 'time'. Ip address is the destination
    address for the request packet. port number is an int between 1024 and 64000 which the socket binds to."""

    def __init__(self, request_type, ip_address, port_number):
        if request_type not in ["date", "time"]:
            raise ValueError("Request type invalid")
        if 1024 > port_number > 640000:
            raise ValueError("Port number out of range")
        try:
            addr = socket.getaddrinfo(ip_address, port_number, socket.SOCK_DGRAM)
        except socket.error:
            raise ValueError("Invalid address")
        self.ip_address = addr[0][4]
        self.port_number = port_number
        self.request_type = request_type
        self.socket = None

    def open_socket(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.settimeout(1)
            self.socket.connect(self.ip_address)
        except socket.error:
            print("Connection failed")
            sys.exit()

    def prepare_packet(self):
        request_packet = bytearray(6)
        request_packet[0] = 0x49
        request_packet[1] = 0x7E
        request_packet[2] = 0x00
        request_packet[3] = 0x01
        request_packet[4] = 0x00
        if self.request_type == "date":
            request_packet[5] = 0x01
        if self.request_type == "time":
            request_packet[5] = 0x02
        return request_packet

    def send_packet(self, packet):
        try:
            self.socket.sendall(packet)
        except socket.error:
            print("Packet failed to send")
            self.socket.close()
            sys.exit()

    def get_response(self):
        try:
            return self.socket.recv(64)
        except socket.error:
            print("Request timed out")
            self.socket.close()
            sys.exit()

    def validate_response(self, response):
        magic_number = ((response[0] << 8) + response[1])
        packet_type = ((response[2] << 8) + response[3])
        language_code = ((response[4] << 8) + response[5])
        year = ((response[6] << 8) + response[7])
        month = response[8]
        day = response[9]
        hour = response[10]
        minute = response[11]
        length = response[12]
        text_field = response[13:].decode("UTF-8")
        if magic_number != 0x497E:
            print("Incorrect magic number")
            self.socket.close()
            sys.exit()
        if packet_type != 0x0002:
            print("Incorrect packet type number")
            self.socket.close()
            sys.exit()
        if language_code not in [0x0001, 0x0002, 0x0003]:
            print("Incorrect language code")
            self.socket.close()
            sys.exit()
        if year > 2100:
            print("Year number out of bound")
            self.socket.close()
            sys.exit()
        if 1 < month > 12:
            print("Month number out of bound")
            self.socket.close()
            sys.exit()

        if 1 < day > 31:
            print("day number out of bound")
            self.socket.close()
            sys.exit()
        if 0 < hour > 23:
            print("hour number out of bound")
            self.socket.close()
            sys.exit()
        if 1 < minute > 60:
            print("minute number out of bound")
            self.socket.close()
            sys.exit()
        if (13 + length) != len(response):
            print("Packet length is invalid")
            self.socket.close()
            sys.exit()
        print(f"Magic number is {format(magic_number, 'x').upper()}")
        print(f"Packet type is {format(packet_type, '04x').upper()}")
        print(f"Language code is {format(language_code, '04x').upper()}")
        print(f"Year is {year}")
        print(f"Month is {month}")
        print(f"Day is {day}")
        print(f"Hour is {hour}")
        print(f"Minute is {minute}")
        print(f"Length is {length}")
        print(text_field)


def main():
    arguments = sys.argv
    if len(arguments) != 4:
        print("Invalid arguments please enter: Request type, ip_address, port_number")
        sys.exit()
    try:
        c = Client(arguments[1], arguments[2], int(arguments[3]))
        c.open_socket()
        packet = c.prepare_packet()
        c.send_packet(packet)
        response = c.get_response()
        c.validate_response(response)

    except ValueError as e:
        print(e)
        sys.exit()


main()
