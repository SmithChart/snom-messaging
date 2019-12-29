# SNOM messaging server

This project contains a proof-of-concept messaging-server for
SMS-like communication between SNOM DECT-handsets.

This project has been developed against a M700 basestation (FW 0450.13),
a M65 (FW 450.13) handset and a M70 (FW 450.11) handset.
This project will probably work with other handsets, too.

This project uses the proprietary messaging-server interface provided by
the M700 Basestations (see Webinterface -> Management -> Text Messaging).
The protocol is completely reverse-engineered by wild guessing.

## How to use it

I assume you have a working M700 setup (either multicell or not) with a few
handsets configured and running.
SNOM uses the primary extension assigned to a handset to route messages so you
also need SIP configured and working.

Start the server on a machine that can be reached by the Basestations.
The server will bind to 0.0.0.0:1300 (sorry, no IPv6 here!).

Now setup Text-Messaging in your M700:

* Text Messaging: "Enabled", *Not* "Enabled without server"(!)
* Text Messaging and Alarm Server: IP of the machine running our server.
* Text Messaging Port: 1300 (default)

Additionally (for development) I have set the following values.
These seem to increase the rate of status updates. But your messaging will
also work without it.

* Text Message Keep Alive: 1
* Text Messaging Response: 10
* Text Messaging TTL: 5
* Terminal Keep Alive: 1

Afterwards you need to reboot your DECT basestation (or for multicell all
basestations in your chain).

The basestations will now start to send status messages to your server.

## What it does

This project currently only implements messaging:

* Accept text messages from a phone and sent a confirmation to the sending phone.
* Accepted text messages are queued for delivery.
* Regularly the queue is checked for messages to deliver.
* If a message can not be delivered it is kept and resend later on.


## What comes next

This project is meant as a platform to implement more functionality
that is made available using this proprietary interface!

For example:

* SNOM's marketing claims the M70 can track bluetooth beacons.
  Is this information exposed using this interface?
* Also: SNOM's marketing claims that you can build automation on top
  of the alarm functionality of their devices, like opening doors.
  I bet this is also implemented using this interface *;)*
