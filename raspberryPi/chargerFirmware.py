from sense_hat import SenseHat
import time as t
import random 
import logging
from threading import Thread

sense = SenseHat()

red = (255,0,0)
green = (0,255,0)
blue = (0,0,255)
white = (255,255,255)
clear = (0,0,0)


class charger(Thread):
    def __init__(self, chargerId, state = "idle"):
        Thread.__init__(self, args=(chargerId, state))
        self.id = chargerId
        self.chargerState = state
        self.cableConnected = True

    def getConnected():
        return charger.cableConnected
    
    def getChargerState():
        return charger.chargerState

    def getChargerId():
        return charger.chargerId

    def changeState(state):
        chargerState = state
    
    def connectCable():
        #gjør noe her
        charger.cableConnected = True

    def chargingState():
        if charger.cableConnected == False:
            charger.changeState("idle")
            raise Exception("ERROR, charging cable not connected")
            
        run = True
        x = 1
        y = charger.chargerId*2
        charger = charger.hargerId
        stateOfCharge = random.randint(1,7)
        for i in range(0,stateOfCharge):
            sense.set_pixel(i, y, green)
            sense.set_pixel(i, y+1, green)
            x = i
        x = x+1
        chargeTime = 0
        is_error = random.randint(0,11)
        if is_error == 5:
            charger.changeState("error")
        print("Started charging on charger ", charger.charger_id)
        while run:
            while chargeTime!= 5:
                sense.set_pixel(x, y, clear)
                sense.set_pixel(x, y+1, clear)
                t.sleep(0.5)
                sense.set_pixel(x, y, green)
                sense.set_pixel(x, y+1, green)
                t.sleep(1)
                sense.set_pixel(x, y, clear)
                sense.set_pixel(x, y+1, clear)
                t.sleep(0.5)
                sense.set_pixel(x, y, green)
                sense.set_pixel(x, y+1, green)
                chargeTime = chargeTime+1
            x = x+1
            chargeTime = 0
            if x == 8:
                run = False
        charger.changeState("finished")
    
    def errorState():
        print("Charging error on ", charger.charger_id)
        run = True
        x = 0
        y = charger.charger_id*2
        for i in range(1,8):
            sense.set_pixel(i, y, red)
            sense.set_pixel(i, y+1, red)
        while run:
            print("error on charger ",charger.charger_id)
            if (charger.getChargerState() == "idle"):
                break
        
    def finishedState():
        print("Finished charging on charger ", charger.chargerId)
        run = True
        x = 0
        y = charger.chargerId*2
        while run:
            event = sense.stick.wait_for_event()
            if event.direction == "middle" and event.action == "pressed":
                for i in range(0,8):
                    sense.set_pixel(i, y, clear)
                    sense.set_pixel(i, y+1, clear)
        charger.changeState("idle")

    def idleState():
        y = charger.id
        for i in range(1,7):
            sense.set_pixel(i, y, clear)
            sense.set_pixel(i, y+1, clear)




def changeChargerState(charger, state): 
    charger.changeState(state)

def selectCharger(chargers):
    run = True
    x = 0
    y = 0
    charger = 0
    chargerArray = chargers 
    sense.set_pixel(x, y, white)
    sense.set_pixel(x, y+1, white)

    while run:
        event = sense.stick.wait_for_event()
        if event.direction == "up" and event.action == "pressed":
            sense.set_pixel(x, y, clear)
            sense.set_pixel(x, y+1, clear)
            y = y-2
            charger = charger-1
            if y < 0:
                y = 6
                charger = 3
            sense.set_pixel(x, y, white)
            sense.set_pixel(x, y+1, white)
        elif event.direction == "down" and event.action == "pressed":
            sense.set_pixel(x, y, clear)
            sense.set_pixel(x, y+1, clear)
            y = y+2
            charger = charger+1
            if y > 6:
                y = 0
                charger = 0
            sense.set_pixel(x, y, white)
            sense.set_pixel(x, y+1, white)
        elif event.direction == "middle" and event.action == "pressed":
            if chargerArray[charger].getConnected() == "connected":
                run = False
            else:
                print("Error: charger not connected")
                sense.set_pixel(x, y, red)
                sense.set_pixel(x, y+1, red)
                t.sleep(0.5)
                sense.set_pixel(x, y, white)
                sense.set_pixel(x, y+1, white)
                t.sleep(0.5)
                sense.set_pixel(x, y, red)
                sense.set_pixel(x, y+1, red)
                t.sleep(0.5)
                sense.set_pixel(x, y, white)
                sense.set_pixel(x, y+1, white)
        t.sleep(0.5)

    changeChargerState(chargerArray[charger], "charging")


    

def main():
    sense.clear()

    

    threads = [charger(i) for i in range(4)]
    for thread in threads:
        thread.start()

    selection = Thread(target = selectCharger, args = (threads))
    selection.start()

    run = True

    while run:
        for i in threads:
            if i.chargerState == "charging":
                i.chargingState()
            elif i.chargerState == "error":
                i.errorState()
            elif i.chargerState == "finished":
                i.finishedState()
            elif i.chargerState == "idle":
                i.idleState()
    



        
            


main()