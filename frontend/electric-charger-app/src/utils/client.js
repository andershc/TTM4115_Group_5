import mqtt from "mqtt";

const MQTT_BROKER = "broker.hivemq.com";
const MQTT_PORT = 8000; // WebSocket port

function createClient() {
    const url = `ws://${MQTT_BROKER}:${MQTT_PORT}/mqtt`;  // Use WebSocket protocol
    const options = {
        clientId: "web-" + Math.random().toString(16).substr(2, 8),
        clean: true,
    };

    let client = mqtt.connect(url, options);
    client.on("connect", function () {
        console.log("Connected to MQTT broker via WebSocket");
    });

    client.on("error", (err) => {
        console.error("Connection error: ", err);
        client.end();
    });

    client.on("reconnect", () => {
        console.log("Reconnecting...");
    });

    // Handle incoming messages
    client.on("message", (topic, message) => {
        console.log(`Message received on topic '${topic}': ${message.toString()}`);
    });

    return client;
}

export const CLIENT = createClient();