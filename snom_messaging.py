#!/usr/bin/env python3

import logging
import asyncio
import xml.etree.ElementTree as ET
import random
from messagesystem import MessageSystem
from consumer import ConsumerDriver

logger = logging.getLogger(__name__)
random.seed()

def _prettyprint_mlstring(s, output):
    l = s.split("\n")
    j = 1
    for i in l:
        output("{:02} {}".format(j, i))
        j += 1


class UdpServer(asyncio.DatagramProtocol):
    def __init__(self):
        self._transport = None
        self._lastConnection = None
        self._drivers = []

    def connection_made(self, transport):
        self._transport = transport
        logger.debug("UDP Socket opened")

    def datagram_received(self, data, addr):
        logger.debug("incoming datagram from: {}".format(addr))
        # Take a note of the last origin.
        # We assume this BaseStation will still be online when we are going to
        # send anything.
        self._lastConnection = addr

        # process all messages in a datagram
        # I haven't seen any datagram with more than one message inside.
        # But having them \0-terminated is either an off-by-one error or can
        # be a delimiter.
        data = data.decode("UTF-8")
        for message in data.split("\0"):
            if not message:
                # skip messages with len(0).
                continue

            _prettyprint_mlstring(message, logger.debug)
            xml_message = ET.fromstring(message)
            for driver in self._drivers:
                # check if we find any driver for this message
                try:
                    if driver.process(xml_message, addr):
                        break
                except Exception as exp:
                    logger.warning(
                        "Message-Driver {} failed to process message with \
                        exception {}.".format(driver, exp)
                    )
            else:
                logger.warning("No driver is interested in this message. Dumping content.")
                _prettyprint_mlstring(message, logger.warning)

    def error_received(self, exc):
        logger.debug("UDP Socket: Got exception: {}".format(exc))

    def register_driver(self, driver):
        logger.debug("Attached Driver {}".format(driver))
        self._drivers.append(driver)

    def send_dgram(self, dgram, addr=None):
        """
        Sends the String in dgram over the socket to the last known
        origin.
        """

        if not self._lastConnection and addr is None:
            logger.warning("Writing to UDP-Socket before anything was received. Will not send!")
        else:
            if addr is None:
                out_addr = self._lastConnection
            else:
                out_addr = addr
            logger.debug("Outgoing Datagram to {}".format(addr))
            _prettyprint_mlstring(dgram, logger.debug)
            self._transport.sendto(dgram.encode("UTF-8"), addr)


def main():
    logging.basicConfig(level=logging.INFO)
    logger.debug("Begin Setup...")

    loop = asyncio.get_event_loop()
    sock = loop.create_datagram_endpoint(
        UdpServer,
        local_addr=("0.0.0.0", 1300)
    )
    transport, protocol = loop.run_until_complete(sock)

    message_system = MessageSystem(protocol)
    consumer_driver = ConsumerDriver(protocol)

    logger.info("Snom Messaging started successfully.")
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass

    transport.close()
    message_system.close()

if __name__ == "__main__":
    main()
