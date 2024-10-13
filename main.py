import bme280 as bme280
#from umqtt.simple import MQTTClient
from simple import MQTTClient
import time
import network
import ujson as json  # Für die Konfigurationsdatei
from machine import SoftI2C
from machine import I2C


# Konfiguration aus Datei laden
with open('config.json') as f:
    config = json.load(f)

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(config["wlan"]["ssid"], config["wlan"]["passwort"])

# Warten, bis die WLAN-Verbindung hergestellt ist
print("Verbinde mit WLAN...", end="")
while not wlan.isconnected():
    print(".", end="")
    time.sleep(1)
print("verbunden!")

# MQTT-Client initialisieren
client = MQTTClient(config["mqtt"]["client_id"], config["mqtt"]["broker"], 
                  config["mqtt"]["port"], config["mqtt"]["user"], 
                  config["mqtt"]["passwort"])

# Versuche, eine Verbindung zum MQTT-Broker herzustellen
print("Verbinde mit MQTT-Broker...", end="")
while True:
    try:
        client.connect()
        print("verbunden!")
        break  # Verbindung erfolgreich, Schleife verlassen
    except OSError as e:
        print(".", end="")
        time.sleep(1)

# Initialisieren des BME280
i2c = I2C(scl=config["sensor"]["i2c_scl_pin"], sda=config["sensor"]["i2c_sda_pin"])
bme1 = bme280.BME280(i2c=i2c, address=0x76) 
i2c = SoftI2C(scl=config["sensor"]["i2c_scl_pin"], sda=config["sensor"]["i2c_sda_pin"], freq=500000)
bme2 = bme280.BME280(i2c=i2c, address=0x77) 

# Definiere eine Funktion zur Berechnung des Taupunkts
def calculate_dew_point(temperature, humidity):
  """Berechnet den Taupunkt anhand von Temperatur und Luftfeuchtigkeit.

  Args:
    temperature: Die Temperatur in Grad Celsius.
    humidity: Die relative Luftfeuchtigkeit in Prozent.

  Returns:
    Der Taupunkt in Grad Celsius.
  """
  return (humidity/100)**(1/8)*(112+0.9*temperature)+0.1*temperature-112

# Definiere eine Funktion zum Veröffentlichen aller Werte über MQTT
def publish_all_values(client, temp1, pressure1, humidity1, temp2, pressure2, humidity2, tau_punkt_innen, tau_punkt_aussen):
  """Veröffentlicht alle Sensorwerte und den Taupunkt über MQTT.

  Args:
    client: Das MQTT-Client-Objekt.
    temp1: Innentemperatur.
    pressure1: Innendruck.
    humidity1: Innenluftfeuchtigkeit.
    temp2: Außentemperatur.
    pressure2: Außendruck.
    humidity2: Außenluftfeuchtigkeit.
    tau_punkt_innen: Taupunkt innen.
    tau_punkt_aussen: Taupunkt außen.
  """
  try:
    # Versuche, eine Verbindung zum MQTT-Broker herzustellen
    #if not client.is_connected():
    if client.sock is None:
      print("Verbinde mit MQTT-Broker verloren...", end="")
      client.connect()
    # Veröffentliche die einzelnen Werte unter den angegebenen Topics
    client.publish(config["mqtt"]["topic"] + "temperature_in", str(temp1))
    client.publish(config["mqtt"]["topic"] + "humidity_in", str(humidity1))
    client.publish(config["mqtt"]["topic"] + "pressure_in", str(pressure1))
    client.publish(config["mqtt"]["topic"] + "temperature_out", str(temp2))
    client.publish(config["mqtt"]["topic"] + "humidity_out", str(humidity2))
    client.publish(config["mqtt"]["topic"] + "pressure_out", str(pressure2))
    client.publish(config["mqtt"]["topic"] + "taupunkt_innen", str(tau_punkt_innen))
    client.publish(config["mqtt"]["topic"] + "taupunkt_aussen", str(tau_punkt_aussen))
  except OSError as e:
    # Gib eine Fehlermeldung aus, falls die Veröffentlichung fehlschlägt
    print("Fehler beim Veröffentlichen der Daten: {}".format(e))
  #finally:
    #client.disconnect()

# Definiere eine Funktion zur Steuerung des Lüfters
def control_fan(client, tau_punkt_innen, tau_punkt_aussen):
  """Steuert den Lüfter basierend auf dem Unterschied der Taupunkte.

  Args:
    client: Das MQTT-Client-Objekt.
    tau_punkt_innen: Taupunkt innen.
    tau_punkt_aussen: Taupunkt außen.
  """
  # Wenn der Unterschied zwischen dem Taupunkt innen und außen größer als 1 Grad Celsius ist...
  if tau_punkt_innen - tau_punkt_aussen > 1:
    try:
        # ...versuche, den Lüfter einzuschalten
        if not client.sock is None:
            print("Verbinde mit MQTT-Broker verloren...", end="")
            client.connect()
            time.sleep(0.1)
        client.publish("cmnd/luefter/POWER", "ON")
        print("Lüfter eingeschaltet")
    except OSError as e:
      # Gib eine Fehlermeldung aus, falls das Einschalten des Lüfters fehlschlägt
      print("Fehler beim Schalten des Lüfters: {}".format(e))
  else:
    # ...ansonsten versuche, den Lüfter auszuschalten
    try:
      client.publish("cmnd/luefter/POWER", "OFF")
      print("Lüfter ausgeschaltet")
    except OSError as e:
      # Gib eine Fehlermeldung aus, falls das Ausschalten des Lüfters fehlschlägt
      print("Fehler beim Schalten des Lüfters: {}".format(e))

# Lade die Konfiguration aus der config.json Datei
with open("config.json", "r") as config_file:
    config = json.load(config_file)

# Endlosschleife
while True:
  # Messung der Werte von beiden Sensoren
  try:
    temp1, pressure1, humidity1 = map(float, (val.replace('C', '').replace('hPa', '').replace('%', '') for val in bme1.values))
    temp2, pressure2, humidity2 = map(float, (val.replace('C', '').replace('hPa', '').replace('%', '') for val in bme2.values))
  except OSError as e:
    # Gib eine Fehlermeldung aus, falls die Messung fehlschlägt
    print("Fehler beim Messen: {}".format(e))
    time.sleep(5)
    continue

  # Berechnung des Taupunkts für innen und außen
  tau_punkt_innen = calculate_dew_point(temp1, humidity1)
  tau_punkt_aussen = calculate_dew_point(temp2, humidity2)

  # Steuerung des Lüfters basierend auf den Taupunkten
  control_fan(client, tau_punkt_innen, tau_punkt_aussen)

  # Veröffentlichen aller Werte über MQTT
  publish_all_values(client, temp1, pressure1, humidity1, temp2, pressure2, humidity2, tau_punkt_innen, tau_punkt_aussen)

  # Wartezeit
  time.sleep(10)