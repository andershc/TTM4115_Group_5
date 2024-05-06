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
MQTT_TOPIC_MANAGE_CHARGER = "ttm4115/team_05/manage_charger"
MQTT_TOPIC_OUTPUT = "ttm4115/team_05/command"

         
class ChargerStateMachine:
    def __init__(self, id, charger):
        self.charger = charger
        self.id = str(id)
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
        t_idle_to_error = {
            "source": "s_error",
            "target": "s_idle",
            "trigger": "t_errorState",
            "effect": "errorState",
        } 
        t_charging_to_error= {
            "source": "s_charging",
            "target": "s_error",
            "trigger": "t_errorState",
            "effect": "errorState",
        }  
        t_charging_to_finished= {
            "source": "s_charging",
            "target": "s_finished",
            "trigger": "t_finishedState",
            "effect": "finishedState",
        }  
        t_finished_to_idle= {
            "source": "s_finished",
            "target": "s_idle",
            "trigger": "t_idleState",
            "effect": "idleState",
        }
        self.stm = Machine(transitions=[t_init,t_idle_to_charging, t_charging_to_error,t_idle_to_error,t_charging_to_finished,t_finished_to_idle], obj=self, name=self.id)
   
   
    def t_chargingState(self):
         print("Started charging on charger ", self.charger.chargerId)
    def chargingState(self):
        
        print("Started charging on charger ", self.charger.chargerId)
        self.charger.chargerState =  "charging"
        
        
        #setup for charging
        self.charger.setChargeAmount(0)
        run = True
        x = 1
        y = self.charger.chargerId * 2
        
        #setup for charging
        initialSOC = random.randint(1, 6)
        currentSOC = initialSOC
        chargeTime = 0

        #select random intitial state of charge
        for i in range(1, initialSOC):
            sense.set_pixel(i, y, green)
            sense.set_pixel(i, y + 1, green)
            x = i
        
        #set two first pixels to white nothing to do with charging
        sense.set_pixel(0, y, white)
        sense.set_pixel(0, y + 1, white)
        
        #set the charge amount (what you will pay for)
        self.mqttSendState("CHARGING",(9-currentSOC)*7.5*1000)
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
            
            #when x == 8 the charging is finished max charging time is 7.5s*8 = 60s
            if x == 8:
                run = False
    
    def t_errorState(self):
        print("error state")
    def errorState(self):
        self.charger.chargerState = "error"
        self.mqttSendState("FAULTY")
        print("Charging error on ", self.charger.chargerId)
        y = self.charger.chargerId * 2
        for i in range(1, 8):
            sense.set_pixel(i, y, red)
            sense.set_pixel(i, y + 1, red)



    def t_finishedState(self):
        print("finished state")
    def finishedState(self):
        self.charger.chargerState = "finished"
        print("Finished charging on charger ", self.charger.chargerId)
        y = self.charger.chargerId * 2
        for i in range(1, 8):
            sense.set_pixel(i, y, green)
            sense.set_pixel(i, y + 1, green)
            t.sleep(0.5)

        #self.mqttSendChargeAmount(self.charger.getChargeAmount())
        self.mqttSendState("FINISHED")

    def t_idleState(self):
        print("idle state")
    def idleState(self):
        print("idle state")
        self.charger.chargerState = "idle"
        y = self.charger.chargerId
        for i in range(1, 8):
            sense.set_pixel(i, y, clear)
            sense.set_pixel(i, y + 1, clear)
        self.mqttSendState("AVAILABLE")

    def mqttSendState(self, status,amount=0):
        print(status)
        payload = {
            "command": "update_status",
            "status": status,
            "duration": amount,
            "charger_id": self.charger.chargerId
        }
        payload = json.dumps(payload)
        self.charger.mqttClient.publish(MQTT_TOPIC_OUTPUT, payload=payload, qos=0)

class Charger:
    def __init__(self, id, mqttClient, state="idle"):
        self.cableConnected = False
        self.chargerId = id
        self.chargerState = state
        self.mqttClient = mqttClient
        self.chargeAmount = 0
        #run connection checker in new thread
        self.t = Thread(target=self.check_charger_connection)
        self.t.start()

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
        prev_state = self.cableConnected
        if self.chargerId in connected_devices :
            print("Charger",self.chargerId," connected")
            self.connectCable()
        if self.chargerId not in connected_devices:
            print("Charger",self.chargerId," disconnected")
            self.disconnectCable()
        if prev_state != self.cableConnected:
            print("Charger",self.chargerId," changed state")
            #send mqtt message
       
    
