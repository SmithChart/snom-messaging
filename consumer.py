import logging
logger = logging.getLogger(__name__)

class ConsumerDriver():

    """
    This Driver consumes all known datagrams
    received via UDP that are not used anywhere else.

    It does currently not do anything with these information.
    This behavior is intended to keep the log clean of known frames.
    """

    def __init__(self, udp_server):
        """
        Creates a new ConsumerDriver.
        """

        self._udpserver = udp_server
        self._udpserver.register_driver(self)

    def process(self, xml_message, addr):
        """
        Process XML-Element-Tree Messages received via UDP.

        We will watch out for known frames and consome those.
        """

        if xml_message.tag == "request" and xml_message.attrib["type"] == "systeminfo":
            """
            These Datagrams look like this:
            | DEBUG:__main__:incoming datagram from: ('192.168.9.107', 1300)
            | DEBUG:__main__:01 <?xml version="1.0" encoding="UTF-8"?>
            | DEBUG:__main__:02 <request version="19.11.12.1403" type="systeminfo">
            | DEBUG:__main__:03 <externalid>3485367639</externalid>
            | DEBUG:__main__:04 <systemdata>
            | DEBUG:__main__:05 <name>M700</name>
            | DEBUG:__main__:06 <datetime>2019-12-29 22:05:44</datetime>
            | DEBUG:__main__:07 <timestamp>5e091528</timestamp>
            | DEBUG:__main__:08 <status>1</status>
            | DEBUG:__main__:09 <statusinfo>System running</statusinfo>
            | DEBUG:__main__:10 </systemdata>
            | DEBUG:__main__:11 <senderdata>
            | DEBUG:__main__:12 <address>23</address>
            | DEBUG:__main__:13 <name>no23</name>
            | DEBUG:__main__:14 <address>34</address>
            | DEBUG:__main__:15 <name>no34</name>
            | DEBUG:__main__:16 <address>42</address>
            | DEBUG:__main__:17 <name>no42</name>
            | DEBUG:__main__:18 </senderdata>
            | DEBUG:__main__:19 </request>
            | DEBUG:__main__:20

            Currently known:
            ./request/senderdata contains a list of all phones currently connected to these
            basestation.
            """
            logger.debug("squelched systeminfo message")
            return True

        if xml_message.tag == "request" and xml_message.attrib["type"] == "login":
            """
            These Datagrams look like this:
            | DEBUG:__main__:incoming datagram from: ('192.168.9.107', 1300)
            | DEBUG:__main__:01 <?xml version="1.0" encoding="UTF-8"?>
            | DEBUG:__main__:02 <request version="19.11.12.1403" type="login">
            | DEBUG:__main__:03 <externalid>3725663668</externalid>
            | DEBUG:__main__:04 <systemdata>
            | DEBUG:__main__:05 <name>M700</name>
            | DEBUG:__main__:06 <datetime>2019-12-29 22:04:48</datetime>
            | DEBUG:__main__:07 <timestamp>5e0914f0</timestamp>
            | DEBUG:__main__:08 <status>1</status>
            | DEBUG:__main__:09 <statusinfo>System running</statusinfo>
            | DEBUG:__main__:10 </systemdata>
            | DEBUG:__main__:11 <logindata>
            | DEBUG:__main__:12 <status>1</status>
            | DEBUG:__main__:13 </logindata>
            | DEBUG:__main__:14 <senderdata>
            | DEBUG:__main__:15 <address>42</address>
            | DEBUG:__main__:16 <name>no42</name>
            | DEBUG:__main__:17 <location>M700</location>
            | DEBUG:__main__:18 </senderdata>
            | DEBUG:__main__:19 </request>
            | DEBUG:__main__:20

            Currently known:
            ./request/logindata/status == 1: Phone connected to this Basestation
                                       == 0: Phone disconnected from this Basestation

            It is currently not unknown if these messages are also transmitted when roaming.
            """
            logger.debug("squelched login message")
            return True

        if xml_message.tag == "request" and xml_message.attrib["type"] == "alarm":
            """
            These Datagrams look like:
            | WARNING:__main__:01 <?xml version="1.0" encoding="UTF-8"?>
            | WARNING:__main__:02 <request version="19.11.12.1403" type="alarm">
            | WARNING:__main__:03 <externalid>0595015157</externalid>
            | WARNING:__main__:04 <systemdata>
            | WARNING:__main__:05 <name>M700</name>
            | WARNING:__main__:06 <datetime>2019-12-29 23:40:32</datetime>
            | WARNING:__main__:07 <timestamp>5e092b60</timestamp>
            | WARNING:__main__:08 <status>1</status>
            | WARNING:__main__:09 <statusinfo>System running</statusinfo>
            | WARNING:__main__:10 </systemdata>
            | WARNING:__main__:11 <alarmdata>
            | WARNING:__main__:12 <type>16</type>
            | WARNING:__main__:13 </alarmdata>
            | WARNING:__main__:14 <rssidata>
            | WARNING:__main__:15 <rfpi>1333a39f00</rfpi>
            | WARNING:__main__:16 <rssi>204</rssi>
            | WARNING:__main__:17 </rssidata>
            | WARNING:__main__:18 <senderdata>
            | WARNING:__main__:19 <address>99</address>
            | WARNING:__main__:20 <name>no99</name>
            | WARNING:__main__:21 <location>M700</location>
            | WARNING:__main__:22 </senderdata>
            | WARNING:__main__:23 </request>
            | WARNING:__main__:24

            Currently known:
            ./request/alarmdata/type == 16: Probably no alarm

            These frames are generated when connecting a M70 DECT Handset.
            """

            return True

        return False

