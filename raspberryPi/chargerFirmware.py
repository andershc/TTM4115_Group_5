from sense_hat import SenseHat
import time as t
import random
import logging
from threading import Thread
#import paho.mqtt.client as mqtt
import logging
from threading import Thread
import json
#import server
from stmpy import Machine, Driver


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

class ChargerStateMachine:
    def __init__(self, charger):
        self.charger = charger
        t_init = {
            "source": "initial",
            "target": "s_idle",
            "effect": "idleState"
        } 

        t_idle_to_charging = {
            "source": "s_idle",
            "target": "s_charging",
            "trigger": "t_chargingState",
            "effect": "chargingState",
        } 
            
        t_charging_to_error= {
            "source": "s_charging",
            "target": "s_error",
            "trigger": "t_errorState",
            "effect": "errorState",
        }  
        t_charging_to_idle= {
            "source": "s_charging",
            "target": "s_idle",
            "trigger": "t_idleState",
            "effect": "idleState",
        }

        t_charging_to_finished= {
            "source": "s_charging",
            "target": "s_finished",
            "trigger": "t_finished",
            "effect": "finishedState",
        }  

        t_finished_to_idle= {
            "source": "s_finished",
            "target": "s_idle",
            "trigger": "t_idleState",
            "effect": "idleState",
        }
        self.stm = Machine(transitions=[t_init,t_idle_to_charging, t_charging_to_error,t_charging_to_idle,t_charging_to_finished,t_finished_to_idle], obj=self, name='stm_charger')
   
    def t_chargingState(self):
         print("Started charging on charger ", self.chargerId)
    def chargingState(self):
        self.charger.changeChargerState = "charging"
        if self.cableConnected == False:
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
            print("Cable not connected on charger ", self.chargerId)
            self.t_idleState()
            

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
            self.t_errorState()
        while run:
            while chargeTime != 5:
                sense.set_pixel(x, y, clear)
                sense.set_pixel(x, y + 1, clear)
                t.sleep(0.5)
                sense.set_pixel(x, y, green)
                sense.set_pixel(x, y + 1, green)
                t.sleep(1)
                chargeTime = chargeTime + 1
            x = x + 1
            chargeTime = 0
            if x == 8:
                run = False
        self.t_finishedState()
    
    def t_errorState(self):
        print("error state")
    def errorState(self):
        self.charger.changeChargerState = "error"
        print("Charging error on ", self.charger.chargerId)
        run = True
        x = 0
        y = self.chargerId * 2
        for i in range(1, 8):
            sense.set_pixel(i, y, red)
            sense.set_pixel(i, y + 1, red)

    def t_finishedState(self):
        print("finished state")
    def finishedState(self):
        self.charger.changeChargerState = "finished"
        print("Finished charging on charger ", self.charger.chargerId)
        run = True
        y = self.charger.chargerId * 2
        for i in range(1, 8):
            sense.set_pixel(i, y, clear)
            sense.set_pixel(i, y + 1, clear)
        for i in range(1, 8):
            sense.set_pixel(i, y, green)
            sense.set_pixel(i, y + 1, green)
            t.sleep(0.5)

    def t_idleState(self):
        print("idle state")
    def idleState(self):
        print("idle state")
        self.charger.changeChargerState = "idle"
        y = self.charger.chargerId
        for i in range(1, 8):
            sense.set_pixel(i, y, clear)
            sense.set_pixel(i, y + 1, clear)

class Charger:
    def __init__(self, id, state="idle"):
        self.cableConnected = True
        self.chargerId = id
        self.chargerState = state
        '''
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
    ''' 
    def getCableConnected(self):
        return self.cableConnected

    def getChargerState(self):
        return self.chargerState

    def getChargerId(self):
        return self.chargerId
    
    def changeChargerState(self, state):
        self.chargerState = state
    
    def connectCable(self):
        # gjør noe her
        self.cableConnected = True

    def disconnectCable(self):
        # gjør noe her
        self.cableConnected = False

def selectCharger(chargerStateMachineArray,chargerArray):
    x = 0
    y = 0
    charger = 0
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
        elif event.direction == "middle" and event.action == "pressed" and chargerArray[charger].getChargerState() == "idle":
            chargerArray[charger].connectCable()
            chargerStateMachineArray[charger].t_chargingState()
            if chargerArray[charger].getChargerState() == "finished":
                chargerArray[charger].disconnectCable()
                chargerStateMachineArray[charger].t_idleState()
        t.sleep(0.5)


def main():
    charger0 = Charger(0)
    charger1 = Charger(1)
    charger2 = Charger(2)
    charger3 = Charger(3)
    chargerArray = [charger0, charger1, charger2, charger3]   

    driver = Driver()

    chargerStateMachine0 = ChargerStateMachine( charger0)
    chargerStateMachine1 = ChargerStateMachine( charger1)
    chargerStateMachine2 = ChargerStateMachine( charger2)
    chargerStateMachine3 = ChargerStateMachine( charger3)
    chargerStateMachineArray = [chargerStateMachine0, chargerStateMachine1, chargerStateMachine2, chargerStateMachine3]
    for i in chargerStateMachineArray:
        driver.add_machine(i.stm)
        driver.start()
        driver.wait_until_finished()

    
    selection = Thread(targer=selectCharger(chargerStateMachineArray,chargerArray))
    selection.start()

main()
