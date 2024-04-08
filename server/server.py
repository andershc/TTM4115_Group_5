import paho.mqtt.client as mqtt
import stmpy
import logging
from threading import Thread
import json

# TODO: choose proper MQTT broker address
MQTT_BROKER = "broker.emqx.io"
MQTT_PORT = 1883

# TODO: choose proper topics for communication
MQTT_TOPIC_INPUT = "ttm4115/team_05/command"
MQTT_TOPIC_OUTPUT = "ttm4115/team_05/answer"


class TimerLogic:
    """
    State Machine for a named timer.

    This is the support object for a state machine that models a single timer.
    """

    def __init__(self, name, duration, component):
        self._logger = logging.getLogger(__name__)
        self.name = name
        self.duration = duration
        self.component = component

        # TODO: build the transitions
        t0 = {
            "source": "initial",
            "target": "active",
        }
        t1 = {
            "source": "active",
            "target": "completed",
            "trigger": "t",
            "effect": "send_notification",
        }
        t2 = {
            "source": "active",
            "trigger": "report",
            "target": "active",
            "effect": "cancel_timer",
        }

        self.stm = stmpy.Machine(name=name, transitions=[t0, t1, t2], obj=self)

    # TODO define functions as transition effetcs

    def send_notification(self):
        self._logger.debug("Timer {} expired".format(self.name))

    def cancel_timer(self):
        self._logger.debug("Cancelling timer for {}".format(self.name))
        self.timer_thread.cancel()

    def report_status(self):
        self._logger.debug("Checking timer status.".format(self.name))
        time = int(self.stm.get_timer("t") / 1000)
        message = "Timer {} has about {} seconds left".format(self.name, time)
        self.component.mqtt_client.publish(MQTT_TOPIC_OUTPUT, message)


class ChargerComponent:
    """
    The component to manage the status of the chargers.

    """

    def on_connect(self, client, userdata, flags, rc):
        # we just log that we are connected
        self._logger.debug("MQTT connected to {}".format(client))

    def on_message(self, client, userdata, msg):
        """
        Processes incoming MQTT messages.

        We assume the payload of all received MQTT messages is an UTF-8 encoded
        string, which is formatted as a JSON object. The JSON object contains
        a field called `command` which identifies what the message should achieve.

        As a reaction to a received message, we can for example do the following:

        * create a new state machine instance to handle the incoming messages,
        * route the message to an existing state machine session,
        * handle the message right here,
        * throw the message away.

        """
        self._logger.debug("Incoming message to topic {}".format(msg.topic))

        # TODO unwrap JSON-encoded payload
        payload = json.loads(msg.payload.decode("utf-8"))

        # TODO extract command
        command = payload["command"]
        self._logger.debug("Received command: {}".format(command))

        # TODO determine what to do

        if command == "new_charger":
            # create a new state machine for the timer
            name = payload["name"]
            duration = payload["duration"]
            print(
                "Creating new timer with name {} and duration {}".format(name, duration)
            )
            timer_logic = TimerLogic(name=name, duration=duration, component=self)

            self.stm_driver.add_machine(timer_logic.stm)
            timer_logic.stm.start_timer("t", duration)
            self._logger.debug("Added state machine for timer {}".format(name))

        elif command == "status_all_timers":
            # send status of all timers
            self._logger.debug("Sending status of all timers")
            # Route the message to an existing state machine session and send status
            print("Sending status of all timers")
            print(self.stm_driver.print_status())

            self.mqtt_client.publish(
                MQTT_TOPIC_OUTPUT, json.dumps(self.stm_driver.print_status())
            )

        elif command == "status_single_timer":
            # send status of a single timer
            name = payload["name"]
            self._logger.debug("Sending status of timer {}".format(name))
            # Route the message to an existing state machine session and send status

            stm = self.stm_driver._stms_by_id[name]

            print(stm)
            print(self.stm_driver._timer_queue)

            self.mqtt_client.publish(
                MQTT_TOPIC_OUTPUT,
                json.dumps(self.stm_driver._get_timer("t", stm)),
            )

        elif command == "cancel_timer":
            # cancel a single timer
            name = payload["name"]
            self._logger.debug("Cancelling timer {}".format(name))
            # Route the message to an existing state machine session and cancel timer
            stm = self.stm_driver._stms_by_id[name]
            self.stm_driver._stop_timer("t", stm)
            self.mqtt_client.publish(
                MQTT_TOPIC_OUTPUT, "Timer {} has been cancelled".format(name)
            )

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
            "Connecting to MQTT broker {} at port {}".format(MQTT_BROKER, MQTT_PORT)
        )
        self.mqtt_client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION1
        )
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

    def stop(self):
        """
        Stop the component.
        """
        # stop the MQTT client
        self.mqtt_client.loop_stop()

        # stop the state machine Driver
        self.stm_driver.stop()


# logging.DEBUG: Most fine-grained logging, printing everything
# logging.INFO:  Only the most important informational log items
# logging.WARN:  Show only warnings and errors.
# logging.ERROR: Show only error messages.
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

t = TimerManagerComponent()
