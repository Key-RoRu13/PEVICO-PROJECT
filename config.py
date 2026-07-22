# config.py
"""
Configuraciones globales del sistema de detección de fatiga y distracción.
Define los umbrales físicos, tiempos de disparo y parámetros de alertas.
"""

# --- CONFIGURACIÓN DE CÁMARA ---

#CAMERA_INDEX = 0         # Índice de la cámara por defecto
CAMERA_INDEX = 0 
FRAME_WIDTH = 640         # Ancho de fotograma para procesamiento
FRAME_HEIGHT = 480        # Alto de fotograma para procesamiento

# --- UMBRALES DE FATIGA (Rostro y Ojos) ---
# EAR (Eye Aspect Ratio): Ojos cerrados < UMBRAL
EAR_THRESHOLD = 0.22      # Umbral por debajo del cual se considera que el ojo está cerrado
EAR_CONSEC_SEC = 1.5      # Tiempo en segundos con ojos cerrados para disparar EMERGENCIA
EAR_WARN_SEC = 0.5        # Tiempo en segundos para disparar una PRECAUCIÓN leve

# MAR (Mouth Aspect Ratio): Bostezar > UMBRAL
MAR_THRESHOLD = 0.50      # Umbral por encima del cual se detecta boca abierta (bostezo)
YAWN_CONSEC_SEC = 1.5     # Tiempo consecutivo bostezando para registrar un bostezo y advertir
YAWN_COOLDOWN_SEC = 6.0   # Tiempo de espera entre conteo de bostezos

# --- CABECEOS E INCLINACIONES DE CABEZA (Pose Estimation en grados) ---
# Ángulos de rotación de cabeza:
# Pitch (Cabeceo arriba/abajo): Positivo es cabeza hacia abajo, negativo hacia arriba.
PITCH_DOWN_THRESHOLD = 18.0   # Cabeza muy inclinada hacia adelante (grados)
PITCH_UP_THRESHOLD = -20.0    # Cabeza muy inclinada hacia atrás (grados)
HEAD_DROOP_CONSEC_SEC = 1.5   # Tiempo en segundos con la cabeza caída para disparar EMERGENCIA

# Yaw (Mirada izquierda/derecha / Rotación de cabeza):
YAW_LOOK_AWAY_THRESHOLD = 25.0  # Ángulo de mirada desviada a los lados (grados)
LOOK_AWAY_CONSEC_SEC = 1.0      # Tiempo mirando a los lados para disparar PRECAUCIÓN

# --- CLASIFICADOR ENTRENADO DE INTELIGENCIA ARTIFICIAL (.PKL) ---
MODEL_PATH = "assets/models/clasificador_fatiga.pkl"

# --- CONFIGURACIÓN DE ALERTAS DE AUDIO ---
TTS_SPEECH_RATE = 160           # Velocidad de voz del sintetizador (palabras por minuto)
TTS_VOLUME = 1.0                # Volumen del sintetizador (0.0 a 1.0)

# Mensajes de alerta por voz en español:
MSG_WARN_DISTRACTED = "¡Atención! Mantenga la vista en el camino."
MSG_WARN_YAWNING = "Se detectan signos de cansancio. Por favor manténgase alerta."
MSG_CRITICAL_SLEEP = "¡PELIGRO! ¡DESPIERTE! ¡SISTEMA DE FRENADO DE EMERGENCIA ACTIVADO!"

# --- CONFIGURACIÓN DE ACTUADORES (SERIAL / ARDUINO) ---
# SERIAL_ENABLED = True          # Cambiar a True si se conecta un Arduino real
# SERIAL_PORT = "COM11"


SERIAL_ENABLED = True          # Cambiar a True si se conecta un Arduino real
SERIAL_PORT = "COM12"            # Puerto COM por defecto en Windows
SERIAL_BAUDRATE = 9600          # Velocidad estándar de transmisión UART
