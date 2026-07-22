
import tkinter as tk
import customtkinter as ctk
from PIL import Image, ImageTk
import time
import cv2

from ui.widgets import CircularGauge, HazardLightIndicator, BrakeLeverVisualizer
import config

# Configurar el estilo visual general de CustomTkinter
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue") # Acento azul eléctrico estándar

class DriverSafetyDashboard(ctk.CTk):
    def __init__(self, on_close_callback=None):
        super().__init__()
        
        self.on_close_callback = on_close_callback
        
        # 1. Configuración de la Ventana Principal
        self.title("PEVICO - Panel de Seguridad Inteligente del Conductor")
        self.geometry("1100x680")
        self.minsize(1000, 620)
        self.configure(fg_color="#0F1016") # Fondo gris/negro ultra oscuro premium
        
        # Vincular cierre de ventana
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Variables de control ajustables en tiempo real desde la UI
        self.ear_thresh_var = tk.DoubleVar(value=config.EAR_THRESHOLD)
        self.mar_thresh_var = tk.DoubleVar(value=config.MAR_THRESHOLD)
        self.prediction_mode = tk.StringVar(value="IA") # Modos: IA, Manual
        
        # Estados actuales del sistema para actualización de widgets
        self.current_state = "SAFE" # SAFE, WARNING, EMERGENCY
        
        self.build_ui()
        self.log_message("Sistema de seguridad y monitoreo iniciado correctamente.")

    def build_ui(self):
        """Construye el layout responsivo del Dashboard."""
        # Grid layout de 1 fila y 2 columnas principales (Cámara izquierda 60%, Controles derecha 40%)
        self.grid_columnconfigure(0, weight=3) # Cámara
        self.grid_columnconfigure(1, weight=2) # Controles/Métricas
        self.grid_rowconfigure(0, weight=1)
        
        # ==========================================
        # PANEL IZQUIERDO: Transmisión de Cámara Web
        # ==========================================
        self.left_panel = ctk.CTkFrame(self, fg_color="#14151F", corner_radius=15, border_width=1, border_color="#1F2130")
        self.left_panel.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        self.left_panel.grid_rowconfigure(0, weight=1)
        self.left_panel.grid_columnconfigure(0, weight=1)
        
        # Etiqueta para incrustar los fotogramas de video
        self.video_label = ctk.CTkLabel(self.left_panel, text="Esperando señal de cámara...", text_color="#5B5F84",
                                        font=ctk.CTkFont(family="Outfit", size=16, weight="bold"))
        self.video_label.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        # Panel flotante de estado en la parte inferior de la cámara (HUD)
        self.hud_frame = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        self.hud_frame.grid(row=1, column=0, padx=15, pady=(0, 15), sticky="ew")
        
        self.status_card = ctk.CTkFrame(self.hud_frame, fg_color="#181926", border_width=1, border_color="#2D2F45", height=50)
        self.status_card.pack(fill="x", expand=True)
        
        self.status_title = ctk.CTkLabel(self.status_card, text="ESTADO DEL CONDUCTOR: ", 
                                         font=ctk.CTkFont(family="Outfit", size=12, weight="bold"), text_color="#A0A0B0")
        self.status_title.pack(side="left", padx=(15, 5), pady=10)
        
        self.status_badge = ctk.CTkLabel(self.status_card, text="SEGURO", 
                                         font=ctk.CTkFont(family="Outfit", size=14, weight="bold"),
                                         text_color="#00FF42", fg_color="#0D2E14", corner_radius=6, height=28, width=100)
        self.status_badge.pack(side="left", padx=5, pady=10)
        
        self.fps_label = ctk.CTkLabel(self.status_card, text="FPS: 0.0", 
                                      font=ctk.CTkFont(family="Outfit", size=11), text_color="#7A7C9A")
        self.fps_label.pack(side="right", padx=15, pady=10)
        
        # ==========================================
        # PANEL DERECHO: Controles, Medidores y Logs
        # ==========================================
        self.right_panel = ctk.CTkScrollableFrame(self, fg_color="#14151F", corner_radius=15, border_width=1, border_color="#1F2130")
        self.right_panel.grid(row=0, column=1, padx=(0, 20), pady=20, sticky="nsew")
        
        # 1. Medidores Circulares (Gauges)
        self.gauges_frame = ctk.CTkFrame(self.right_panel, fg_color="transparent")
        self.gauges_frame.pack(fill="x", padx=10, pady=10)
        self.gauges_frame.grid_columnconfigure(0, weight=1)
        self.gauges_frame.grid_columnconfigure(1, weight=1)
        
        self.gauge_ear = CircularGauge(self.gauges_frame, size=115, title="Ojos Abiertos (EAR)", min_val=0.0, max_val=0.45)
        self.gauge_ear.grid(row=0, column=0, padx=5, pady=5)
        
        self.gauge_mar = CircularGauge(self.gauges_frame, size=115, title="Apertura Boca (MAR)", min_val=0.0, max_val=0.90)
        self.gauge_mar.grid(row=0, column=1, padx=5, pady=5)
        
        # 2. Visualizadores de Actuación del Vehículo
        self.actuators_frame = ctk.CTkFrame(self.right_panel, fg_color="transparent")
        self.actuators_frame.pack(fill="x", padx=10, pady=(10, 5))
        
        self.visualizer_brake = BrakeLeverVisualizer(self.actuators_frame)
        self.visualizer_brake.pack(fill="x", pady=5)
        
        self.visualizer_hazard = HazardLightIndicator(self.actuators_frame)
        self.visualizer_hazard.pack(fill="x", pady=5)
        
        # 3. Terminal de Logs de Eventos
        self.terminal_frame = ctk.CTkFrame(self.right_panel, fg_color="#181926", border_width=1, border_color="#2D2F45")
        self.terminal_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.terminal_title = ctk.CTkLabel(
            self.terminal_frame, 
            text="HISTORIAL DE INCIDENCIAS EN CONDUCCIÓN", 
            font=ctk.CTkFont(family="Outfit", size=10, weight="bold"),
            text_color="#7A7C9A"
        )
        self.terminal_title.pack(anchor="w", padx=15, pady=(10, 5))
        
        self.log_textbox = ctk.CTkTextbox(
            self.terminal_frame, 
            height=130, 
            fg_color="#11121B", 
            text_color="#FFFFFF",
            font=ctk.CTkFont(family="Consolas", size=11),
            corner_radius=8,
            border_width=0
        )
        self.log_textbox.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        self.log_textbox.configure(state="disabled") # Solo lectura por defecto
        
        # 4. Panel de Calibración de Sensibilidad
        self.calib_frame = ctk.CTkFrame(self.right_panel, fg_color="#181926", border_width=1, border_color="#2D2F45")
        self.calib_frame.pack(fill="x", padx=10, pady=10)
        
        self.calib_title = ctk.CTkLabel(
            self.calib_frame, 
            text="AJUSTE DE SENSIBILIDAD EN TIEMPO REAL", 
            font=ctk.CTkFont(family="Outfit", size=11, weight="bold"),
            text_color="#A0A0B0"
        )
        self.calib_title.pack(anchor="w", padx=15, pady=(10, 5))
        
        # Control Deslizante EAR (Ojos)
        self.ear_slider_label = ctk.CTkLabel(self.calib_frame, text="Umbral Sueño (Ojos EAR): 0.22", font=ctk.CTkFont(family="Outfit", size=11), text_color="#A0A0B0")
        self.ear_slider_label.pack(anchor="w", padx=15, pady=(5, 0))
        
        self.ear_slider = ctk.CTkSlider(
            self.calib_frame, 
            from_=0.15, 
            to=0.30, 
            variable=self.ear_thresh_var,
            number_of_steps=15,
            command=self._update_ear_slider_label
        )
        self.ear_slider.pack(fill="x", padx=15, pady=(0, 10))
        
        # Control Deslizante MAR (Bostezos)
        self.mar_slider_label = ctk.CTkLabel(self.calib_frame, text="Umbral Cansancio (MAR Bostezos): 0.50", font=ctk.CTkFont(family="Outfit", size=11), text_color="#A0A0B0")
        self.mar_slider_label.pack(anchor="w", padx=15, pady=(5, 0))
        
        self.mar_slider = ctk.CTkSlider(
            self.calib_frame, 
            from_=0.35, 
            to=0.70, 
            variable=self.mar_thresh_var,
            number_of_steps=35,
            command=self._update_mar_slider_label
        )
        self.mar_slider.pack(fill="x", padx=15, pady=(0, 10))
        
        # Modo de Evaluación: IA vs Reglas Manuales
        self.mode_label = ctk.CTkLabel(self.calib_frame, text="Modo de Evaluación:", font=ctk.CTkFont(family="Outfit", size=11, weight="bold"), text_color="#A0A0B0")
        self.mode_label.pack(anchor="w", padx=15, pady=(5, 0))
        
        self.mode_segmented_button = ctk.CTkSegmentedButton(
            self.calib_frame,
            values=["IA", "Manual"],
            variable=self.prediction_mode,
            font=ctk.CTkFont(family="Outfit", size=11),
            selected_color="#00FF42",
            selected_hover_color="#00D035",
            text_color="#FFFFFF"
        )
        self.mode_segmented_button.pack(fill="x", padx=15, pady=(5, 15))

    def _update_ear_slider_label(self, val):
        self.ear_slider_label.configure(text=f"Umbral Sueño (Ojos EAR): {val:.2f}")
        config.EAR_THRESHOLD = val

    def _update_mar_slider_label(self, val):
        self.mar_slider_label.configure(text=f"Umbral Cansancio (MAR Bostezos): {val:.2f}")
        config.MAR_THRESHOLD = val

    def log_message(self, message):
        """Agrega un log con marca de tiempo al terminal interno."""
        timestamp = time.strftime("%H:%M:%S")
        self.log_textbox.configure(state="normal")
        self.log_textbox.insert("end", f"[{timestamp}] {message}\n")
        self.log_textbox.see("end")
        self.log_textbox.configure(state="disabled")

    def update_frame(self, cv_img):
        """Convierte una matriz BGR de OpenCV a Image de Tkinter y actualiza el frame izquierdo."""
        # Redimensionar el frame para ajustarse al panel de la UI manteniendo una relación fluida
        # Tamaño recomendado en panel: ~600x450 px
        h_panel = self.video_label.winfo_height()
        w_panel = self.video_label.winfo_width()
        
        # Prevenir tamaños inválidos en las primeras etapas de renderizado
        if h_panel < 50 or w_panel < 50:
            h_panel, w_panel = 450, 600
            
        cv_img_resized = cv2_resize_keep_aspect(cv_img, w_panel, h_panel)
        
        # Convertir BGR a RGB
        cv_img_rgb = cv2.cvtColor(cv_img_resized, cv2.COLOR_BGR2RGB)
        img_rgb = Image.fromarray(cv_img_rgb)
        
        # Convertir a formato Tkinter PhotoImage
        img_tk = ImageTk.PhotoImage(image=img_rgb)
        
        # Asignar a la etiqueta de video
        self.video_label.configure(image=img_tk, text="")
        # Guardar referencia para evitar recolección de basura
        self.video_label._image_ref = img_tk

    def update_metrics(self, ear, mar, state, fps):
        """Actualiza los medidores circulares, estado de alerta y FPS de la UI."""
        self.gauge_ear.set_value(ear)
        self.gauge_mar.set_value(mar)
        self.fps_label.configure(text=f"FPS: {fps:.1f}")
        
        if self.current_state != state:
            self.current_state = state
            
            # Cambiar colores del distintivo (Badge) de la UI según el estado
            if state == "SAFE":
                self.status_badge.configure(
                    text="SEGURO",
                    text_color="#00FF42",
                    fg_color="#0D2E14"
                )
            elif state == "WARNING":
                self.status_badge.configure(
                    text="PRECAUCIÓN",
                    text_color="#FFD200",
                    fg_color="#3B3004"
                )
            else: # EMERGENCY
                self.status_badge.configure(
                    text="¡PELIGRO!",
                    text_color="#FF003C",
                    fg_color="#3A0D18"
                )

    def set_brake_visual(self, active):
        """Jala o libera visualmente la palanca de freno."""
        self.visualizer_brake.set_pulled(active)

    def set_hazard_visual(self, active):
        """Enciende o apaga visualmente el indicador de intermitentes."""
        self.visualizer_hazard.set_active(active)

    def on_close(self):
        """Llama al callback de cierre y destruye de forma segura la ventana."""
        if self.on_close_callback:
            self.on_close_callback()
        self.destroy()


def cv2_resize_keep_aspect(cv_img, max_w, max_h):
    """Redimensiona una imagen de OpenCV conservando la relación de aspecto."""
    import cv2
    h, w, _ = cv_img.shape
    aspect = w / h
    
    if max_w / max_h > aspect:
        new_h = max_h
        new_w = int(max_h * aspect)
    else:
        new_w = max_w
        new_h = int(max_w / aspect)
        
    return cv2.resize(cv_img, (new_w, new_h))
