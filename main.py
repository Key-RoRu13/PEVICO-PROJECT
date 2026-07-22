# main.py
"""
Punto de entrada principal del Sistema de Detección de Fatiga y Distracción PEVICO.
Orquesta los hilos de captura, procesamiento de visión artificial, interfaz gráfica y actuadores.
"""

import cv2
import numpy as np
import threading
import time

import config
from core.face_mesh import FaceMeshDetector
from utils.audio_player import AudioAlertSystem
from utils.serial_controller import VehicleActuatorController
from ui.dashboard import DriverSafetyDashboard
import pickle

class DriverSafetyApp:
    def __init__(self):
        # 1. Inicializar Actuadores y Alertas (Audio y Serial)
        self.actuators = VehicleActuatorController()
        self.audio = AudioAlertSystem()
        
        # 2. Inicializar Detectores de Visión Inteligente
        self.face_detector = FaceMeshDetector()
        
        # Cargar el cerebro clasificador de IA
        self.classifier = None
        try:
            with open(config.MODEL_PATH, "rb") as f:
                self.classifier = pickle.load(f)
            print("[IA] Clasificador de fatiga Random Forest cargado correctamente.")
        except Exception as e:
            print(f"[IA] Error crítico al cargar el clasificador de fatiga: {e}")
        
        # 3. Inicializar la Interfaz Gráfica (Dashboard)
        self.dashboard = DriverSafetyDashboard(on_close_callback=self.stop)
        
        # Estados internos de medición de tiempos y umbrales (para persistencia temporal de estados)
        self.eyes_closed_start_time = None
        self.yawning_start_time = None
        self.head_droop_start_time = None
        self.looking_away_start_time = None
        self.ia_fatigue_start_time = None # Tiempo sostenido de fatiga según IA
        
        # Banderas para registro de incidencias únicas en el terminal log de la UI
        self.sleep_logged = False
        self.yawn_logged = False
        self.droop_logged = False
        self.look_away_logged = False
        self.ia_fatigue_logged = False
        
        # Control del ciclo de video
        self.cap = None
        self.is_running = False
        self.video_thread = None
        
        # Cálculos de FPS
        self.prev_frame_time = 0
        self.fps = 0.0

    def start(self):
        """Inicia el hilo de video y arranca el loop de la interfaz gráfica."""
        self.is_running = True
        
        # Iniciar captura de cámara web (Quitamos CAP_DSHOW porque a veces congela cámaras virtuales o móviles)
        self.cap = cv2.VideoCapture(config.CAMERA_INDEX)
        
        # Si la cámara no abre, intentar con un índice diferente o simular
        if not self.cap.isOpened():
            self.dashboard.log_message("[CÁMARA] Error: No se pudo abrir la cámara web por defecto.")
            self.dashboard.log_message("[CÁMARA] Ejecutando en Modo Simulación de Imagen Estática/Color.")
            # No cerramos la aplicación, crearemos fotogramas sintéticos en el loop si es necesario
        else:
            # Solo cambiar propiedades de resolución si es una cámara física USB (número entero).
            # Si es un enlace HTTP de IP Webcam, intentar forzar la resolución corrompe el stream y da pantalla negra.
            if isinstance(config.CAMERA_INDEX, int):
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.FRAME_WIDTH)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.FRAME_HEIGHT)
            self.dashboard.log_message("[CÁMARA] Cámara web inicializada con éxito.")
            
        # Arrancar hilo de procesamiento de frames
        self.video_thread = threading.Thread(target=self._video_processing_loop, daemon=True)
        self.video_thread.start()
        
        # Arrancar loop principal de CustomTkinter (Bloqueante en el hilo principal de la UI)
        self.dashboard.mainloop()

    def _video_processing_loop(self):
        """Ciclo continuo de captura y procesamiento de fotogramas."""
        while self.is_running:
            frame = None
            
            # 1. Obtener frame
            if self.cap is not None and self.cap.isOpened():
                ret, frame = self.cap.read()
                if not ret:
                    frame = None
            
            # Si no hay cámara web física disponible, crear una señal de prueba animada (Modo Simulación)
            if frame is None:
                frame = self._create_simulated_frame()
                time.sleep(0.03) # Limitar FPS simulados a ~30
                
            # Espejar la imagen para que sea natural para el conductor (efecto espejo)
            frame = cv2.flip(frame, 1)
            
            # 2. Calcular FPS
            current_time = time.time()
            self.fps = 1.0 / (current_time - self.prev_frame_time) if self.prev_frame_time != 0 else 30.0
            self.prev_frame_time = current_time
            
            # 3. Procesar Landmarks Faciales y Pose (MediaPipe)
            metrics = self.face_detector.process(frame)
            
            # 4. Analizar Estado de Seguridad Híbrido (Reglas + IA)
            alert_level = self._evaluate_driver_state(metrics)
            
            # 5. Dibujar anotaciones estilizadas en el Frame
            annotated_frame = frame.copy()
            
            # Anotaciones de Rostro y Cabeza
            if metrics["detected"]:
                annotated_frame = self.face_detector.draw_annotations(annotated_frame, metrics, alert_level)
                
            # Leyenda de estado (Binario)
            legend_x, legend_y = 10, 20
            # Dibujar un fondo oscuro semitransparente para la leyenda (usando overlay)
            overlay = annotated_frame.copy()
            cv2.rectangle(overlay, (legend_x, legend_y - 15), (legend_x + 220, legend_y + 95), (0, 0, 0), -1)
            cv2.addWeighted(overlay, 0.6, annotated_frame, 0.4, 0, annotated_frame)
            
            # Textos a mostrar
            face_det = 1 if metrics["detected"] else 0
            
            if face_det:
                ear = metrics["ear"]
                eyes_open = 1 if ear >= config.EAR_THRESHOLD + 0.04 else 0
                eyes_semi = 1 if config.EAR_THRESHOLD <= ear < config.EAR_THRESHOLD + 0.04 else 0
                eyes_closed = 1 if ear < config.EAR_THRESHOLD else 0
            else:
                eyes_open, eyes_semi, eyes_closed = 0, 0, 0
                
            cv2.putText(annotated_frame, f"Rostro Detectado: {face_det}", (legend_x + 10, legend_y + 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            cv2.putText(annotated_frame, f"Ojos Abiertos: {eyes_open}", (legend_x + 10, legend_y + 35), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0) if eyes_open else (255, 255, 255), 1)
            cv2.putText(annotated_frame, f"Ojos Semi-abiertos: {eyes_semi}", (legend_x + 10, legend_y + 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255) if eyes_semi else (255, 255, 255), 1)
            cv2.putText(annotated_frame, f"Ojos Cerrados: {eyes_closed}", (legend_x + 10, legend_y + 85), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255) if eyes_closed else (255, 255, 255), 1)
                
            # 7. Actualizar la interfaz gráfica de forma segura
            # CustomTkinter permite llamar métodos desde hilos secundarios, pero lo ideal es pasar datos numéricos rápidamente
            try:
                # Pasar fotograma procesado a la UI
                self.dashboard.update_frame(annotated_frame)
                
                # Pasar EAR, MAR, Estado general y FPS reales
                ear = metrics["ear"] if metrics["detected"] else 0.30
                mar = metrics["mar"] if metrics["detected"] else 0.15
                self.dashboard.update_metrics(ear, mar, alert_level, self.fps)
            except Exception as e:
                print(f"[GUI Update Exception] {e}")
                
            # Pequeña pausa para no acaparar toda la CPU
            time.sleep(0.01)

    def _evaluate_driver_state(self, metrics):
        """
        Analiza las métricas en tiempo real y gestiona las transiciones de estado de alerta.
        Combina un interruptor rígido de seguridad (Ojos Cerrados) con inferencia de IA.
        Retorna: "SAFE", "WARNING" o "EMERGENCY".
        """
        now = time.time()
        
        # Banderas e interruptores de detección por reglas manuales
        is_sleeping = False
        is_drooping = False
        is_yawning = False
        is_looking_away = False
        
        # Bandera de la Inteligencia Artificial (Random Forest)
        is_ia_fatigued = False
        
        # 1. EVALUAR OJOS (EAR) - Capa Rígida de Microsueños (Siempre activa por seguridad)
        if metrics["detected"]:
            ear = metrics["ear"]
            if ear < config.EAR_THRESHOLD:
                if self.eyes_closed_start_time is None:
                    self.eyes_closed_start_time = now
                else:
                    duration = now - self.eyes_closed_start_time
                    if duration >= config.EAR_CONSEC_SEC:
                        is_sleeping = True
                        if not self.sleep_logged:
                            self.dashboard.log_message("¡ALERTA CRÍTICA! Ojos cerrados por prolongado tiempo.")
                            self.sleep_logged = True
            else:
                self.eyes_closed_start_time = None
                if self.sleep_logged and ear > 0.24: # Recuperación exitosa
                    self.dashboard.log_message("Conductor recuperó contacto visual. Alarma desactivada.")
                    self.sleep_logged = False
        else:
            self.eyes_closed_start_time = None

        # 2. EVALUACIÓN DE REGLAS FÍSICAS MANUALES (Siempre activas si hay rostro para mayor seguridad)
        if metrics["detected"]:
            # Cabeceo (Pitch)
            pitch = metrics["pitch"]
            if pitch > config.PITCH_DOWN_THRESHOLD or pitch < config.PITCH_UP_THRESHOLD:
                if self.head_droop_start_time is None:
                    self.head_droop_start_time = now
                else:
                    if now - self.head_droop_start_time >= config.HEAD_DROOP_CONSEC_SEC:
                        is_drooping = True
                        if not self.droop_logged:
                            self.dashboard.log_message("¡ALERTA CRÍTICA! Cabeceo o caída de cabeza detectada.")
                            self.droop_logged = True
            else:
                self.head_droop_start_time = None
                self.droop_logged = False
            
            # Bostezos (MAR)
            mar = metrics["mar"]
            if mar > config.MAR_THRESHOLD:
                if self.yawning_start_time is None:
                    self.yawning_start_time = now
                else:
                    if now - self.yawning_start_time >= config.YAWN_CONSEC_SEC:
                        is_yawning = True
                        if not self.yawn_logged:
                            self.dashboard.log_message("Advertencia: Conductor bostezando frecuentemente.")
                            self.audio.speak(config.MSG_WARN_YAWNING)
                            self.yawn_logged = True
            else:
                self.yawning_start_time = None
                self.yawn_logged = False
            
            # Distracción / Mirada desviada (Yaw)
            yaw = abs(metrics["yaw"])
            if yaw > config.YAW_LOOK_AWAY_THRESHOLD:
                if self.looking_away_start_time is None:
                    self.looking_away_start_time = now
                else:
                    if now - self.looking_away_start_time >= config.LOOK_AWAY_CONSEC_SEC:
                        is_looking_away = True
                        if not self.look_away_logged:
                            self.dashboard.log_message("Precaución: Distracción detectada (mirada fuera de ruta).")
                            self.audio.speak(config.MSG_WARN_DISTRACTED)
                            self.look_away_logged = True
            else:
                self.looking_away_start_time = None
                self.look_away_logged = False

        # 3. SELECCIÓN DE MÉTODO DE EVALUACIÓN DE SOMNOLENCIA (Inferencia de IA si está activado)
        prediction_mode = self.dashboard.prediction_mode.get() # "IA" o "Manual"
        
        if prediction_mode == "IA" and self.classifier is not None and metrics["detected"]:
            # --- EVALUACIÓN DE SUEÑO POR INTELIGENCIA ARTIFICIAL (Random Forest) ---
            # Crear vector de características: [EAR, MAR, Pitch, Yaw]
            features = np.array([[
                metrics["ear"],
                metrics["mar"],
                metrics["pitch"],
                metrics["yaw"]
            ]])
            
            try:
                # Realizar predicción: 0 = despierto, 1 = somnoliento
                prediction = int(self.classifier.predict(features)[0])
                
                if prediction == 1:
                    if self.ia_fatigue_start_time is None:
                        self.ia_fatigue_start_time = now
                    else:
                        duration = now - self.ia_fatigue_start_time
                        # Si la IA predice fatiga de manera consecutiva por más de 1.5s, disparamos alerta
                        if duration >= 1.5:
                            is_ia_fatigued = True
                            if not self.ia_fatigue_logged:
                                self.dashboard.log_message("[IA] Alerta: Se detectan patrones consolidados de somnolencia.")
                                self.ia_fatigue_logged = True
                else:
                    self.ia_fatigue_start_time = None
                    if self.ia_fatigue_logged:
                        self.dashboard.log_message("[IA] Conductor en estado seguro detectado.")
                        self.ia_fatigue_logged = False
            except Exception as e:
                print(f"[IA Inferencia Exception] {e}")

        # ==========================================
        # MAQUINA DE ESTADOS Y ACTUACIÓN CONJUNTA
        # ==========================================
        # Clasificar la fatiga detectada por la IA: si los ojos están abiertos o semi-abiertos, es advertencia.
        # Si están cerrados (por debajo del umbral), es una emergencia real.
        is_ia_emergency = prediction_mode == "IA" and is_ia_fatigued and (metrics["ear"] if metrics["detected"] else 1.0) < config.EAR_THRESHOLD
        is_ia_warning = prediction_mode == "IA" and is_ia_fatigued and (metrics["ear"] if metrics["detected"] else 1.0) >= config.EAR_THRESHOLD

        # Ojos cerrados por reglas (microsueño), cabeceo por reglas, o fatiga crítica de IA obligan a frenado inmediato
        if is_sleeping or is_drooping or is_ia_emergency:
            # ESTADO CRÍTICO DE EMERGENCIA (Microsueño, Cabeceo o Fatiga IA Crítica)
            self.actuators.set_alert_level("EMERGENCY")
            self.actuators.set_emergency_brake(True)
            self.actuators.set_hazard_lights(True)
            self.audio.set_emergency_siren(True)
            self.audio.speak(config.MSG_CRITICAL_SLEEP)
            
            # Sincronizar UI
            self.dashboard.set_brake_visual(True)
            self.dashboard.set_hazard_visual(True)
            return "EMERGENCY"
            
        elif is_yawning or is_looking_away or is_ia_warning:
            # ⚠️ ESTADO DE PRECAUCIÓN / ADVERTENCIA (Bostezo, distracción o cansancio moderado detectado por IA)
            self.actuators.set_alert_level("WARNING")
            self.audio.set_emergency_siren(False)
            self.actuators.set_emergency_brake(False)
            
            # Sincronizar UI
            self.dashboard.set_brake_visual(False)
            
            if not is_sleeping and not is_drooping:
                self.actuators.set_hazard_lights(False)
                self.dashboard.set_hazard_visual(False)
                
            return "WARNING"
            
        else:
            # ✅ ESTADO SEGURO
            self.actuators.set_alert_level("SAFE")
            self.audio.set_emergency_siren(False)
            self.actuators.set_emergency_brake(False)
            self.actuators.set_hazard_lights(False)
            
            # Sincronizar UI
            self.dashboard.set_brake_visual(False)
            self.dashboard.set_hazard_visual(False)
            
            return "SAFE"

    def _create_simulated_frame(self):
        """Crea un frame sintético elegante si no hay una cámara web física disponible."""
        # Frame azul oscuro cyber con gradiente
        img = np.zeros((480, 640, 3), dtype=np.uint8)
        img[:, :] = (32, 20, 16) # Color de fondo BGR
        
        # Dibujar rejilla cyber
        for x in range(0, 640, 40):
            cv2.line(img, (x, 0), (x, 480), (45, 30, 24), 1)
        for y in range(0, 480, 40):
            cv2.line(img, (y_coordinate_line := y, 0), (y_coordinate_line, 640), (45, 30, 24), 1) # Note: simple lines
            cv2.line(img, (0, y), (640, y), (45, 30, 24), 1)
            
        # Dibujar un radar/círculo en el centro
        cv2.circle(img, (320, 240), 120, (100, 60, 40), 1)
        cv2.circle(img, (320, 240), 180, (100, 60, 40), 1)
        
        # Animación oscilante para simular escaneo en vivo
        scan_y = int(240 + 150 * np.sin(time.time() * 2))
        cv2.line(img, (80, scan_y), (560, scan_y), (0, 140, 255), 2)
        
        # Dibujar cara simplificada simulada para que MediaPipe no falle del todo,
        # o simplemente mostrar el texto
        cv2.putText(img, "ESCANER DE CABINA - MODO SIMULACION", (100, 50), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 140, 255), 2)
        cv2.putText(img, "Conecte una camara USB para deteccion real.", (120, 430), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 66), 1)
        
        # Dibujar una cara vectorial simple en el centro para dar mejor aspecto
        cv2.circle(img, (320, 220), 60, (200, 150, 120), -1) # Cabeza
        cv2.circle(img, (300, 210), 8, (255, 255, 255), -1)   # Ojo izq
        cv2.circle(img, (340, 210), 8, (255, 255, 255), -1)   # Ojo der
        cv2.circle(img, (300, 210), 3, (0, 0, 0), -1)
        cv2.circle(img, (340, 210), 3, (0, 0, 0), -1)
        
        # Boca parpadeante simulada
        mouth_r = int(5 + 10 * abs(np.sin(time.time())))
        cv2.ellipse(img, (320, 250), (15, mouth_r), 0, 0, 180, (0, 0, 255), -1)
        
        return img

    def stop(self):
        """Detiene de forma limpia todos los hilos y recursos."""
        self.is_running = False
        self.dashboard.log_message("Deteniendo hilos y cerrando aplicación...")
        
        if self.cap is not None and self.cap.isOpened():
            self.cap.release()
            
        self.audio.stop_all()
        self.actuators.close()
        
        print("[App] Detención completa.")


if __name__ == "__main__":
    app = DriverSafetyApp()
    app.start()
