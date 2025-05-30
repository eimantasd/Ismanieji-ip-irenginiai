from flask import Flask, jsonify, send_file, render_template_string
import requests
import json
import paho.mqtt.client as mqtt
import time
import threading
from datetime import datetime

# Konfigūracija
DICTIONARY_API_URL = "https://api.dictionaryapi.dev/api/v2/entries/en/"
MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883
MQTT_TOPIC = "dictionary/words"
CLIENT_NAME = "dictionary_client_" + str(int(time.time()))

app = Flask(__name__)

# Globalus kintamasis MQTT žinutėms saugoti
mqtt_messages = []

# HTML šablonas žinučių atvaizdavimui
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Dictionary API + MQTT Integration</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .container { max-width: 800px; margin: 0 auto; }
        .section { margin: 20px 0; padding: 20px; border: 1px solid #ddd; border-radius: 5px; }
        .json-display { background: #f5f5f5; padding: 15px; border-radius: 5px; white-space: pre-wrap; }
        .message { background: #e8f4fd; padding: 10px; margin: 5px 0; border-radius: 3px; }
        button { padding: 10px 20px; margin: 5px; background: #007bff; color: white; border: none; border-radius: 3px; cursor: pointer; }
        button:hover { background: #0056b3; }
        input { padding: 8px; margin: 5px; border: 1px solid #ddd; border-radius: 3px; }
    </style>
    <script>
        function refreshMessages() {
            fetch('/mqtt_messages_json')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('mqtt-messages').innerHTML = 
                        data.map(msg => `<div class="message">
                            <strong>${msg.timestamp}</strong><br>
                            Topic: ${msg.topic}<br>
                            Message: <pre>${JSON.stringify(msg.payload, null, 2)}</pre>
                        </div>`).join('');
                });
        }
        
        function lookupWord() {
            const word = document.getElementById('word-input').value;
            if (word) {
                fetch(`/lookup/${word}`)
                    .then(response => response.json())
                    .then(data => {
                        document.getElementById('dictionary-result').innerHTML = 
                            `<pre>${JSON.stringify(data, null, 2)}</pre>`;
                    });
            }
        }
        
        setInterval(refreshMessages, 3000); // Atnaujinti kas 3 sekundes
    </script>
</head>
<body>
    <div class="container">
        <h1>Dictionary API + MQTT Integration</h1>
        
        <div class="section">
            <h2>Žodžio paieška (Dictionary API)</h2>
            <input type="text" id="word-input" placeholder="Įveskite žodį anglų kalba" />
            <button onclick="lookupWord()">Ieškoti</button>
            <div id="dictionary-result" class="json-display"></div>
        </div>
        
        <div class="section">
            <h2>MQTT žinutės</h2>
            <button onclick="refreshMessages()">Atnaujinti žinutes</button>
            <div id="mqtt-messages"></div>
        </div>
        
        <div class="section">
            <h2>Nuorodos</h2>
            <button onclick="window.open('/api', '_blank')">Atsisiųsti api.json</button>
            <button onclick="window.open('/mqtt_messages_json', '_blank')">MQTT žinutės (JSON)</button>
        </div>
    </div>
    
    <script>
        // Pradinis žinučių įkėlimas
        refreshMessages();
    </script>
</body>
</html>
"""

def jprint(data):
    """Gražiai atspausdina JSON duomenis"""
    text = json.dumps(data, sort_keys=True, indent=4, ensure_ascii=False)
    print(text)

def on_connect(client, userdata, flags, rc, properties=None):
    """MQTT prisijungimo callback"""
    print(f"Prisijungta prie MQTT brokerio su kodu: {rc}")
    client.subscribe(MQTT_TOPIC)
    print(f"Prenumeruojama tema: {MQTT_TOPIC}")

def on_message(client, userdata, msg):
    """MQTT žinutės gavimo callback"""
    try:
        payload = json.loads(msg.payload.decode())
        message_data = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "topic": msg.topic,
            "payload": payload
        }
        mqtt_messages.append(message_data)
        print(f"Gauta MQTT žinutė iš temos {msg.topic}")
        jprint(payload)
        
        # Saugoti tik paskutines 10 žinučių
        if len(mqtt_messages) > 10:
            mqtt_messages.pop(0)
            
    except Exception as e:
        print(f"Klaida apdorojant MQTT žinutę: {e}")

def setup_mqtt_client():
    """Sukuria ir konfigūruoja MQTT klientą"""
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, CLIENT_NAME)
    client.on_connect = on_connect
    client.on_message = on_message
    
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_start()
        print("MQTT klientas paleistas")
        return client
    except Exception as e:
        print(f"Nepavyko prisijungti prie MQTT brokerio: {e}")
        return None

def lookup_word_api(word):
    """Ieško žodžio reikšmės naudojant Dictionary API"""
    try:
        url = f"{DICTIONARY_API_URL}{word}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"Žodis '{word}' nerastas arba API klaida", "status_code": response.status_code}
    except Exception as e:
        return {"error": f"API užklausos klaida: {str(e)}"}

def save_to_json_file(data, filename="api.json"):
    """Išsaugo duomenis į JSON failą"""
    try:
        # Pridedame papildomą informaciją
        data_with_meta = {
            "timestamp": datetime.now().isoformat(),
            "source": "Dictionary API",
            "client_info": "Python Dictionary MQTT Integration",
            "data": data
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data_with_meta, f, indent=4, ensure_ascii=False)
        print(f"Duomenys išsaugoti į {filename}")
        return data_with_meta
    except Exception as e:
        print(f"Klaida saugant failą: {e}")
        return None

# Inicializuojame MQTT klientą
mqtt_client = setup_mqtt_client()

@app.route('/')
def home():
    """Pagrindinis puslapis"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/lookup/<word>')
def lookup_word(word):
    """API endpoint žodžio paieškai"""
    print(f"Ieškomas žodis: {word}")
    
    # Gauname duomenis iš Dictionary API
    api_data = lookup_word_api(word)
    jprint(api_data)
    
    # Išsaugome į JSON failą
    saved_data = save_to_json_file(api_data)
    
    # Siunčiame į MQTT, jei klientas prisijungęs
    if mqtt_client and saved_data:
        try:
            mqtt_client.publish(MQTT_TOPIC, json.dumps(saved_data))
            print(f"Duomenys išsiųsti į MQTT temą: {MQTT_TOPIC}")
        except Exception as e:
            print(f"MQTT siuntimo klaida: {e}")
    
    return jsonify(api_data)

@app.route('/search/<word>')
def search_word_demo(word):
    """Demonstracinis endpoint - iš karto atlieka paiešką ir atvaizdavimą"""
    return lookup_word(word)

@app.route('/api')
def send_api_file():
    """Siunčia JSON failą atsisiuntimui"""
    try:
        return send_file('api.json', as_attachment=True)
    except FileNotFoundError:
        return jsonify({"error": "api.json failas nerastas. Pirmiau atlikite žodžio paiešką."}), 404

@app.route('/mqtt_messages_json')
def get_mqtt_messages_json():
    """Grąžina MQTT žinutes JSON formatu"""
    return jsonify(mqtt_messages)

@app.route('/mqtt_messages')
def get_mqtt_messages():
    """Atvaizdoja MQTT žinutes"""
    return jsonify({
        "total_messages": len(mqtt_messages),
        "messages": mqtt_messages
    })

@app.route('/test_mqtt')
def test_mqtt():
    """Testuoja MQTT siuntimą"""
    test_message = {
        "test": True,
        "timestamp": datetime.now().isoformat(),
        "message": "Test žinutė iš Flask aplikacijos"
    }
    
    if mqtt_client:
        try:
            mqtt_client.publish(MQTT_TOPIC, json.dumps(test_message))
            return jsonify({"status": "success", "message": "Test žinutė išsiųsta į MQTT"})
        except Exception as e:
            return jsonify({"status": "error", "message": f"MQTT klaida: {e}"})
    else:
        return jsonify({"status": "error", "message": "MQTT klientas neprisijungęs"})

def cleanup():
    """Išvaloma išteklius"""
    if mqtt_client:
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
        print("MQTT klientas atjungtas")

if __name__ == '__main__':
    try:
        print("=== Dictionary API + MQTT Integration prasideda ===")
        print(f"MQTT Broker: {MQTT_BROKER}")
        print(f"MQTT Topic: {MQTT_TOPIC}")
        print(f"Client Name: {CLIENT_NAME}")
        print("Aplankykite http://localhost:5000 naršyklėje")
        print("Pavyzdžiui, ieškokite žodžio: http://localhost:5000/lookup/hello")
        print("=" * 50)
        
        # Paleidžiame Flask aplikaciją
        app.run(debug=True, host='0.0.0.0', port=5000)
        
    except KeyboardInterrupt:
        print("\nPrograma sustabdyta")
    finally:
        cleanup()