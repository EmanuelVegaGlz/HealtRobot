#include <WiFi.h>
#include <PubSubClient.h>
#include <DHT.h>
#include <string.h>

// Configuración de la red Wi-Fi
const char* ssid = "INFINITUM3434_2.4";
const char* password = "Z1bat42019";

// Configuración del broker MQTT
const char* mqttServer = "192.168.1.142";
const int mqttPort = 1883;

// Pines del LED
const int ledPin = 2; // Cambia este valor si usas otro pin

// Definimos el pin digital donde se conecta el sensor
#define DHTPIN 16
// Dependiendo del tipo de sensor
#define DHTTYPE DHT11
// Inicializamos el sensor DHT11
DHT dht(DHTPIN, DHTTYPE);

// Instancias de cliente Wi-Fi y MQTT
WiFiClient wifiClient;
PubSubClient mqttClient(wifiClient);

// Estado del LED
bool ledState = LOW;

// Función de callback para mensajes MQTT
void callback(char* topic, byte* payload, unsigned int length) {
    Serial.print("Mensaje recibido en el tópico: ");
    Serial.println(topic);

    String message;
    for (int i = 0; i < length; i++) {
        message += (char)payload[i];
    }

    Serial.print("Mensaje: ");
    Serial.println(message);

    // Control del LED basado en el mensaje
    if (message == "ON" && ledState == LOW) {
        digitalWrite(ledPin, HIGH);
        ledState = HIGH;
        mqttClient.publish("laptop/emanuel", "LED is ON");
    } else if (message == "OFF" && ledState == HIGH) {
        digitalWrite(ledPin, LOW);
        ledState = LOW;
        mqttClient.publish("laptop/emanuel", "LED is OFF");
    }
}

// Conectar al broker MQTT
void reconnect() {
    while (!mqttClient.connected()) {
        Serial.print("Intentando conectar al broker MQTT...");
        if (mqttClient.connect("ESP32Client")) {
            Serial.println("Conectado");
            mqttClient.subscribe("esp32/LED");
        } else {
            Serial.print("Fallido, rc=");
            Serial.print(mqttClient.state());
            Serial.println(" Intentando de nuevo en 5 segundos");
            delay(5000);
        }
    }
}

void setup() {
    // Inicializar el puerto serie
    Serial.begin(115200);

    // Inicializar el sensor DHT11
    dht.begin();

    // Configurar el pin del LED
    pinMode(ledPin, OUTPUT);
    digitalWrite(ledPin, LOW);

    // Conectar a la red Wi-Fi
    WiFi.begin(ssid, password);
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }
    Serial.println("Conectado a Wi-Fi");

    // Configurar el servidor MQTT
    mqttClient.setServer(mqttServer, mqttPort);
    mqttClient.setCallback(callback);
}

void loop() {
    if (!mqttClient.connected()) {
        reconnect();
    }
    mqttClient.loop();

    // Leer los valores de temperatura y humedad
    float humedad = dht.readHumidity();
    float temperatura = dht.readTemperature();

    // Verificar si la lectura es válida
    if (isnan(humedad) || isnan(temperatura)) {
        Serial.println("Error al leer del sensor DHT11");
    } else {
        // Convertir los valores a cadenas (sin texto adicional)
        char humedadStr[8];
        dtostrf(humedad, 6, 2, humedadStr);  // Valor numérico con 2 decimales
        
        char temperaturaStr[8];
        dtostrf(temperatura, 6, 2, temperaturaStr);  // Valor numérico con 2 decimales

        // Publicar solo los valores numéricos en los tópicos MQTT
        mqttClient.publish("esp32/Humedad", humedadStr);
        mqttClient.publish("esp32/Temperatura", temperaturaStr);

        // Imprimir los valores en el monitor serie
        Serial.print("Humedad: ");
        Serial.println(humedadStr);
        Serial.print("Temperatura: ");
        Serial.println(temperaturaStr);
    }

    // Publicar los datos cada segundo
    delay(1000);
}
