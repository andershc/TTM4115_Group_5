Idle
Start_lading
Ferdig_lading
Error_lading

from sense_hat import SenseHat
import random 
sense = SenseHat()

red = (255,0,0)
green = (0,255,0)
blue = (0,0,255)
white = (255,255,255)
clear = (0,0,0)

def checkForConnection():
    

def select_charger(charger_id = 0):
    run = True
    x = 0
    y = select_charger*2
    charger = select_charger 
    sense.set_pixel(x, y, white)
    sense.set_pixel(x, y+1, white)

    while run:
        event = sense.stick.get_event()
        if event.direction == "up":
            sense.set_pixel(x, y, clear)
            sense.set_pixel(x, y+1, clear)
            y = y-2
            charger = charger-1
            if y < 0:
                y = 6
                charger = 3
            sense.set_pixel(x, y, white)
            sense.set_pixel(x, y+1, white)
        elif event.direction == "down":
            sense.set_pixel(x, y, clear)
            sense.set_pixel(x, y+1, clear)
            y = y+2
            charger = charger+1
            if y > 6:
                y = 0
                charger = 0
            sense.set_pixel(x, y, white)
            sense.set_pixel(x, y+1, white)
        elif event.action == "pressed":
            if getChargerState(charger) == "connected":
                run = False
            else:
                print("Error: charger not connected")
                sense.set_pixel(x, y, red)
                sense.set_pixel(x, y+1, red)
                sleep(0.5)
                sense.set_pixel(x, y, white)
                sense.set_pixel(x, y+1, white)
                sleep(0.5)
                sense.set_pixel(x, y, red)
                sense.set_pixel(x, y+1, red)
                sleep(0.5)
                sense.set_pixel(x, y, white)
                sense.set_pixel(x, y+1, white)
        sleep(0.1)

    changeState(start_charging(charger))


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
    chargeTimeOut = 0
    is_error = random.randint(0,11)
    if is_error == 5:
        changeState(error_charger(charger))
    print("Started charging on charger ", charger_id)
    while run:
        while chargeTimeOut!= 100:
            sense.set_pixel(x, y, clear)
            sense.set_pixel(x, y+1, clear)
            sleep(0.5)
            sense.set_pixel(x, y, green)
            sense.set_pixel(x, y+1, green)
            chargeTime = chargeTime+1
        x = x+1
        chargeTimeOut = 0
        if x == 7:
            run = False
    changeState(finished_charging(charger))
        
def error_charger(charger_id):
    print("Charging error on ", charger_id)
    run = True
    x = 0
    y = charger_id*2
    for i in range(1,8):
        sense.set_pixel(i, y, red)
        sense.set_pixel(i, y+1, red)
    setChargerState(charger_id, "error")
    while run:
        print("error loop")
        
    
    

def finished_charging(charger_id):
    print("Finished charging on charger ", charger_id)
    run = True
    x = 0
    y = charger_id*2
    setChargerState(charger_id, "finished")
    while run:
        event = sense.stick.get_event()
        if event.action == "pressed" or getCallFromServer() == "stop":
            for i in range(1,8):
                sense.set_pixel(i, y, clear)
                sense.set_pixel(i, y+1, clear)
