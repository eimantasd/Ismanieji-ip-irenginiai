import paho.mqtt.client as mqtt
import subprocess
import os
import json # Still useful for sending structured responses

# MQTT Configuration
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
CLIENT_ID = "LinuxSystemAgentSimpleInput"

# --- Define Single Topics ---
COMMAND_TOPIC = "dictionary/word/query"
RESPONSE_TOPIC = "dictionary/word/meaning"

# --- Command Execution Functions (mostly unchanged) ---

def execute_command(command_array):
    try:
        process = subprocess.run(command_array, capture_output=True, text=True, check=False, timeout=10)
        if process.returncode == 0:
            return process.stdout.strip()
        else:
            return f"Error: Command failed with code {process.returncode}\nStderr: {process.stderr.strip()}"
    except subprocess.TimeoutExpired:
        return "Error: Command timed out."
    except Exception as e:
        return f"Error executing command: {str(e)}"

def list_directory_content(path_arg=None):
    path = path_arg.strip() if path_arg else "."
    if not os.path.isdir(path):
        return f"Error: '{path}' is not a valid directory."
    return execute_command(['ls', '-lah', path])

def get_ip_addresses():
    return execute_command(['ip', 'addr'])

def get_free_memory():
    return execute_command(['free', '-h'])

def create_new_file(filename, content):
    try:
        filename = filename.strip()
        if ".." in filename or "/" in filename or "\\" in filename:
            return "Error: Invalid filename. Cannot contain path separators or '..'."
        if not filename:
            return "Error: Filename cannot be empty."
        filepath = os.path.join(os.getcwd(), filename)
        with open(filepath, 'w') as f:
            f.write(content)
        return f"Success: File '{filename}' created at '{filepath}'."
    except Exception as e:
        return f"Error creating file: {str(e)}"

# --- MQTT Callbacks ---

def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print(f"Connected to MQTT Broker: {MQTT_BROKER}")
        client.subscribe(COMMAND_TOPIC)
        print(f"Subscribed to command topic: {COMMAND_TOPIC}")
    else:
        print(f"Failed to connect, reason code {reason_code}")

def on_message(client, userdata, msg):
    payload_str = msg.payload.decode("utf-8").strip()
    print(f"\nReceived command string: '{payload_str}'")

    parts = payload_str.split(maxsplit=2) # Max split for create_file: command, filename, content
    command_name_from_user = parts[0].lower() if parts else ""
    
    response_data = "Error: Unknown command or internal error."
    status = "error"
    command_echo = command_name_from_user # Echo back what the user typed as command

    try:
        if not command_name_from_user:
            response_data = "Error: Empty command received."
        
        elif command_name_from_user in ["ls", "list_directory"]:
            path_to_list = parts[1] if len(parts) > 1 else None
            response_data = list_directory_content(path_to_list)
            status = "success" if not response_data.startswith("Error:") else "error"
        
        elif command_name_from_user in ["ip", "get_ip_address"]:
            response_data = get_ip_addresses()
            status = "success" if not response_data.startswith("Error:") else "error"

        elif command_name_from_user in ["mem", "get_free_memory"]:
            response_data = get_free_memory()
            status = "success" if not response_data.startswith("Error:") else "error"

        elif command_name_from_user in ["mkfile", "create_file"]:
            if len(parts) >= 2: # Need at least command and filename
                filename = parts[1]
                content = parts[2] if len(parts) > 2 else "" # Content is optional or can be empty
                response_data = create_new_file(filename, content)
                status = "success" if response_data.startswith("Success:") else "error"
            else:
                response_data = "Error: 'create_file' (or 'mkfile') requires a filename. Usage: mkfile <filename> [content]"
                status = "error"
        
        else:
            response_data = f"Error: Unknown command '{command_name_from_user}'."
            status = "error"

    except Exception as e:
        response_data = f"Error processing command: {str(e)}"
        status = "error"

    # We still send a JSON response because it's structured and easy for the app to parse
    # even if the input is simple text.
    response_payload = {
        "status": status,
        "command_echo": command_echo,
        "data": response_data
    }
    client.publish(RESPONSE_TOPIC, json.dumps(response_payload))
    print(f"Published response to '{RESPONSE_TOPIC}': {json.dumps(response_payload)}")


# --- Main Script ---
if __name__ == "__main__":
    client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2, client_id=CLIENT_ID)
    
    client.on_connect = on_connect
    client.on_message = on_message

    print(f"Attempting to connect to MQTT broker: {MQTT_BROKER} on port {MQTT_PORT}...")
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
    except Exception as e:
        print(f"Could not connect to MQTT broker: {e}")
        exit(1)

    try:
        client.loop_forever()
    except KeyboardInterrupt:
        print("\nDisconnecting from MQTT broker...")
    finally:
        client.disconnect()
        print("Disconnected.")
