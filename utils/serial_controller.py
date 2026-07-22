# utils/serial_controller.py
"""
Controlador de Comunicación Serial para Actuadores Físicos (Arduino/ESP32).
Envía señales de frenado, luces intermitentes y niveles de alerta.
Si no hay hardware conectado, opera de forma simulada (dry-run).
"""

import serial
import time
import threading
import config

class VehicleActuatorController:
    def __init__(self):
        self.ser = None
        self.is_connected = False
        
        # Estados actuales del actuador
        self.emergency_brake_active = False
        self.hazard_lights_active = False
        self.alert_level = None # Se inicializa en None para forzar el envío del primer estado (ej. SAFE) a Arduino
        
        # Intentar conectar si está habilitado
        if config.SERIAL_ENABLED:
            threading.Thread(target=self._connect_serial, daemon=True).start()
        else:
            self.log("Sistema iniciado en Modo Simulación Virtual (Sin hardware).")

    def _connect_serial(self):
        """Intenta abrir la conexión con el puerto serial en segundo plano."""
        self.log(f"Intentando conectar al puerto {config.SERIAL_PORT}...")
        try:
            self.ser = serial.Serial(
                port=config.SERIAL_PORT,
                baudrate=config.SERIAL_BAUDRATE,
                timeout=1.0
            )
            time.sleep(2) # Esperar a que Arduino se reinicie al abrir conexión
            self.is_connected = True
            self.log(f"Conectado con éxito a Arduino en {config.SERIAL_PORT}.")
        except Exception as e:
            self.is_connected = False
            self.log(f"Error de conexión en {config.SERIAL_PORT}: {e}. Operando en Modo Simulación.")

    def log(self, message):
        """Registra un mensaje de evento en consola."""
        timestamp = time.strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        print(log_entry)

    def _send_data(self, char):
        """Envía un carácter único al puerto serial si está conectado."""
        if self.is_connected and self.ser is not None:
            try:
                self.ser.write(char.encode('utf-8'))
                # Enviar de forma inmediata
                self.ser.flush()
            except Exception as e:
                self.is_connected = False
                self.log(f"Conexión serial perdida durante transmisión: {e}")

    def set_emergency_brake(self, active):
        """Acciona o libera la palanca del freno de emergencia."""
        if self.emergency_brake_active == active:
            return # Sin cambios
            
        self.emergency_brake_active = active
        if active:
            self.log("¡ACCIÓN CRÍTICA! Frenado de Emergencia ACTIVADO.")
            self._send_data('F') # 'F' = Frenar (Freno On)
        else:
            self.log("Freno de Emergencia liberado.")
            self._send_data('f') # 'f' = liberar freno (Freno Off)

    def set_hazard_lights(self, active):
        """Enciende o apaga las luces intermitentes de emergencia del vehículo."""
        if self.hazard_lights_active == active:
            return # Sin cambios
            
        self.hazard_lights_active = active
        if active:
            self.log("Luces intermitentes de emergencia encendidas.")
            self._send_data('I') # 'I' = Intermitentes On
        else:
            self.log("Luces intermitentes de emergencia apagadas.")
            self._send_data('i') # 'i' = Intermitentes Off

    def set_alert_level(self, level):
        """Actualiza el nivel de alerta general y lo envía a la placa."""
        if self.alert_level == level:
            return
            
        self.alert_level = level
        if level == "SAFE":
            self._send_data('S') # 'S' = Safe
        elif level == "WARNING":
            self.log("Alerta de conducción: Estado de Precaución.")
            self._send_data('W') # 'W' = Warning
        elif level == "EMERGENCY":
            self._send_data('E') # 'E' = Emergency

    def close(self):
        """Cierra la conexión serial de forma segura."""
        if self.is_connected and self.ser is not None:
            try:
                self.ser.close()
                self.log("Conexión serial cerrada.")
            except Exception:
                pass
            self.is_connected = False
