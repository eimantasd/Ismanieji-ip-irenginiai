import sqlite3
import paho.mqtt.client as mqtt
import json

MQTT_Topic = "Home/BedRoom/18/#"
mqttBroker ="broker.hivemq.com"

# SQLite DB Name
DB_Name =  "IoT.db"

# SQLite DB Table Schema
TableSchema="""
drop table if exists Temperature_Data ;
create table Temperature_Data (
  id integer primary key autoincrement,
  SensorID text,
  Date_n_Time text,
  Temperature text
);


drop table if exists Humidity_Data ;
create table Humidity_Data (
  id integer primary key autoincrement,
  SensorID text,
  Date_n_Time text,
  Humidity text
);

drop table if exists Pressure_Data ;
create table Pressure_Data (
  id integer primary key autoincrement,
  SensorID text,
  Date_n_Time text,
  Pressure text
);
"""

class DatabaseManager():
	def __init__(self):
		self.conn = sqlite3.connect(DB_Name)
		self.conn.execute('pragma foreign_keys = on')
		self.conn.commit()
		self.cur = self.conn.cursor()
		
	def add_del_update_db_record(self, sql_query, args=()):
		self.cur.execute(sql_query, args)
		self.conn.commit()
		return

	def __del__(self):
		self.cur.close()
		self.conn.close()

def build_db(TableSchema):
	#Connect or Create DB File
	conn = sqlite3.connect(DB_Name)
	curs = conn.cursor()

	#Create Tables
	sqlite3.complete_statement(TableSchema)
	curs.executescript(TableSchema)

	#Close DB
	curs.close()
	conn.close()

# Function to save Temperature to DB Table
def Temp_Data_Handler(jsonData):
	#Parse Data 
	json_Dict = json.loads(jsonData)
	SensorID = json_Dict['Sensor_ID']
	Data_and_Time = json_Dict['Date']
	try:
		Temperature = json_Dict['Temperature']
		dbObj = DatabaseManager()
		dbObj.add_del_update_db_record("insert into Temperature_Data (SensorID, Date_n_Time, Temperature) values (?,?,?)",[SensorID, Data_and_Time, Temperature])
		del dbObj
		print("Inserted Temperature Data into Database.")
	except:
		print("wrong payload, skipped inserting to DB")
	

# Function to save Humidity to DB Table
def Humidity_Data_Handler(jsonData):
	#Parse Data 
	json_Dict = json.loads(jsonData)
	SensorID = json_Dict['Sensor_ID']
	Data_and_Time = json_Dict['Date']
	try:
		Humidity = json_Dict['Humidity']
		dbObj = DatabaseManager()
		dbObj.add_del_update_db_record("insert into Humidity_Data (SensorID, Date_n_Time, Humidity) values (?,?,?)",[SensorID, Data_and_Time, Humidity])
		del dbObj
		print("Inserted Humidity Data into Database.")
	except:
		print("wrong payload, skipped inserting to DB")

# Function to save Pressure to DB Table
def Pressure_Data_Handler(jsonData):
	#Parse Data 
	json_Dict = json.loads(jsonData)
	SensorID = json_Dict['Sensor_ID']
	Data_and_Time = json_Dict['Date']
	try:
		Pressure = json_Dict['Pressure']
		dbObj = DatabaseManager()
		dbObj.add_del_update_db_record("insert into Pressure_Data (SensorID, Date_n_Time, Pressure) values (?,?,?)",[SensorID, Data_and_Time, Pressure])
		del dbObj
		print("Inserted Pressure Data into Database.")
	except:
		print("wrong payload, skipped inserting to DB")
	

def sensor_Data_Handler(Topic, jsonData):
	if Topic == "Home/BedRoom/18/Temperature":
		Temp_Data_Handler(jsonData)
	elif Topic == "Home/BedRoom/18/Humidity":
		Humidity_Data_Handler(jsonData)	
	elif Topic == "Home/BedRoom/18/Pressure":
		Pressure_Data_Handler(jsonData)	

def on_message(client, userdata, message):
    print("received message: " ,str(message.payload.decode("utf-8")))
    sensor_Data_Handler(message.topic, message.payload)

if __name__ == "__main__":
	build_db(TableSchema)
	client = mqtt.Client(client_id="Sniffergfffggff", callback_api_version=2, transport="websockets", protocol=mqtt.MQTTv311, clean_session=True)
	client.connect(mqttBroker, 8000) 
	print("Connecting")

	client.subscribe(MQTT_Topic)
	print("Subscribed")
	client.on_message=on_message
	client.loop_forever() 