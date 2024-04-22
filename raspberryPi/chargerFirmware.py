from sense_hat import SenseHat
import time as t
import random
import logging
from threading import Thread
import paho.mqtt.client as mqtt
import logging
from threading import Thread
import json

sense = SenseHat()

red = (255, 0, 0)
green = (0, 255, 0)
blue = (0, 0, 255)
white = (255, 255, 255)
clear = (0, 0, 0)

MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883

MQTT_TOPIC_INPUT = "ttm4115/team_05/charger/command"
MQTT_TOPIC_OUTPUT = "ttm4115/team_05/charger/answer"


class charger:
    chargerId = 0
    chargerState = "idle"
    cableConnected = True

    def __init__(self, id, state="idle"):
        self.chargerId = id
        self.chargerState = state

        # Init the mqtt client
        self._logger = logging.getLogger(__name__)
        print("logging under name {}.".format(__name__))
        self._logger.info("Starting Component")

        # create a new MQTT client
        self._logger.debug(
            "Connecting to MQTT broker {} at port {}".format(MQTT_BROKER, MQTT_PORT)
        )
        self.mqtt_client = mqtt.Client()
        # callback methods
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message
        # Connect to the broker
        self.mqtt_client.connect(MQTT_BROKER, MQTT_PORT)
        # start the internal loop to process MQTT messages
        self.mqtt_client.loop_start()

    def publish_command(self, command):
        payload = json.dumps(command)
        self._logger.info(command)
        self.mqtt_client.publish(MQTT_TOPIC_INPUT, payload=payload, qos=0)

    def getCableConnected(self):
        return self.cableConnected

    def getChargerState(self):
        return self.chargerState

    def getChargerId(self):
        return self.chargerId

    def changeState(self, state):
        self.chargerState = state

    def connectCable(self):
        # gjør noe her
        self.cableConnected = True

    def disconnectCable(self):
        # gjør noe her
        self.cableConnected = False

    def chargerFsm(self):
        while True:
            if self.getChargerState() == "charging":
                self.chargingState()
            elif self.getChargerState() == "error":
                self.errorState()
            elif self.getChargerState() == "finished":
                self.finishedState()
            elif self.getChargerState() == "idle":
                self.idleState()

    def chargingState(self):
        if self.cableConnected == False:
            self.changeState("idle")
            sense.set_pixel(x, y, red)
            sense.set_pixel(x, y + 1, red)
            t.sleep(0.5)
            sense.set_pixel(x, y, white)
            sense.set_pixel(x, y + 1, white)
            t.sleep(0.5)
            sense.set_pixel(x, y, red)
            sense.set_pixel(x, y + 1, red)
            t.sleep(0.5)
            sense.set_pixel(x, y, white)
            sense.set_pixel(x, y + 1, white)
            raise Exception("ERROR, charging cable not connected")

        run = True
        x = 1
        y = self.chargerId * 2
        initialSOC = random.randint(1, 6)
        for i in range(0, initialSOC):
            sense.set_pixel(i, y, green)
            sense.set_pixel(i, y + 1, green)
            x = i

        sense.set_pixel(0, y, white)
        sense.set_pixel(0, y + 1, white)

        x = x + 1
        currentSOC = initialSOC
        chargeTime = 0
        is_error = random.randint(0, 11)
        if is_error == 5:
            self.changeState("ERROR")
        print("Started charging on charger ", self.chargerId)
        while run:
            while chargeTime != 5:
                sense.set_pixel(x, y, clear)
                sense.set_pixel(x, y + 1, clear)
                t.sleep(0.5)
                sense.set_pixel(x, y, green)
                sense.set_pixel(x, y + 1, green)
                t.sleep(1)
                chargeTime = chargeTime + 1
                if self.getCableConnected() == False:
                    # send charging amount initialsoc - current soc
                    run = False
                    break
            x = x + 1
            chargeTime = 0
            if x == 8:
                run = False
        self.changeState("finished")

    def errorState(self):
        print("Charging error on ", self.chargerId)
        run = True
        x = 0
        y = self.chargerId * 2
        for i in range(1, 8):
            sense.set_pixel(i, y, red)
            sense.set_pixel(i, y + 1, red)
        while run:
            print("error on charger ", self.chargerId)
            if self.getChargerState() == "idle":
                self.changeState("finished")
                break

    def finishedState(self):
        print("Finished charging on charger ", self.chargerId)
        run = True
        x = 0
        y = self.chargerId * 2
        while run:
            if self.cableConnected == False:
                for i in range(1, 8):
                    sense.set_pixel(i, y, clear)
                    sense.set_pixel(i, y + 1, clear)
        self.changeState("idle")

    def idleState(self):
        y = self.chargerId
        for i in range(1, 8):
            sense.set_pixel(i, y, clear)
            sense.set_pixel(i, y + 1, clear)


def startStopCharger(charger):
    if charger.getChargerState() == "finished":
        charger.disconnectCable()
    elif charger.getChargerState() == "charging":
        charger.disconnectCable()
    elif charger.getChargerState() == "idle":
        charger.changeState("charging")
        charger.connectCable()
        Thread(target=charger.chargerFsm).start()


def selectCharger(chargers):
    x = 0
    y = 0
    charger = 0
    chargerArray = chargers
    sense.set_pixel(x, y, white)
    sense.set_pixel(x, y + 1, white)
    while True:
        event = sense.stick.wait_for_event()
        if event.direction == "up" and event.action == "pressed":
            sense.set_pixel(x, y, clear)
            sense.set_pixel(x, y + 1, clear)
            y = y - 2
            charger = charger - 1
            if y < 0:
                y = 6
                charger = 3
            sense.set_pixel(x, y, white)
            sense.set_pixel(x, y + 1, white)
        elif event.direction == "down" and event.action == "pressed":
            sense.set_pixel(x, y, clear)
            sense.set_pixel(x, y + 1, clear)
            y = y + 2
            charger = charger + 1
            if y > 6:
                y = 0
                charger = 0
            sense.set_pixel(x, y, white)
            sense.set_pixel(x, y + 1, white)
        elif event.direction == "middle" and event.action == "pressed":
            startStopCharger(chargerArray[charger])
        t.sleep(0.5)


def main():
    sense.clear()
    charger0 = charger(0)
    charger1 = charger(1)
    charger2 = charger(2)
    charger3 = charger(3)
    chargers = [charger0, charger1, charger2, charger3]

    selection = Thread(target=selectCharger(chargers))
    selection.start()

    # legge til mqtt broker funcksjon
    # legge til statemachine fra stmpy i charger classen


main()
