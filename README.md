# PEVICO: Sistema Híbrido de Detección de Somnolencia y Distracción para Conductores

PEVICO (Prevención de Víctimas por Colisiones) es un sistema avanzado de asistencia a la conducción (ADAS) diseñado para monitorear el estado de alerta del conductor en tiempo real. La arquitectura del sistema es de carácter híbrido: combina la extracción de características geométricas faciales en 3D y clasificación por Inteligencia Artificial (Random Forest) con un supervisor determinista de reglas físicas de seguridad y actuadores electromecánicos controlados por hardware (Arduino).

---

## Características Principales

* **Monitoreo Facial Tridimensional:** Extracción de 468 puntos de referencia faciales (landmarks) mediante MediaPipe Face Mesh, inmune a ligeras rotaciones del rostro y variaciones de escala.
* **Métricas Geométricas Proporcionales:** 
  * Cálculo de la Relación de Aspecto del Ojo (EAR) para detección de parpadeos y microsueños.
  * Cálculo de la Relación de Aspecto de la Boca (MAR) para la detección de fatiga y bostezos continuos.
* **Estimación de la Pose de la Cabeza:** Cálculo de los ángulos de inclinación (Pitch) y rotación (Yaw) mediante la resolución del problema Perspective-n-Point (SolvePnP) para detectar cabeceo por sueño o distracción por desvío de la mirada.
* **Clasificación Predictiva por IA:** Inferencia en microsegundos de un modelo Random Forest (Bosque Aleatorio) entrenado sobre un dataset real de 30,626 fotogramas para clasificar estados de fatiga.
* **Arquitectura de Control Híbrido:** Una máquina de estados en tres niveles (SAFE, WARNING, EMERGENCY) fusiona la clasificación probabilística del modelo de IA con reglas físicas deterministas para evitar falsos positivos críticos en carretera.
* **Actuación Física por Hardware:** Integración serial UART (9600 baudios) con Arduino Uno para accionar LEDs indicadores, zumbador de alerta y relés de potencia de lógica mixta (freno de emergencia en Active-Low y luces en Active-High).

---

## Requisitos del Sistema

* **Sistema Operativo:** Windows 10/11, Linux o macOS.
* **Python:** Versión 3.8 o superior.
* **Hardware:** Cámara web USB convencional y placa Arduino Uno con circuito de relés y zumbador.

---

## Instalación y Configuración

1. **Clonar o descargar el repositorio:**
   Extraer los archivos en la carpeta de trabajo local.

2. **Crear e inicializar un entorno virtual (Recomendado):**
   ```bash
   python -m venv .venv
   ```

3. **Activar el entorno virtual:**
   * En Windows (PowerShell):
     ```powershell
     .venv\Scripts\Activate.ps1
     ```
   * En Linux/macOS o CMD:
     ```bash
     source .venv/bin/activate
     ```

4. **Instalar las dependencias de Python:**
   ```bash
   pip install -r requirements.txt
   ```

5. **Firmware del Arduino:**
   * Abrir el archivo `arduino/arduino_buzzer_leds/arduino_buzzer_leds.ino` en el Arduino IDE.
   * Compilar y cargar el programa en la placa Arduino Uno conectada al puerto correspondiente.
   * Verificar en el Administrador de Dispositivos el puerto COM asignado (por ejemplo, `COM12`) y configurarlo en el archivo `config.py` si es diferente.

---

## Instrucciones de Ejecución

### Ejecutar la Aplicación Principal:
Asegúrate de que la cámara web y el Arduino estén conectados, y el entorno virtual esté activo. Corre el siguiente comando:
```bash
python main.py
```

### Ejecutar Scripts Secundarios (Opcional):
* **Prueba de captura de cámara básica:**
  ```bash
  python test_camara.py
  ```
* **Entrenamiento y optimización del modelo Random Forest:**
  ```bash
  python scripts/2_entrenar_modelo.py
  ```
* **Visualización y graficado del rendimiento del entrenamiento:**
  ```bash
  python scripts/visualizar_entrenamiento.py
  ```

---

## Configuración y Calibración
Los umbrales físicos del sistema, tiempos de persistencia de seguridad y la configuración del puerto de comunicación serial están centralizados en el archivo `config.py`. Los parámetros principales incluyen:
* `EAR_THRESHOLD = 0.22` (Umbral de ojos cerrados)
* `MAR_THRESHOLD = 0.50` (Umbral de apertura de boca)
* `PITCH_DOWN_THRESHOLD = 18.0` (Ángulo límite de cabeceo hacia abajo)
* `SERIAL_PORT = "COM12"` (Puerto de comunicación física con Arduino)
