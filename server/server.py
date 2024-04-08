import uuid
import paho.mqtt.client as mqtt
import stmpy
import logging
from threading import Thread
import json

# TODO: choose proper MQTT broker address
MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883

# TODO: choose proper topics for communication
MQTT_TOPIC_INPUT = "ttm4115/team_05/command"
MQTT_TOPIC_OUTPUT = "ttm4115/team_05/answer"


class ChargerServerLogic:
    """
    State Machine for a session in the charging app.
    """

    def __init__(self, name, component):
        self._logger = logging.getLogger(__name__)
        self.name = name
        self.component = component

        # TODO: build the transitions
        t0 = {
            "source": "initial",
            "target": "selecting",
        }  # Initial state
        t1 = {
            "source": "selecting",
            "target": "charger_selected",
            "trigger": "select_charger",
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
            "effect": "start_charging",
        }  # Payment done
        t4 = {
            "source": "charger_selected",
            "target": "selecting",
            "trigger": "disconnect_charger",
            "effect": "disconnect_charger",
        }  # Charger disconnected

        self.stm = stmpy.Machine(name=name, transitions=[t0, t1, t2, t3, t4], obj=self)

    def select_charger(self):
        self._logger.debug("Selecting charger")

    def pay(self):
        self._logger.debug("Paying")

    def disconnect_charger(self):
        self._logger.debug("Disconnecting charger")

    def start_charging(self):
        self._logger.debug("Starting charging")

    def stop_charging(self):
        self._logger.debug("Stopping charging")
        self.timer_thread.cancel()


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
            "Connecting to MQTT broker {} at port {}".format(MQTT_BROKER, MQTT_PORT)
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


class UserManagementComponent:
    """
    Component for registering and managing users.

    """

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

        if command == "register_user":
            """
            Recieve a message to register a user. Data should include the user's name and email.
            Then store the user in the database (db/users.json) with a unique ID.
            """
            name = payload["name"]
            email = payload["email"]
            # Store the user in the database with a unique ID.
            file_path = "server/db/users.json"

            self._logger.debug(
                "Registering user with name {} and email {}".format(name, email)
            )

            # Check there is a user with the same email or name
            with open(file_path, "r") as file:
                data = json.load(file)
                for user in data["users"]:
                    if user["email"] == email or user["name"] == name:
                        self._logger.debug(
                            "User with email {} already exists".format(email)
                        )
                        self.mqtt_client.publish(
                            MQTT_TOPIC_OUTPUT,
                            "User with email {} already exists".format(email),
                        )
                        return

            # Store the data in the json file
            with open(file_path, "r") as file:
                data = json.load(file)
                data["users"].append(
                    {"name": name, "email": email, "id": str(uuid.uuid4())}
                )

            with open(file_path, "w") as file:
                json.dump(data, file)

            # Send a message to the user with the unique ID.
            self._logger.debug(
                "Registering user with name {} and email {}".format(name, email)
            )
            # Send a message to the user with the unique ID.
            self.mqtt_client.publish(
                MQTT_TOPIC_OUTPUT, "User {} has been registered".format(name)
            )

        elif command == "login":
            """
            Recieve a message to login a user. Data should include the user's email.
            Then check if the user is in the database (db/users.json) and send a message with the user's ID.
            """
            email = payload["email"]
            # Check if the user is in the database (db/users.json) and send a message with the user's ID.
            file_path = "server/db/users.json"

            self._logger.debug("Logging in user with email {}".format(email))

            with open(file_path, "r") as file:
                data = json.load(file)
                for user in data["users"]:
                    if user["email"] == email:
                        self._logger.debug(
                            "User with email {} has been logged in".format(email)
                        )
                        self.mqtt_client.publish(
                            MQTT_TOPIC_OUTPUT,
                            "User with email {} has been logged in".format(email),
                        )
                        # Add the state machine for the charger server with a session ID based on the amount of sessions
                        sessionID = "session_" + email
                        self._logger.debug(
                            "Adding state machine for charger server with session ID {}".format(
                                sessionID
                            )
                        )
                        charger_server_logic = ChargerServerLogic(sessionID, self)
                        self.stm_driver.add_machine(charger_server_logic.stm)

                        return

            self._logger.debug(
                "User with email {} does not exist in the database".format(email)
            )

            self.mqtt_client.publish(
                MQTT_TOPIC_OUTPUT,
                "User with email {} does not exist in the database".format(email),
            )

        elif command == "logout":
            """
            Recieve a message to logout a user. Data should include the user's email.
            Then check if the user is in the database (db/users.json) and send a message with the user's ID.
            """
            email = payload["email"]
            # Check if the user is in the database (db/users.json) and send a message with the user's ID.
            file_path = "server/db/users.json"

            self._logger.debug("Logging out user with email {}".format(email))

            with open(file_path, "r") as file:
                data = json.load(file)
                for user in data["users"]:
                    if user["email"] == email:
                        # Stop the state machine for the charger server
                        sessionID = "session_" + email
                        self._logger.debug(
                            "Stopping state machine for charger server with session ID {}".format(
                                sessionID
                            )
                        )
                        self.stm_driver.stop_machine(sessionID)

                        self._logger.debug(
                            "User with email {} has been logged out".format(email)
                        )
                        self.mqtt_client.publish(
                            MQTT_TOPIC_OUTPUT,
                            "User with email {} has been logged out".format(email),
                        )

                        return

            self._logger.debug(
                "User with email {} does not exist in the database".format(email)
            )

            self.mqtt_client.publish(
                MQTT_TOPIC_OUTPUT,
                "User with email {} does not exist in the database".format(email),
            )

    def stop(self):
        """
        Stop the component.
        """
        # stop the MQTT client
        self.mqtt_client.loop_stop()


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

t = UserManagementComponent()
