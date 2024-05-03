from stmpy import Machine, Driver
import paho.mqtt.client as mqtt
from sense_hat import SenseHat
from threading import Thread
import time as t
import usb.core
import logging
import random
import json

#stup for sensehat
sense = SenseHat()
red = (255, 0, 0)
green = (0, 255, 0)
blue = (0, 0, 255)
white = (255, 255, 255)
clear = (0, 0, 0)

#MQTT settings
MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883
MQTT_TOPIC_INPUT = "ttm4115/team_05/command"
MQTT_TOPIC_OUTPUT = "ttm4115/team_05/charger_station_status"

def on_connect(self, client, userdata, flags, rc):
        # we just log that we are connected
        self._logger.debug("MQTT connected to {}".format(client))

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
        self.charger.changeChargerState = "charging"
        self.mqttSendState("CHARGING")
        
        #setup for charging
        self.charger.setChargeAmount(0)
        run = True
        x = 1
        y = self.charger.chargerId * 2
        
        #check for connected cable
        if  self.charger.getCableConnected() == False:
            #add something here
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
            sense.set_pixel(x, y, clear)
            sense.set_pixel(x, y + 1, clear)
            self.send(message_id="t_idleState",stm_id=self.id)

        #random chance for error
        is_error = random.randint(0, 11)
        if is_error == 5:
            #add something here
            self.send(message_id="t_errorState",stm_id=self.id)
        
        #setup for charging
        initialSOC = random.randint(1, 6)
        currentSOC = initialSOC
        chargeTime = 0

        #select random intitial state of charge
        for i in range(0, initialSOC):
            sense.set_pixel(i, y, green)
            sense.set_pixel(i, y + 1, green)
            x = i
        
        #set two first pixels to white nothing to do with charging
        sense.set_pixel(0, y, white)
        sense.set_pixel(0, y + 1, white)
        

        #run charging
        while run:
            #time for one charge step 7.5s
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
            currentSOC = x
            #set the charge amount (what you will pay for)
            self.charger.setChargeAmount(currentSOC-initialSOC)
            #when x == 8 the charging is finished max charging time is 7.5s*8 = 60s
            if x == 8:
                run = False

        #goto finished state
        self.t_finishedState()
    
    def t_errorState(self):
        print("error state")
    def errorState(self):
        self.charger.changeChargerState = "error"
        self.mqttSendState("FAULTY")
        print("Charging error on ", self.charger.chargerId)
        y = self.charger.chargerId * 2
        for i in range(1, 8):
            sense.set_pixel(i, y, red)
            sense.set_pixel(i, y + 1, red)



    def t_finishedState(self):
        print("finished state")
    def finishedState(self):
        self.charger.changeChargerState = "finished"
        print("Finished charging on charger ", self.charger.chargerId)
        y = self.charger.chargerId * 2
        for i in range(1, 8):
            sense.set_pixel(i, y, clear)
            sense.set_pixel(i, y + 1, clear)
        for i in range(1, self.charger.getChargeAmount()):
            sense.set_pixel(i, y, green)
            sense.set_pixel(i, y + 1, green)
            t.sleep(0.5)

        self.mqttSendChargeAmount(self.charger.getChargeAmount())
        self.mqttSendState("OCCUPIED")

    def t_idleState(self):
        print("idle state")
    def idleState(self):
        print("idle state")
        self.charger.changeChargerState = "idle"
        y = self.charger.chargerId
        for i in range(1, 8):
            sense.set_pixel(i, y, clear)
            sense.set_pixel(i, y + 1, clear)
        self.mqttSendState("IDLE")

    def mqttSendState(self, status):
        payload = {
            "command": "update_status",
            "status": status,
            "charger_id": self.charger.chargerId
        }
        self.charger.mqttClient.publish(MQTT_TOPIC_OUTPUT, payload=payload, qos=0)

    def mqttSendChargeAmount(self, amount):
        payload = {
            "command": "charge_amount",
            "amount": amount,
            "charger_id": self.charger.chargerId
        }
        self.charger.mqttClient.publish(MQTT_TOPIC_OUTPUT, payload=payload, qos=0)

class Charger:
    def __init__(self, id, mqttClient, state="idle"):
        self.cableConnected = False
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

    def find_new_usb_devices(self):
        devices = usb.core.find(find_all=True)
        new_devices = []
        for dev in devices:
            if dev.idVendor == 0x1d6b or dev.idVendor == 0x2109: #0x2109 driver for keyboard should be ignored 
                continue
            elif dev.port_number not in new_devices: 
                new_devices.append(dev.port_number)
        new_devices.sort()
        return new_devices
    
    def check_charger_connection(self):
        connected_devices = self.find_new_usb_devices()
        if self.chargerId in connected_devices :
            print("Charger",self.chargerId," connected")
            self.connectCable()
        if self.chargerId not in connected_devices:
            print("Charger",self.chargerId," disconnected")
            self.disconnectCable()
       
    
def selectCharger(driver,chargerArray):
    x = 0
    y = 0
    charger = 0
    sense.clear()
    sense.set_pixel(x, y, white)
    sense.set_pixel(x, y + 1, white)
    while True:
        chargerArray[charger].check_charger_connection()

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
            if chargerArray[charger].chargerState == "idle":
                driver.send(message_id="t_chargingState",stm_id=charger)
            if  chargerArray[charger].chargerState == "charging":
                driver.send(message_id="t_finishedState",stm_id=charger)
        t.sleep(0.5)







def main():
    #TODO: 
    #Add MQTT functionality
    #Fix not changing states when getting an error or in charging state and not connected
    
    mqtt_client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION1)
    # callback methods
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message
    # Connect to the broker
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT)
    # start the internal loop to process MQTT messages
    mqtt_client.loop_start()
    
    #setup chargers
    charger0 = Charger(0, "idle", mqtt_client)
    charger1 = Charger(1, "idle", mqtt_client)
    charger2 = Charger(2, "idle", mqtt_client)
    charger3 = Charger(3, "idle", mqtt_client)
    chargerArray = [charger0, charger1, charger2, charger3]   
    
    #setup state machines
    chargerStateMachine0 = ChargerStateMachine(0,charger0)
    chargerStateMachine1 = ChargerStateMachine(1, charger1)
    chargerStateMachine2 = ChargerStateMachine(2, charger2)
    chargerStateMachine3 = ChargerStateMachine(3, charger3)
    chargerStateMachineArray = [chargerStateMachine0, chargerStateMachine1, chargerStateMachine2, chargerStateMachine3]
    
    #initiate state machines
    driver = Driver()
    for i in chargerStateMachineArray:
        driver.add_machine(i.stm)
        driver.start()

    #start select function    
    select_charger = Thread(targer=selectCharger(driver,chargerArray))
    select_charger.start()
    
main()
