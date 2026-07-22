# utils/audio_player.py
"""
Módulo de Alertas Sonoras y Voz Sintetizada.
Utiliza pyttsx3 en un hilo secundario de forma segura mediante colas (Queue)
e integra beeps y alarmas de emergencia de alta potencia usando winsound.
"""

import threading
import queue
import time
import winsound
import pyttsx3
import config

class AudioAlertSystem:
    def __init__(self):
        # Cola de mensajes de texto para sintetizar
        self.speech_queue = queue.Queue()
        
        # Bandera para controlar la reproducción de la sirena/alarma de emergencia
        self.siren_active = False
        
        # Historial de alertas de voz para evitar spam
        self.last_speech_time = {}
        self.SPAM_COOLDOWN = 6.0 # Segundos mínimos antes de repetir la misma alerta
        
        # Iniciar hilo de voz sintetizada
        self.speech_thread = threading.Thread(target=self._speech_worker, daemon=True)
        self.speech_thread.start()
        
        # Iniciar hilo para sirena de emergencia
        self.siren_thread = threading.Thread(target=self._siren_worker, daemon=True)
        self.siren_thread.start()

    def _speech_worker(self):
        """Worker que procesa y reproduce los archivos de audio locales en segundo plano."""
        import os
        import ctypes
        
        # Mapeo de frases a archivos de audio locales
        audio_mapping = {
            config.MSG_WARN_DISTRACTED: "assets/audio/distracted.mp3",
            config.MSG_WARN_YAWNING: "assets/audio/yawning.mp3",
            config.MSG_CRITICAL_SLEEP: "assets/audio/critical.mp3"
        }
        
        while True:
            try:
                # Esperar a que haya un mensaje en la cola
                msg = self.speech_queue.get()
                if msg is None:
                    break
                
                # Obtener la ruta del archivo de audio correspondiente
                audio_file = audio_mapping.get(msg)
                
                if audio_file and os.path.exists(audio_file):
                    try:
                        # Asegurarse de cerrar cualquier alias previo
                        ctypes.windll.winmm.mciSendStringW("close alert_sound", None, 0, 0)
                        # Abrir el archivo
                        open_cmd = f'open "{os.path.abspath(audio_file)}" type mpegvideo alias alert_sound'
                        ctypes.windll.winmm.mciSendStringW(open_cmd, None, 0, 0)
                        # Reproducir esperando a que termine (el hilo worker se bloquea, previniendo empalmes, pero la app sigue fluida)
                        ctypes.windll.winmm.mciSendStringW("play alert_sound wait", None, 0, 0)
                        # Cerrar alias al terminar
                        ctypes.windll.winmm.mciSendStringW("close alert_sound", None, 0, 0)
                    except Exception as err:
                        print(f"[Audio Worker] Error al reproducir '{audio_file}': {err}")
                else:
                    # Fallback simple
                    print(f"[Audio Fallback] Alerta: '{msg}'")
                    winsound.Beep(1000, 300)
                    
                self.speech_queue.task_done()
                
            except Exception as e:
                print(f"[Audio Worker Queue] Error: {e}")
                time.sleep(0.5)

    def _siren_worker(self):
        """Generador de alarma acústica de emergencia intermitente."""
        while True:
            if self.siren_active:
                try:
                    # Un pitido de alta frecuencia de 2000Hz por 150ms
                    # Seguido de un pitido de 1500Hz por 150ms para simular sirena
                    winsound.Beep(2000, 150)
                    winsound.Beep(1500, 150)
                except Exception as e:
                    print(f"[Siren Worker] Error Beep: {e}")
                    time.sleep(0.5)
            else:
                time.sleep(0.1)

    def speak(self, text):
        """Agrega un mensaje a la cola de voz sintetizada respetando el cooldown anti-spam."""
        now = time.time()
        
        # Evitar repetir el mismo mensaje antes de que pase el tiempo de cooldown
        if text in self.last_speech_time:
            if now - self.last_speech_time[text] < self.SPAM_COOLDOWN:
                return # Ignorar para evitar saturar al conductor
                
        self.last_speech_time[text] = now
        self.speech_queue.put(text)

    def trigger_warn_beep(self):
        """Emite un pitido de precaución simple no bloqueante."""
        threading.Thread(
            target=lambda: winsound.Beep(1200, 200), 
            daemon=True
        ).start()

    def set_emergency_siren(self, active):
        """Activa o desactiva la sirena continua de emergencia."""
        self.siren_active = active

    def stop_all(self):
        """Detiene todas las alarmas y limpia la cola."""
        self.siren_active = False
        while not self.speech_queue.empty():
            try:
                self.speech_queue.get_now_exclusive()
                self.speech_queue.task_done()
            except Exception:
                break