def selectCharger(driver,chargerArray):
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
        elif event.direction == "middle" and event.action == "pressed":
            is_error = random.randint(0, 11)
            #check for connected cable
            if chargerArray[charger].chargerState == "finished":
                driver.send(message_id="t_idleState",stm_id=str(charger))
            elif  chargerArray[charger].getCableConnected() == False:
                #add something here
                sense.set_pixel(x+1, y, red)
                sense.set_pixel(x+1, y + 1, red)
                t.sleep(0.5)
                sense.set_pixel(x+1, y, white)
                sense.set_pixel(x+1, y + 1, white)
                t.sleep(0.5)
                sense.set_pixel(x+1, y, red)
                sense.set_pixel(x+1, y + 1, red)
                t.sleep(0.5)
                sense.set_pixel(x+1, y, white)
                sense.set_pixel(x+1, y + 1, white)
                print("Cable not connected on charger ", chargerArray[charger].chargerId)
                sense.set_pixel(x+1, y, clear)
                sense.set_pixel(x+1, y + 1, clear)
            elif is_error == 5:
                #add something here
                driver.send(message_id="t_errorState",stm_id=str(charger))
            elif chargerArray[charger].chargerState == "idle":
                driver.send(message_id="t_chargingState",stm_id=str(charger))
            elif chargerArray[charger].chargerState == "charging":
                driver.send(message_id="t_finishedState",stm_id=str(charger))
            driver.print_status()
            t.sleep(0.5)







class Main:
    #TODO: 
    #Add MQTT functionality
    #Fix not changing states when getting an error or in charging state and not connected
    def __init__(self):
        self.mqtt_client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION1)
        # callback methods
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message
        # Connect to the broker
        self.mqtt_client.connect(MQTT_BROKER, MQTT_PORT)
        self.mqtt_client.subscribe(MQTT_TOPIC_MANAGE_CHARGER)
        # start the internal loop to process MQTT messages
        self.mqtt_client.loop_start()
        
        #setup chargers
        charger0 = Charger(id=0, state="idle", mqttClient=self.mqtt_client)
        charger1 = Charger(id=1, state="idle", mqttClient=self.mqtt_client)
        charger2 = Charger(id=2, state="idle", mqttClient=self.mqtt_client)
        charger3 = Charger(id=3, state="idle", mqttClient=self.mqtt_client)
        self.chargerArray = [charger0, charger1, charger2, charger3]   
        
        #setup state machines
        chargerStateMachine0 = ChargerStateMachine(0,charger0)
        chargerStateMachine1 = ChargerStateMachine(1, charger1)
        chargerStateMachine2 = ChargerStateMachine(2, charger2)
        chargerStateMachine3 = ChargerStateMachine(3, charger3)
        self.chargerStateMachineArray = [chargerStateMachine0, chargerStateMachine1, chargerStateMachine2, chargerStateMachine3]
        
        #initiate state machines
        self.driver = Driver()
        for i in self.chargerStateMachineArray:
            self.driver.add_machine(i.stm)
            self.driver.start()
        #start select function    
        select_charger = Thread(targer=selectCharger(self.driver,self.chargerArray))
        select_charger.start()
    def on_connect(self, client, userdata, flags,rc):
        # we just log that we are connected
        print("Connected to broker")

    def on_message(self, client, userdata, msg):
        payload = json.loads(msg.payload.decode("utf-8"))
        if msg.topic != MQTT_TOPIC_MANAGE_CHARGER:
            return
        else:
            print(payload)
            if payload["command"] == "start_charging":
                x = 0
                y = int(payload["charger_id"])
                if  self.chargerArray[int(payload["charger_id"])].getCableConnected() == False:
                    #add something here
                    sense.set_pixel(x+1, y, red)
                    sense.set_pixel(x+1, y + 1, red)
                    t.sleep(0.5)
                    sense.set_pixel(x+1, y, white)
                    sense.set_pixel(x+1, y + 1, white)
                    t.sleep(0.5)
                    sense.set_pixel(x+1, y, red)
                    sense.set_pixel(x+1, y + 1, red)
                    t.sleep(0.5)
                    sense.set_pixel(x+1, y, white)
                    sense.set_pixel(x+1, y + 1, white)
                    print("Cable not connected on charger ", payload["charger_id"])
                    sense.set_pixel(x+1, y, clear)
                    sense.set_pixel(x+1, y + 1, clear)
                else:
                    self.driver.send(message_id="t_chargingState",stm_id=str(payload["charger_id"]))
            elif payload["command"] == "stop_charging":
                self.driver.send(message_id="t_finishedState",stm_id=str(payload["charger_id"]))
            elif payload["command"] == "disconnect_charger":
                self.driver.send(message_id="t_idleState",stm_id=str(payload["charger_id"]))
            


            
                
   
main = Main()
