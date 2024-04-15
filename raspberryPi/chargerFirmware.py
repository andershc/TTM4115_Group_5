from sense_hat import SenseHat
import time as t
import random 
sense = SenseHat()

red = (255,0,0)
green = (0,255,0)
blue = (0,0,255)
white = (255,255,255)
clear = (0,0,0)
sense.clear()
chargerState = "idle"
def getConnected():
    return "connected"

def getChargerState(charger):
    return chargerState

def changeState(state):
    chargerState = state
    print(chargerState)
    
def checkForConnection():
    print("check for connection")

def select_charger(charger_id = 0):
    run = True
    x = 0
    y = charger_id*2
    charger = charger_id
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
            if getConnected() == "connected":
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

    changeState("charging")
    start_charging(charger)

def start_charging(charger_id):
    run = True
    x = 0
    y = charger_id*2
    charger = charger_id
    stateOfCharge = random.randint(1,6)
    for i in range(0,stateOfCharge):
        sense.set_pixel(i, y, green)
        sense.set_pixel(i, y+1, green)
        x = i
    x = x+1
    chargeTime = 0
    is_error = random.randint(0,11)
    if is_error == 5:
        changeState(error_charger(charger))
    print("Started charging on charger ", charger_id)
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
    finished_charging(charger)


def error_charger(charger_id):
    print("Charging error on ", charger_id)
    run = True
    x = 0
    y = charger_id*2
    for i in range(1,8):
        sense.set_pixel(i, y, red)
        sense.set_pixel(i, y+1, red)
    changeState("error")
    while run:
        print("error loop")
        
    
    

def finished_charging(charger_id):
    print("Finished charging on charger ", charger_id)
    run = True
    x = 0
    y = charger_id*2
    changeState("finished")
    while run:
        event = sense.stick.wait_for_event()
        if event.direction == "middle" and event.action == "pressed":
            for i in range(0,8):
                sense.set_pixel(i, y, clear)
                sense.set_pixel(i, y+1, clear)

def main():
    select_charger()

main()