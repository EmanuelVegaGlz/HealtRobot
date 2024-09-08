import paho.mqtt.client as mqtt


# Función que se ejecuta cuando te conectas al broker MQTT
def on_connect(client, userdata, flags, reasonCode, properties=None):
    print(f"Conectado con código de resultado {reasonCode}")
    client.subscribe("esp32/LED")


# Función que se ejecuta cuando se recibe un mensaje en un tópico suscrito
def on_message(client, userdata, msg):
    print(f"Mensaje recibido en {msg.topic}: {msg.payload.decode()}")


# Configuración del cliente MQTT
client = mqtt.Client()

# Asignación de funciones de callback
client.on_connect = on_connect
client.on_message = on_message

# Conexión al broker MQTT
client.connect("192.168.1.142", 1883, 60)

# Inicio de un hilo para manejar la red y las callbacks
client.loop_start()

# Bucle principal para enviar mensajes desde la consola
try:
    while True:
        # Leer texto desde la consola
        mensaje = input("Ingresa un mensaje para publicar en 'laptop/emanuel': ")

        # Publicar el mensaje en el tópico 'laptop/emanuel'
        client.publish("laptop/emanuel", mensaje)

except KeyboardInterrupt:
    print("Desconectando...")

# Finaliza el hilo loop
client.loop_stop()
client.disconnect()
