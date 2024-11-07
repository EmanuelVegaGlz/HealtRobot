import pandas as pd
import paho.mqtt.client as mqtt
from queue import Queue
import time
import qrcode


class IOTSystem:
    def __init__(self, csv_file):
        self.csv_file = csv_file
        self.data = pd.read_csv(csv_file)
        self.queue = Queue()
        self.client = mqtt.Client()
        
        # Conectarse al broker MQTT
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect("localhost", 1883, 60)

        # Suscribirse a los tópicos
        self.client.subscribe("Node/routine")
        self.client.subscribe("Node/confirm")
        self.client.subscribe("ESP/routine")
        self.client.subscribe("ESP/confirm")

    def on_connect(self, client, userdata, flags, rc):
        print("Conectado con código de resultado " + str(rc))

    def on_message(self, client, userdata, msg):
        self.queue.put(msg.payload.decode())
    
    def load_data(self):
        self.data = pd.read_csv(self.csv_file)

    def save_data(self):
        self.data.to_csv(self.csv_file, index=False)

    def process_instructions(self):
        while not self.queue.empty():
            instruction = self.queue.get()
            command = instruction[:2]
            params = instruction[2:].split(',')

            if command == "NP":  # Nuevo perfil
                self.add_patient_profile(params)
            elif command == "CP":  # Configuración de pastillas
                self.configure_dispensing(params)
            elif command == "QR":  # Generar QR
                self.generate_qr(params)
            elif command == "HD":  # Historial de dosis
                self.send_dosage_history()

    def add_patient_profile(self, params):
        nombre, telefono, edad, sexo, historial_medico, contactos = params
        new_data = {
            "id": len(self.data) + 1,
            "nombre": nombre,
            "edad": int(edad),
            "sexo": sexo,
            "historial_medico": historial_medico,
            "numero_telefono": telefono,
            "contactos": contactos,
            "configuracion_pastillas": "",
            "Historial de Dosis": ""
        }
        self.data = self.data.append(new_data, ignore_index=True)
        self.client.publish("Py/routine", "NPOK")

    # Configurar dispensado de pastillas
    def configure_dispensing(self, params):
        nombre, freq, hora_inicial, dias, notas = params
        idx = self.data[self.data["nombre"] == nombre].index
        if not idx.empty:
            self.data.at[idx[0], "configuracion_pastillas"] = f"{freq},{hora_inicial},{dias},{notas}"
            self.client.publish("Py/routine", "CPOK")
        
    # Genera QR (falta mandarlo por whats)
    def generate_qr(self, params):
        nombre = params[0]
        # Buscar el registro en el DataFrame basado en el nombre
        record = self.data[self.data["nombre"] == nombre]

        if not record.empty:
            # Extraer nombre, id y número de teléfono
            nombre = record.iloc[0]["nombre"]
            id_paciente = record.iloc[0]["id"]
            numero_telefono = record.iloc[0]["numero_telefono"]
            
            # Crear la cadena con la información necesaria para el QR
            qr_data = f"Nombre: {nombre}, ID: {id_paciente}, Teléfono: {numero_telefono}"
            
            # Configuración del QR con los parámetros deseados
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            
            # Añadir datos y generar el QR
            qr.add_data(qr_data)
            qr.make(fit=True)
            img = qr.make_image(fill='black', back_color='white')
            
            # Guardar la imagen en un archivo
            filename = f"{nombre}_QR.png"
            img.save(filename)
            
            # Publicar mensaje de confirmación
            self.client.publish("Py/routine", "QROK")
            print(f"Código QR generado y guardado como '{filename}'.")
        else:
            # En caso de no encontrar el nombre en el DataFrame
            self.client.publish("Py/routine", "QRERROR")
            print("Error: Paciente no encontrado.")

    def send_dosage_history(self):
        ''' 
        Aqui Envia el historial de dosis
        
        '''
        self.client.publish("Py/routine", "HDOK")

    def start(self):
        self.client.loop_start()
        try:
            while True:
                self.process_instructions()
                time.sleep(1)  # Tiempo de espera entre ejecuciones
        except KeyboardInterrupt:
            pass
        finally:
            self.save_data()
            self.client.loop_stop()

if __name__ == "__main__":
    system = IOTSystem("pacientes.csv")
    system.start()
