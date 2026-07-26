# PEVICO: Sistema Híbrido de Detección de Somnolencia y Distracción para Conductores

PEVICO (Prevención de Víctimas por Colisiones) es un sistema avanzado de asistencia a la conducción (ADAS) diseñado para monitorear, detectar y mitigar el estado de fatiga, microsueño y distracción del conductor en tiempo real. 

El sistema implementa una **arquitectura híbrida** de seguridad crítica: utiliza algoritmos de visión artificial y aprendizaje automático probabilístico en tiempo real para predecir el cansancio del conductor, respaldado por un supervisor determinista de reglas físicas y una etapa de actuación por hardware (Arduino) con relés de potencia de lógica mixta para intervenir físicamente sobre los sistemas del vehículo (frenos e intermitentes).

---

## Arquitectura Lógica del Sistema

El procesamiento del sistema se divide en cuatro capas secuenciales ejecutadas a una tasa de refresco promedio de **27 FPS**:

1. **Capa de Captura y Preprocesamiento:** Captura de video a resolución optimizada (640x480) y conversión del espacio de color de BGR a RGB para adecuarse al motor de inferencia facial.
2. **Capa de Extracción Geométrica (MediaPipe Face Mesh):** Extracción de una malla de 468 landmarks faciales 3D para calcular de forma matemática la apertura de los párpados ($EAR$) y de la boca ($MAR$). Además, se estima la pose de la cabeza en grados de libertad (Pitch y Yaw) mediante la resolución del problema de perspectiva *SolvePnP*.
3. **Capa de Clasificación Predictiva (IA):** Inferencia en microsegundos utilizando un modelo **Random Forest** (Bosque Aleatorio) entrenado sobre un dataset real de **30,626 fotogramas**.
4. **Capa de Fusión y Control Híbrido:** Una máquina de estados lógica clasifica el riesgo en tres niveles (`SAFE`, `WARNING`, `EMERGENCY`). La IA activa pre-alertas de advertencia en caso de fatiga moderada, mientras que las reglas físicas deterministas (ojos cerrados o cabeza caída por más de 1.5 segundos de persistencia temporal) gobiernan el disparo de la alarma crítica y la frenada de emergencia, protegiendo al vehículo contra falsos positivos de la IA.

---

## Diagrama de Conexión de Hardware (Arduino Uno)

El sistema de Python se comunica vía protocolo serial UART (9600 baudios) con una placa Arduino Uno encargada de comandar la retroalimentación en la cabina y la potencia del vehículo. Los pines se configuran de la siguiente manera:

| Componente | Pin Digital Arduino | Tipo de Entrada/Salida | Descripción / Comportamiento |
| :--- | :---: | :---: | :--- |
| **LED Verde** | `D2` | Salida (Active-High) | Indicador de Conducción Segura (`SAFE`). |
| **LED Amarillo** | `D3` | Salida (Active-High) | Indicador de Advertencia / Distracción (`WARNING`). |
| **LED Rojo** | `D4` | Salida (Active-High) | Indicador de Alerta Crítica / Emergencia (`EMERGENCY`). |
| **Buzzer / Bocina** | `D5` | Salida (PWM) | Tono intermitente (1000 Hz) en `WARNING` y tono continuo (2500 Hz) en `EMERGENCY`. |
| **Relé 1 (Freno)** | `D6` | Salida (Active-Low) | Activa el frenado físico. Lógica invertida: `LOW` activa el relé, `HIGH` lo mantiene desactivado. |
| **Relé 2 (Luces)** | `D7` | Salida (Active-High) | Activa las luces intermitentes físicas de peligro. Lógica estándar: `HIGH` activa el relé. |

---

## Resultados Experimentales y Rendimiento

El sistema ha sido evaluado y validado científicamente, arrojando las siguientes métricas de desempeño computacional y analítico:

* **Exactitud Global (Accuracy):** **$97.94\%$** en clasificación de estados en cabina.
* **Sensibilidad (Recall) ante Fatiga:** **$72.9\%$**, permitiendo la anticipación y detección de somnolencia antes del cierre total de ojos del conductor.
* **Latencia de Actuación de Hardware:** Menor a **$35\text{ ms}$** desde la detección de la cámara hasta la conmutación de los relés físicos en Arduino.
* **Rendimiento de FPS (Procesamiento Multihilo):** **$27.2\text{ FPS}$** estables gracias a la separación de la inferencia secundaria de YOLOv8 (detección de celular) en un hilo asíncrono secundario.

---

## Instalación y Configuración

1. **Inicializar y activar el entorno virtual:**
   ```bash
   python -m venv .venv
   # Activar en Windows:
   .venv\Scripts\activate
   ```

2. **Instalar dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Cargar firmware de Arduino:**
   Cargar el sketch `arduino/arduino_buzzer_leds/arduino_buzzer_leds.ino` a la placa mediante Arduino IDE.

4. **Ejecutar el sistema:**
   ```bash
   python main.py
   ```
