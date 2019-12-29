#!/usr/bin/env python3

import socket
import xml.etree.ElementTree as ET
import random
random.seed()

def _prettyprint_mlstring(s):
    l = s.split("\n")
    j = 1
    for i in l:
        print("{:02} {}".format(j, i))
        j += 1

def _get_message(from_name, from_ext, from_loc, to_ext, sysdata_datetime, systada_ts, message_text):
    message = """<?xml version="1.0" encoding="UTF-8"?>
<request version="19.11.12.1403" type="job">
<externalid>{{eid}}</externalid>
<systemdata>
<name>server</name>
<datetime>{{dt}}</datetime>
<timestamp>{{ts}}</timestamp>
<status>1</status>
<statusinfo>System running</statusinfo>
</systemdata>
<jobdata>
<priority>0</priority>
<messages>
<message1></message1>
<message2></message2>
<messageuui>{{msg}}</messageuui>
</messages>
<status>0</status>
<statusinfo></statusinfo>
</jobdata>
<senderdata>
<address>{{from_ext}}</address>
<name>{{from_name}}</name>
<location>{{from_loc}}</location>
</senderdata>
<persondata>
<address>{{to_ext}}</address>
</persondata>
</request>
\0"""
    message = message.replace("{{eid}}", "{:010}".format(random.randrange(9999999999+1)))
    message = message.replace("{{from_ext}}", from_ext)
    message = message.replace("{{from_name}}", from_name)
    message = message.replace("{{from_loc}}", from_loc)
    message = message.replace("{{to_ext}}", to_ext)
    message = message.replace("{{dt}}", sysdata_datetime)
    message = message.replace("{{ts}}", systada_ts)
    message = message.replace("{{msg}}", message_text)
    return message

def _get_messageresponse(ext_id, from_name, from_ext, from_loc, to_ext, sysdata_datetime, systada_ts):
    response = """<?xml version="1.0" encoding="UTF-8"?>
<response version="19.11.12.1403" type="job">
<externalid>{{eid}}</externalid>
<systemdata>
<name>server</name>
<datetime>{{dt}}</datetime>
<timestamp>{{ts}}</timestamp>
<status>1</status>
<statusinfo>System running</statusinfo>
</systemdata>
<jobdata>
<priority>0</priority>
<messages>
<message1></message1>
<message2></message2>
<messageuui></messageuui>
</messages>
<status>1</status>
<statusinfo></statusinfo>
</jobdata>
<senderdata>
<address>{{to_ext}}</address>
<name>name</name>
<location>server</location>
</senderdata>
<persondata>
<address>{{from_ext}}</address>
<name>{{from_name}}</name>
<location>{{from_loc}}</location>
</persondata>
</response>
\0"""
    response = response.replace("{{eid}}", ext_id)
    response = response.replace("{{from_ext}}", from_ext)
    response = response.replace("{{from_name}}", from_name)
    response = response.replace("{{from_loc}}", from_loc)
    response = response.replace("{{to_ext}}", to_ext)
    response = response.replace("{{dt}}", sysdata_datetime)
    response = response.replace("{{ts}}", systada_ts)
    return response

def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", 1300))

    while True:
        data, addr = sock.recvfrom(2048)
        data = data.decode("UTF-8")
        print("\n\nReceived from {}".format(addr))
        for m in data.split("\0"):
            if not m:
                continue
            try:
                r = ET.fromstring(m)
                if r.attrib["type"] == "systeminfo":
                    bs = r.find("./systemdata/name").text
                    stat = r.find("./systemdata/statusinfo").text
                    print("Systemstatus: {} reports '{}'.".format(bs, stat))
                    handsets = r.find("./senderdata")
                    for from_ext, from_name in zip(handsets.getchildren()[0::2], handsets.getchildren()[1::2]):
                        print("-> Handset on bs: {},{}".format(from_name.text, from_ext.text))

                elif r.tag == "request" and r.attrib["type"] == "job":
                    print("Message request")
                    ext_id = r.find("./externalid").text
                    message = r.find("./jobdata/messages/messageuui").text
                    from_name = r.find("./senderdata/name").text
                    from_ext = r.find("./senderdata/address").text
                    from_loc = r.find("./senderdata/location").text
                    to_ext = r.find("./persondata/address").text
                    sysdata_datetime = r.find("./systemdata/datetime").text
                    sysdata_ts = r.find("./systemdata/timestamp").text
                    print("Incoming Message ID '{}' from {},{},{} to {}: '{}'".format(ext_id, from_name, from_ext, from_loc, to_ext, message))

                    response = _get_messageresponse(ext_id, from_name, from_ext, from_loc, to_ext, sysdata_datetime, sysdata_ts)
                    sock.sendto(response.encode(), addr)
                    print("-> Sending confirmation")

                    fwd_message = _get_message(from_name, from_ext, from_loc, to_ext, sysdata_datetime, sysdata_ts, message)
                    sock.sendto(fwd_message.encode(), addr)
                    print("-> Bouncing message onwards")

                elif r.tag == "response" and r.attrib["type"] == "job":
                    print("Message response")

                elif r.tag == "request" and r.attrib["type"] == "login":
                    print("Handset login")
                    bs = r.find("./systemdata/name").text
                    from_name = r.find("./senderdata/name").text
                    from_ext = r.find("./senderdata/address").text
                    print("-> BS '{}': Handset {},{} logged in".format(bs, from_name, from_ext))

                else:
                    _prettyprint_mlstring(m)
                    print("Unkown type!")
            except Exception as e:
                raise e


if __name__ == "__main__":
    main()
