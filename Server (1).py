"""Socket Assigment cosc264, Sam McMillan, 87685388, Server"""
import select
import socket
import sys
from datetime import datetime

ENGLISH_MONTHS = {
    1: "January",
    2: "February",
    3: "March",
    4: "April",
    5: "May",
    6: "June",
    7: "July",
    8: "August",
    9: "September",
    10: "October",
    11: "November",
    12: "December"
}

MAORI_MONTHS = {
    1: "Kohitatea",
    2: "Hui-tanguru",
    3: "Poutu-te-rangi",
    4: "Paenga-whawha",
    5: "Haratua",
    6: "Pipiri",
    7: "Hongongoi",
    8: "Here-turi-koka",
    9: "Mahuru",
    10: "Whiringa-a-nuku",
    11: "Whiringa-a-rangi",
    12: "Hakihea"
}

GERMAN_MONTHS = {
    1: "Januar",
    2: "Februar",
    3: "Marz",
    4: "April",
    5: "Mai",
    6: "Juni",
    7: "Juli",
    8: "August",
    9: "September",
    10: "Oktober",
    11: "November",
    12: "Dezember"
}


class Server:
    """This is a server, the server receives a request packet and replies with a current time or date in
    English, Te reo Maori or German. The server takes three different parameters, ports for English Maori and German"""

    def __init__(self, port_eng, port_maori, port_ger):
        if 1024 > port_eng < 64000:
            print("English port out of range")
            sys.exit()
        if 1024 > port_maori < 64000:
            print("Maori port out of range")
            sys.exit()
        if 1024 > port_ger < 64000:
            print("German port out of range")
            sys.exit()
        ports = {port_eng, port_maori, port_ger}
        if len(ports) != 3:
            print("Port values must be different")
            sys.exit()
        self.port_eng = port_eng
        self.port_maori = port_maori
        self.port_ger = port_ger
        self.english_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.maori_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.german_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def bind_sockets(self):
        try:
            self.english_socket.bind(("localhost", self.port_eng))
            self.maori_socket.bind(("localhost", self.port_maori))
            self.german_socket.bind(("localhost", self.port_ger))
        except socket.error:
            print("Binding sockets has failed")
            self.close_socket()
            sys.exit()

    def listen(self):
        while True:
            listener = select.select([self.english_socket, self.maori_socket, self.german_socket], [], [])
            request_packet, address = listener[0][0].recvfrom(64)
            _, connected_port = listener[0][0].getsockname()
            print(f"Request arrived on {connected_port}")
            request_packet = bytearray(request_packet)
            request_type = self.validate_packet(request_packet)
            if request_type:
                date, time = str(datetime.now()).split(' ')
                year, month, day = date.split('-')
                hours, minutes, _ = time.split(':')
                year, month, day, hours, minutes = int(year), \
                                                   int(month), \
                                                   int(day), \
                                                   int(hours), \
                                                   int(minutes)

                language = "eng" if connected_port == self.port_eng \
                    else "maori" if connected_port == self.port_maori \
                    else "ger"
                if request_type == 0x0001:
                    text_field, language_code = self.get_date(language, year, month, day)
                else:
                    text_field, language_code = self.get_time(language, hours, minutes)
                response_packet = self.prepare_response_packet(
                    text_field,
                    language_code,
                    (year, month, day, hours, minutes))
                listener[0][0].sendto(response_packet, address)
            else:
                request_packet, request_type, address, connected_port = None, None, None, None

    def get_date(self, language, year, month, day):
        if language == 'eng':
            text_field = f"Today’s date is {ENGLISH_MONTHS[int(month)]} {day}, {year}"
            language_code = 0x01
        elif language == 'maori':
            text_field = f"Ko te ra o tenei ra ko {MAORI_MONTHS[int(month)]} {day}, {year}"
            language_code = 0x02
        else:
            text_field = f"Heute ist der {GERMAN_MONTHS[int(month)]} {day}, {year}"
            language_code = 0x03
        return text_field, language_code

    def get_time(self, language, hours, minutes):
        if language == 'eng':
            text_field = f"The current time is {str(hours).zfill(2)}:{str(minutes).zfill(2)}"
            language_code = 0x01
        elif language == 'maori':
            text_field = f"Ko te wa o tenei wa {str(hours).zfill(2)}:{str(minutes).zfill(2)}"
            language_code = 0x02
        else:
            text_field = f"Die Uhrzeut ist {str(hours).zfill(2)}:{str(minutes).zfill(2)}"
            language_code = 0x03
        return text_field, language_code,

    def close_socket(self):
        self.english_socket.close()
        self.maori_socket.close()
        self.german_socket.close()

    def validate_packet(self, packet):
        magic_number = (packet[0] << 8) + packet[1]
        packet_type = (packet[2] << 8) + packet[3]
        request_type = (packet[4] << 8) + packet[5]
        if magic_number != 0x497E:
            print(f"Magic number is incorrect, {format(magic_number, 'x')}")
            return False
        if packet_type != 0x0001:
            print("Packet type is incorrect")
            return False
        if request_type not in [0x0001, 0x0002]:
            print("Request type is incorrect")
            return False
        return request_type

    def prepare_response_packet(self, text_field, language_code, date_time):
        year, month, day, hours, minutes = date_time
        response_packet = bytearray(13 + len(text_field))
        response_packet[0], response_packet[1] = 0x49, 0x7E
        response_packet[3] = 0x02
        response_packet[5] = language_code
        response_packet[6], response_packet[7] = year >> 8, year & 255
        response_packet[8] = month
        response_packet[9] = day
        response_packet[10] = hours
        response_packet[11] = minutes
        response_packet[12] = len(text_field)
        index = 13
        for char in text_field.encode('UTF-8'):
            response_packet[index] = char
            index += 1
        return response_packet


def main():
    arguments = sys.argv
    if len(arguments) != 4:
        print("Invalid arguments please enter 3 different port numbers between 1024 and 64000")
        sys.exit()
    try:
        s = Server(int(arguments[1]), int(arguments[2]), int(arguments[3]))
        s.bind_sockets()
        s.listen()
    except ValueError:
        print("Ports must be integers")
        sys.exit()


main()
