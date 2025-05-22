import paho.mqtt.client as mqtt
from dictionary_client import get_word_meaning  # Import the function from our other file

# MQTT Configuration
MQTT_BROKER = "192.168.83.107"  # Or "test.mosquitto.org" or your own broker
MQTT_PORT = 1883
# CLIENT_ID = "DictionaryLookupClient" # This will be set in the constructor now

# Topics
TOPIC_WORD_QUERY = "dictionary/word/query"  # Topic to listen for words from Expo app
TOPIC_WORD_MEANING = "dictionary/word/meaning"  # Topic to publish meanings back to Expo app


def on_connect(client, userdata, flags, rc):
    """Callback for when the client connects to the broker."""
    if rc == 0:
        print(f"Connected successfully to MQTT Broker: {MQTT_BROKER}")
        # Subscribe to the topic where words will be sent
        client.subscribe(TOPIC_WORD_QUERY)
        print(f"Subscribed to topic: {TOPIC_WORD_QUERY}")
    else:
        print(f"Failed to connect, return code {rc}\n")


def on_message(client, userdata, message):
    """Callback for when a message is received from the broker."""
    try:
        word_to_search = message.payload.decode("utf-8")
        print(f"\nReceived word: '{word_to_search}' on topic '{message.topic}'")

        if word_to_search:
            print(f"Looking up meaning for '{word_to_search}'...")
            meaning = get_word_meaning(word_to_search)

            print(f"Publishing meaning to topic: {TOPIC_WORD_MEANING}")
            # Log first 200 chars of meaning if it's long
            log_meaning = meaning if len(meaning) < 200 else meaning[:200] + "..."
            print(f"Meaning snippet: {log_meaning}")

            client.publish(TOPIC_WORD_MEANING, str(meaning))
        else:
            print("Received an empty message. No word to search.")
            client.publish(TOPIC_WORD_MEANING, "Error: Received an empty word to search.")

    except Exception as e:
        print(f"Error processing message or fetching meaning: {e}")
        client.publish(TOPIC_WORD_MEANING, f"Error processing request: {e}")


# --- Main script execution ---
if __name__ == "__main__":
    # MODIFICATION HERE: Specify callback_api_version and client_id
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, client_id="DictionaryLookupClient")

    client.on_connect = on_connect
    client.on_message = on_message

    print(f"Attempting to connect to MQTT broker: {MQTT_BROKER}...")
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
    except Exception as e:
        print(f"Could not connect to MQTT broker: {e}")
        exit()

    # Start the loop to process network traffic, dispatch callbacks, and handle reconnecting.
    try:
        client.loop_forever()
    except KeyboardInterrupt:
        print("\nDisconnecting from MQTT broker...")
        client.disconnect()
        print("Disconnected.")