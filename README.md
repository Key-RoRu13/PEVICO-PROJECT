# PEVICO: Detección de Somnolencia y Distracción

PEVICO es un sistema avanzado de asistencia a la conducción diseñado para monitorear el estado de alerta del conductor en tiempo real. Combina algoritmos de visión artificial (MediaPipe Face Mesh) con clasificación por Inteligencia Artificial (Random Forest) y actuación física (Arduino) para evitar accidentes de tránsito.

---

## Características Principales
* **MediaPipe Face Mesh:** Extracción de puntos de referencia 3D para calcular el nivel de apertura de ojos (EAR) y boca (MAR).
* **Estimación de Pose de la Cabeza:** Cálculo de los ángulos de cabeceo (Pitch) y desviación de la mirada (Yaw).
* **Entrenamiento de IA Ligero:** Modelo Random Forest que clasifica la somnolencia en microsegundos basándose en vectores geométricos simples.
* **Controlador Físico Arduino Uno:** Acciona bocina, LEDs y relés de potencia de lógica mixta (freno de emergencia en Active-Low y luces en Active-High).

---

## Instalación y Configuración
1. **Crear e iniciar el entorno virtual:**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```
2. **Instalar dependencias:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Cargar firmware de Arduino:**
   Abrir y subir el sketch `arduino/arduino_buzzer_leds/arduino_buzzer_leds.ino` a la placa.

4. **Ejecutar el sistema:**
   ```bash
   python main.py
   ```
