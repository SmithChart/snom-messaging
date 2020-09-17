import logging
import asyncio
import xml.etree.ElementTree as ET
import random
import time
logger = logging.getLogger(__name__)

class Message():

    """
    This class encapsulates a Text-Message with it's metadata.
    """

    def __init__(self, xml_message):
        """
        Creates a Message from it's XML-Element-Tree representation.
        """

        self.created = time.time()
        self.last_send_try = 0

        self._xml_message = xml_message

        self.ext_id = xml_message.find("./externalid").text
        self.message = xml_message.find("./jobdata/messages/messageuui").text
        self.from_name = xml_message.find("./senderdata/name").text
        self.from_ext = xml_message.find("./senderdata/address").text
        self.from_loc = xml_message.find("./senderdata/location").text
        self.to_ext = xml_message.find("./persondata/address").text
        self.sysdata_datetime = xml_message.find("./systemdata/datetime").text
        self.sysdata_ts = xml_message.find("./systemdata/timestamp").text

        # This 10-Digit random number will be used as ID, when re-sending
        # the message to it's recipient.
        self.internal_ext_id = random.randrange(9999999999+1)

    def get_messageresponse(self):
        """
        This function creates a 'received confirmation' for a received message.
        It seems the BaseStations are somewhat picky on the format of the XML.
        Thus I am using a template here to create the binary-xml I really want.

        'Received confirmations' are empty message containing the same externalid
        and an empty message. They are send with senderdata and persondata swapped.
        """

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
        response = response.replace("{{eid}}", self.ext_id)
        response = response.replace("{{from_ext}}", self.from_ext)
        response = response.replace("{{from_name}}", self.from_name)
        response = response.replace("{{from_loc}}", self.from_loc)
        response = response.replace("{{to_ext}}", self.to_ext)
        response = response.replace("{{dt}}", self.sysdata_datetime)
        response = response.replace("{{ts}}", self.sysdata_ts)
        return response

    def get_message(self):
        """
        This function creates a new message for a received message.
        It seems the BaseStations are somewhat picky on the format of the XML.
        Thus I am using a template here to create the binary-xml I really want.

        The new message looks like the one we received. But we can re-create it anytime
        we want.
        """
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
        message = message.replace("{{eid}}", "{:010}".format(self.internal_ext_id))
        message = message.replace("{{from_ext}}", self.from_ext)
        message = message.replace("{{from_name}}", self.from_name)
        message = message.replace("{{from_loc}}", self.from_loc)
        message = message.replace("{{to_ext}}", self.to_ext)
        message = message.replace("{{dt}}", self.sysdata_datetime)
        message = message.replace("{{ts}}", self.sysdata_ts)
        message = message.replace("{{msg}}", self.message)
        return message

class MessageSystem():

    """
    This dictionary contains known status codes returned from BaseStations
    after sending a message.

    It contains the following information:
    <statuscode>: (<Log-message String>, <Remove from Queue>)
    """
    _snom_message_status = {
        1: ("Message delivered", True),
        11: ("User absent", False),
    }

    def __init__(self, udp_server):
        """
        Create a new MessageSystem.

        This Message-System implements SMS-Communication with storage of
        non-delivered messages for Snom DECT handsets.
        """
        self._udp_server = udp_server
        self._queue = []

        self._udp_server.register_driver(self)

        loop = asyncio.get_event_loop()
        loop.create_task(self.process_outbox())

        self._roaming_monitor = roaming_monitor

    def close(self):
        #TODO: Implement proper shutdown of this function.
        pass

    def process(self, xml_message, addr):

        """
        Process a message received via UDP.

        We are interested in two typed of messages from the UDP-Socket:
        * New Messages from Phones
        * Status-Updates for messages we have sent

        All other messages are not consumed.
        """

        if xml_message.tag == "request" and xml_message.attrib["type"] == "job":
            # This is an incoming message. We will queue this message in our outbox and
            # send a reception confirmation to the sending phone.
            # We do not track if the sending phone confirms our status update.
            logger.debug("Found incoming message. Trying to parse and add it to queue")
            m = Message(xml_message)
            self._queue.append(m)
            logger.info("Added Message with external ID %s and internal id %s", m.ext_id, m.internal_ext_id)

            # send confirmation to sender
            self._udp_server.send_dgram(m.get_messageresponse())
            logger.debug("Confirmation for sender sent!")

            return True

        if xml_message.tag == "response" and xml_message.attrib["type"] == "job":
            # This is a reception confirmation.
            # These come in two tastes:
            # * With "./response/jobdata": These contain status information for a message
            #   ./response/jobdata/status == 1: Message received
            #   ./response/jobdata/status == 11: User absent?
            # * Without "./response/jobdata":  I am not sure what these do. They seem to be send
            #   by the BaseStations. I am currently ignoring these.

            if xml_message.find("./jobdata"):
                ext_id = int(xml_message.find("./externalid").text)
                logger.debug("Status update for %s", ext_id)

                status = int(xml_message.find(".jobdata/status").text)

                remove_from_queue = False
                if status in MessageSystem._snom_message_status:
                    logger.info(
                        "Status Update for %s: %s => '%s'. Remove from queue? %s",
                        ext_id,
                        status,
                        MessageSystem._snom_message_status[status][0],
                        MessageSystem._snom_message_status[status][1],
                    )
                    remove_from_queue = MessageSystem._snom_message_status[status][1]
                else:
                    logger.warning("Got unknown status code: %s. Keeping message in queue", status)

                if remove_from_queue:
                    for msg in self._queue:
                        if msg.internal_ext_id == ext_id:
                            self._queue.remove(msg)
                            logger.debug("Removed %s from queue", ext_id)
                            break
                    else:
                        logger.warning("Got reception confirmation for unknown message: %s", ext_id)

            return True

        return False

    async def process_outbox(self):

        """
        Process the queue of outgoing messages.
        """

        while True:
            # check if any message is to resend
            for message in self._queue:
                if (time.time() - message.last_send_try) > 60:
                    logger.debug("Sending message %s", message.internal_ext_id)
                    self._udp_server.send_dgram(message.get_message())
                    message.last_send_try = time.time()

            # purge all messages older than
            for message in self._queue:
                if (time.time() - message.created) > 7*24*60*60:
                    logger.info("Removing undelivered message from queue: %s", message.internal_ext_id)
                    self._queue.remove(message)

            await asyncio.sleep(1)
            continue
