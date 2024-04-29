from sense_hat import SenseHat
import time as t
import random
import logging
from threading import Thread
import paho.mqtt.client as mqtt
import logging
from threading import Thread
import json
import usb.core
from stmpy import Machine, Driver

sense = SenseHat()

red = (255, 0, 0)
green = (0, 255, 0)
blue = (0, 0, 255)
white = (255, 255, 255)
clear = (0, 0, 0)

MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883

MQTT_TOPIC_INPUT = "ttm4115/team_05/command"
MQTT_TOPIC_OUTPUT = "ttm4115/team_05/charger_station_status"

def on_connect(self, client, userdata, flags, rc):
    # we just log that we are connected
    print("on_connect:: connected with result code "+str(rc))

def on_message(self, client, userdata, msg):
    pass


class ChargerStateMachine:
    def __init__(self, id, charger):
        self.charger = charger
        self.id = id
        t_init = {
            "source": "initial",
            "target": "s_idle",
            "effect": "idleState",
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
        self.stm = Machine(transitions=[t_init,t_idle_to_charging, t_charging_to_error,t_charging_to_idle,t_charging_to_finished,t_finished_to_idle], obj=self, name=id)
   
    def t_chargingState(self):
         print("Started charging on charger ", self.charger.chargerId)
    def chargingState(self):
        print("Started charging on charger ", self.charger.chargerId)
        self.charger.setChargeAmount(0)
        """
        payload = {
            "command": "update_status",
            "status": "CHARGING",
            "charger_id": self.charger.chargerId
        }
        self.charger.mqttClient.publish(MQTT_TOPIC_OUTPUT, payload=payload, qos=0)
        """
        self.charger.changeChargerState = "charging"
        if self.charger.cableConnected == False:
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
            print("Cable not connected on charger ", self.charger.chargerId)
            self.t_idleState()
            

        run = True
        x = 1
        y = self.charger.chargerId * 2
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
        
        self.charger.setChargeAmount(currentSOC-initialSOC)
        """
        self.charger.mqttClient.publish(MQTT_TOPIC_OUTPUT, payload=payload, qos=0)
        """
        self.t_finishedState()
    
    def t_errorState(self):
        print("error state")
    def errorState(self):
        
        self.charger.changeChargerState = "error"
        """
        payload = {
            "command": "update_status",
            "status":"FAULTY",
            "charger_id": self.charger.chargerId
        }
        payload = {
            "command": "charge_amount",
            "ammount": self.charger.getChargeAmount,
            "charger_id": self.charger.chargerId
        }
        self.charger.mqttClient.publish(MQTT_TOPIC_OUTPUT, payload=payload, qos=0)
        """
        print("Charging error on ", self.charger.chargerId)
        run = True
        x = 0
        y = self.charger.chargerId * 2
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
        """
        payload = {
            "command": "update_status",
            "status":"OCCUPIED",
            "charger_id": self.charger.chargerId
        }
        self.charger.mqttClient.publish(MQTT_TOPIC_OUTPUT, payload=payload, qos=0)
        """
    def t_idleState(self):
        print("idle state")
    def idleState(self):
        print("idle state")
        self.charger.changeChargerState = "idle"
        y = self.charger.chargerId
        for i in range(1, 8):
            sense.set_pixel(i, y, clear)
            sense.set_pixel(i, y + 1, clear)
        """
        payload = {
            "command": "update_status",
            "status":"IDLE",
            "charger_id": self.charger.chargerId
        }
        self.charger.mqttClient.publish(MQTT_TOPIC_OUTPUT, payload=payload, qos=0)
        """
    
class Charger:
    def __init__(self, id, state="idle",mqttClient=None):
        self.cableConnected = True
        self.chargerId = id
        self.chargerState = state
        self.mqttClient = mqttClient
        self.chargeAmount = 0

    def getCableConnected(self):
        return self.cableConnected

    def getChargerState(self):
        return self.chargerState

    def getChargerId(self):
        return self.chargerId
    
    def getChargeAmount(self):
        return self.chargeAmount
    
    def setChargeAmount(self, amount):
        self.chargeAmount = amount

    def changeChargerState(self, state):
        self.chargerState = state
    
    def connectCable(self):
        # gjør noe her
        self.cableConnected = True

    def disconnectCable(self):
        # gjør noe her
        self.cableConnected = False

def selectCharger(driver,chargerStateMachineArray,chargerArray):
    x = 0
    y = 0
    charger = 0
    sense.clear()
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
            if chargerArray[charger].getChargerState() == "charging":
                driver.send(message_id="t_finishedState",stm_id=charger)
            driver.send(message_id="t_chargingState",stm_id=charger)
        t.sleep(0.5)



def find_new_usb_devices():
    devices = usb.core.find(find_all=True)
    new_devices = []
    for dev in devices:
        if dev.idVendor == 0x1d6b or dev.idVendor == 0x2109: #0x2109 driver for keyboard should be ignored 
            print("device is a hub")
        elif dev.port_number not in new_devices: 
            new_devices.append(dev.port_number)
    new_devices.sort()
    return new_devices

def check_charger_connection(chargerArray):
    new_devices = find_new_usb_devices()
    old_devices = []
    while True:
        added = [] 
        removed = []
        new_devices = find_new_usb_devices()
        for dev in new_devices:
            if dev not in old_devices:
                print("Device added")
                print(dev)
                added.append(dev)
        for dev in old_devices:
            if dev not in new_devices:
                print("Device removed")
                print(dev)
                removed.append(dev)
        old_devices = new_devices
        for i in added:
            chargerArray[i].connectCable()
            print("Charger ", i, " cable connected")
            print("--------------------")
        for i in removed:
            chargerArray[i].disconnectCable()
            print("Charger ", i, " cable disconnected")
            print("--------------------")
        t.sleep(5)

def main():
    
    mqtt_client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION1)
    # callback methods
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message
    # Connect to the broker
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT)
    # start the internal loop to process MQTT messages
    mqtt_client.loop_start()

    charger0 = Charger(0, "idle", mqtt_client)
    charger1 = Charger(1, "idle", mqtt_client)
    charger2 = Charger(2, "idle", mqtt_client)
    charger3 = Charger(3, "idle", mqtt_client)
    chargerArray = [charger0, charger1, charger2, charger3]   

    driver = Driver()

    chargerStateMachine0 = ChargerStateMachine(0,charger0)
    chargerStateMachine1 = ChargerStateMachine(1, charger1)
    chargerStateMachine2 = ChargerStateMachine(2, charger2)
    chargerStateMachine3 = ChargerStateMachine(3, charger3)
    chargerStateMachineArray = [chargerStateMachine0, chargerStateMachine1, chargerStateMachine2, chargerStateMachine3]
    for i in chargerStateMachineArray:
        driver.add_machine(i.stm)
        driver.start()

    
    selection = Thread(targer=selectCharger(driver,chargerStateMachineArray,chargerArray))
    check_connection = Thread(target=check_charger_connection(chargerArray))
    selection.start()
    check_connection.start()

main()
