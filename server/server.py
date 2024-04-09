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
            "effect": "start_charging",
        }  # Payment done
        t4 = {
            "source": "charger_selected",
            "target": "selecting",
            "trigger": "disconnect_charger",
            "effect": "disconnect_charger",
        }  # Charger disconnected

        self.stm = stmpy.Machine(name=name, transitions=[t0, t1, t2, t3, t4], obj=self)

    def show_chargers(self):
        self._logger.debug("Showing chargers")
        # Get the available chargers from the database
        file_path = "server/db/chargers.json"
        with open(file_path, "r") as file:
            data = json.load(file)
            chargers = data["chargers"]
            # Filter out the chargers that are already in use
            for charger in chargers:
                if charger["status"] != "AVAILABLE":
                    chargers.remove(charger)
            # Send a message with the chargers to the user
            self.client.publish(MQTT_TOPIC_OUTPUT, "Chargers: {}".format(chargers))

    def update_selected_charger(self, selected_charger: int):
        self._logger.debug("Updating selected charger")
        # Update the status of the selected charger in the database
        file_path = "server/db/chargers.json"
        print(selected_charger)

        # Update the status of the selected charger in the database
        with open(file_path, "r") as file:
            data = json.load(file)
            for charger in data["chargers"]:
                if charger["id"] == selected_charger:
                    charger["status"] = "OCCUPIED"
                    break

        with open(file_path, "w") as file:
            json.dump(data, file)

        self.show_chargers()

    def pay(self):
        self._logger.debug("Paying")

    def disconnect_charger(self):
        self._logger.debug("Disconnecting charger")

    def start_charging(self):
        self._logger.debug("Starting charging")

    def stop_charging(self):
        self._logger.debug("Stopping charging")
        self.timer_thread.cancel()


class ChargingSessionComponent:
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

        elif command == "select_charger":
            """
            Recieve a message to select a charger. Data should include the user's email and the charger.
            Then send a message to the charger server to select the charger.
            """
            if "email" in payload and "charger" in payload:
                self._logger.debug(
                    "Selecting charger {} for user with email {}".format(
                        payload["charger"], payload["email"]
                    )
                )

                self.stm_driver.send(
                    message_id="select_charger",
                    stm_id="session_" + payload["email"],
                    args=[payload["charger"]],
                )
                return

            self._logger.debug("Missing email or charger in payload")

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

t = ChargingSessionComponent()
