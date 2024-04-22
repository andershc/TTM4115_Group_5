import datetime
import uuid
import paho.mqtt.client as mqtt
import stmpy
import logging
from threading import Thread
import json

MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883

MQTT_TOPIC_INPUT = "ttm4115/team_05/charger/command"
MQTT_TOPIC_OUTPUT = "ttm4115/team_05/charger/answer"


class ChargerLogic:
    """
    State machine for the charger
    """

    def __init__(self, name, component):
        self._logger = logging.getLogger(__name__)
        self.name = name
        self.component = component
        self.client = component.mqtt_client

        # TODO: build the transitions
        t0 = {
            "source": "initial",
            "target": "selecting",
            "effect": "show_chargers",
        }  # Initial state
        t1 = {
            "source": "selecting",
            "target": "charger_selected",
            "trigger": "select_charger",
            "effect": "update_selected_charger(*)",
        }  # Charger selected
        t2 = {
            "source": "charging",
            "target": "selecting",
            "trigger": "t",
            "effect": "stop_charging",
        }  # Charging stopped
        t3 = {
            "source": "charger_selected",
            "target": "charging",
            "trigger": "pay",
            "effect": "start_charging(*)",
        }  # Payment done
        t4 = {
            "source": "charger_selected",
            "target": "selecting",
            "trigger": "disconnect_charger",
            "effect": "disconnect_charger",
        }  # Charger disconnected

        self.stm = stmpy.Machine(name=name, transitions=[t0, t1, t2, t3, t4], obj=self)


class ChargerComponent:
    def __init__(self):
        """
        Start the component.

        ## Start of MQTT
        We subscribe to the topic(s) the component listens to.
        The client is available as variable `self.client` so that subscriptions
        may also be changed over time if necessary.

        The MQTT client reconnects in case of failures.

        ## State Machine driver
        We create a single state machine driver for STMPY. This should fit
        for most components. The driver is available from the variable
        `self.driver`. You can use it to send signals into specific state
        machines, for instance.

        """
        # get the logger object for the component
        self._logger = logging.getLogger(__name__)
        print("logging under name {}.".format(__name__))
        self._logger.info("Starting Component")

        # create a new MQTT client
        self._logger.debug(
            "Connecting to MQTT broker {} at port {}".format(MQTT_BROKER, MQTT_PORT)
        )
        self.mqtt_client = mqtt.Client()
        # callback methods
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message
        # Connect to the broker
        self.mqtt_client.connect(MQTT_BROKER, MQTT_PORT)
        # subscribe to proper topic(s) of your choice
        self.mqtt_client.subscribe(MQTT_TOPIC_INPUT)
        # start the internal loop to process MQTT messages
        self.mqtt_client.loop_start()

        # we start the stmpy driver, without any state machines for now
        self.stm_driver = stmpy.Driver()
        self.stm_driver.start(keep_active=True)
        self._logger.debug("Component initialization finished")

    def on_connect(self, client, userdata, flags, rc):
        # we just log that we are connected
        self._logger.debug("MQTT connected to {}".format(client))

    def on_message(self, client, userdata, msg):
        """
        Processes incoming MQTT messages.

        We assume the payload of all received MQTT messages is an UTF-8 encoded
        string, which is formatted as a JSON object. The JSON object contains
        a field called `command` which identifies what the message should achieve.
        """

        self._logger.debug("Incoming message to topic {}".format(msg.topic))

        payload = json.loads(msg.payload.decode("utf-8"))
        command = payload["command"]

        if command == "select_charger":
            self._logger.debug("Selecting charger")
            self.stm_driver.send("charger_logic", "select_charger")


debug_level = logging.DEBUG
logger = logging.getLogger(__name__)
logger.setLevel(debug_level)
ch = logging.StreamHandler()
ch.setLevel(debug_level)
formatter = logging.Formatter(
    "%(asctime)s - %(name)-12s - %(levelname)-8s - %(message)s"
)
ch.setFormatter(formatter)
logger.addHandler(ch)

t = ChargerComponent()
