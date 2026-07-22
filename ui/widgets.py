# ui/widgets.py
"""
Widgets gráficos personalizados y avanzados usando Tkinter Canvas y CustomTkinter.
Implementa medidores circulares tipo tacómetro, luces de emergencia intermitentes y freno de mano animado.
"""

import tkinter as tk
import customtkinter as ctk
import math
import time

class CircularGauge(ctk.CTkFrame):
    """
    Medidor circular premium y futurista para representar métricas de conducción
    tales como EAR (Ojos), MAR (Boca) y Nivel de Fatiga.
    """
    def __init__(self, parent, size=150, title="Métrica", min_val=0.0, max_val=1.0, 
                 color_safe="#00FF42", color_warn="#FFD200", color_danger="#FF0000", **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        
        self.size = size
        self.title = title
        self.min_val = min_val
        self.max_val = max_val
        self.value = min_val
        
        self.color_safe = color_safe
        self.color_warn = color_warn
        self.color_danger = color_danger
        
        # UI Layout
        self.label_title = ctk.CTkLabel(self, text=self.title, font=ctk.CTkFont(family="Outfit", size=13, weight="bold"), text_color="#A0A0B0")
        self.label_title.pack(pady=(0, 2))
        
        # Canvas para dibujar el arco circular
        self.canvas = tk.Canvas(
            self, 
            width=self.size, 
            height=self.size, 
            bg="#1A1B26",            # Color oscuro de fondo coordinado con el dashboard
            highlightthickness=0
        )
        self.canvas.pack()
        
        self.label_val = ctk.CTkLabel(self, text="0.00", font=ctk.CTkFont(family="Outfit", size=16, weight="bold"))
        self.label_val.pack(pady=(2, 0))
        
        # Configurar colores de fondo del canvas redondeado
        self.canvas.configure(bg=self.cget("fg_color") if self.cget("fg_color") != "transparent" else "#14151F")
        
        self.draw_gauge()

    def set_value(self, val):
        """Actualiza el valor del medidor y lo redibuja."""
        # Limitar valor dentro de rangos
        self.value = max(self.min_val, min(self.max_val, val))
        self.label_val.configure(text=f"{self.value:.2f}")
        self.draw_gauge()

    def draw_gauge(self):
        """Dibuja el medidor circular con sus arcos y colores dinámicos."""
        self.canvas.delete("all")
        
        cx = self.size / 2
        cy = self.size / 2
        r = (self.size / 2) - 12 # Radio
        
        # 1. Dibujar anillo de fondo (Gris oscuro)
        self.canvas.create_arc(
            cx - r, cy - r, cx + r, cy + r,
            start=-220, extent=260,
            style="arc", outline="#252636", width=8
        )
        
        # 2. Calcular porcentaje y ángulo
        val_range = self.max_val - self.min_val
        pct = (self.value - self.min_val) / val_range if val_range != 0 else 0.0
        pct = max(0.0, min(1.0, pct))
        
        extent_angle = -260 * pct
        
        # 3. Determinar color dinámico según el valor
        if pct < 0.5:
            # Transición suave de colores o color seguro
            color = self.color_safe
        elif pct < 0.75:
            color = self.color_warn
        else:
            color = self.color_danger
            
        # Para métricas invertidas (como EAR donde menor es más peligroso)
        if "ojos" in self.title.lower() or "ear" in self.title.lower():
            if self.value > 0.25:
                color = self.color_safe
            elif self.value > 0.21:
                color = self.color_warn
            else:
                color = self.color_danger
                
        # 4. Dibujar anillo de progreso activo
        if extent_angle != 0:
            self.canvas.create_arc(
                cx - r, cy - r, cx + r, cy + r,
                start=-220, extent=extent_angle,
                style="arc", outline=color, width=10,
                tags="progress"
            )
            
        # 5. Dibujar un pequeño punto indicador brillante en la punta del arco
        angle_rad = math.radians(-220 + extent_angle)
        px = cx + r * math.cos(angle_rad)
        py = cy - r * math.sin(angle_rad)
        self.canvas.create_oval(
            px - 5, py - 5, px + 5, py + 5,
            fill=color, outline="#FFFFFF", width=1
        )
        
        # 6. Dibujar efecto de resplandor sutil (glow)
        self.canvas.create_text(
            cx, cy, 
            text=f"{int(pct*100)}%", 
            fill="#FFFFFF", 
            font=("Outfit", 12, "bold")
        )


class HazardLightIndicator(ctk.CTkFrame):
    """
    Indicador de luces intermitentes vehiculares.
    Parpadea con una animación suave de 0.5s entre rojo y gris cuando está activo.
    """
    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color="#181926", border_width=1, border_color="#2D2F45", **kwargs)
        
        self.is_active = False
        self.flash_state = False
        
        # Título
        self.title_label = ctk.CTkLabel(
            self, 
            text="LUCES INTERMITENTES", 
            font=ctk.CTkFont(family="Outfit", size=11, weight="bold"),
            text_color="#A0A0B0"
        )
        self.title_label.pack(pady=(10, 5))
        
        # Contenedor de las dos flechas (Luces de advertencia izquierda y derecha)
        self.canvas = tk.Canvas(self, width=200, height=60, bg="#14151F", highlightthickness=0)
        self.canvas.pack(padx=15, pady=(5, 10))
        
        self.draw_arrows()
        self._animate()

    def draw_arrows(self):
        self.canvas.delete("all")
        
        # Color según estado
        left_color = "#FF003C" if (self.is_active and self.flash_state) else "#2D2F45"
        right_color = "#FF003C" if (self.is_active and self.flash_state) else "#2D2F45"
        
        # Dibujar Flecha Izquierda (◄)
        # Puntos: Punta izquierda (20,30), Superior derecha (60,10), Cuerpo arriba (60, 20), Base arriba (90, 20)...
        self.canvas.create_polygon(
            20, 30,  # Punta
            55, 10,  # Esquina arriba
            55, 22,  # Hombro arriba
            90, 22,  # Extremo arriba
            90, 38,  # Extremo abajo
            55, 38,  # Hombro abajo
            55, 50,  # Esquina abajo
            fill=left_color, outline="#FF003C" if self.is_active and self.flash_state else "#1F2130", width=1
        )
        
        # Dibujar Flecha Derecha (►)
        self.canvas.create_polygon(
            180, 30, # Punta
            145, 10, # Esquina arriba
            145, 22, # Hombro arriba
            110, 22, # Extremo arriba
            110, 38, # Extremo abajo
            145, 38, # Hombro abajo
            145, 50, # Esquina abajo
            fill=right_color, outline="#FF003C" if self.is_active and self.flash_state else "#1F2130", width=1
        )
        
        # Triángulo central clásico de Hazard ⚠️
        warn_color = "#FF8C00" if (self.is_active and self.flash_state) else "#2D2F45"
        self.canvas.create_polygon(
            100, 15,
            88, 42,
            112, 42,
            fill="", outline=warn_color, width=3
        )
        # Exclamación adentro
        self.canvas.create_line(100, 23, 100, 34, fill=warn_color, width=2)
        self.canvas.create_oval(99, 37, 101, 39, fill=warn_color, outline=warn_color)

    def set_active(self, active):
        """Enciende o apaga las luces intermitentes."""
        self.is_active = active
        if not active:
            self.flash_state = False
            self.draw_arrows()

    def _animate(self):
        """Mantiene el parpadeo cíclico de las intermitentes de forma asíncrona en la UI."""
        if self.is_active:
            self.flash_state = not self.flash_state
            self.draw_arrows()
            
        # Ejecutar cada 400ms para un parpadeo dinámico realista
        self.after(400, self._animate)


class BrakeLeverVisualizer(ctk.CTkFrame):
    """
    Visualizador animado del freno de mano mecánico de emergencia.
    Muestra la palanca inclinada arriba/liberada en verde (0°)
    o jalada hacia abajo/bloqueada en rojo brillante (45°) con animación de transición.
    """
    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color="#181926", border_width=1, border_color="#2D2F45", **kwargs)
        
        self.is_pulled = False
        self.current_angle = 15.0 # Ángulo actual para la animación de rotación
        self.target_angle = 15.0
        
        self.title_label = ctk.CTkLabel(
            self, 
            text="FRENO DE EMERGENCIA", 
            font=ctk.CTkFont(family="Outfit", size=11, weight="bold"),
            text_color="#A0A0B0"
        )
        self.title_label.pack(pady=(10, 5))
        
        self.canvas = tk.Canvas(self, width=200, height=80, bg="#14151F", highlightthickness=0)
        self.canvas.pack(padx=15, pady=(5, 10))
        
        self.draw_lever()
        self._update_animation()

    def draw_lever(self):
        self.canvas.delete("all")
        
        # Color de estado
        glow_color = "#FF003C" if self.is_pulled else "#00FF42"
        lever_color = "#3A3D5A" if not self.is_pulled else "#8B0000"
        
        # Centro de rotación de la palanca (Eje de pivote a la izquierda)
        px, py = 40, 55
        
        # Calcular coordenadas de la palanca rotada
        # Ángulo en radianes
        rad = math.radians(self.current_angle)
        
        # Longitud de la palanca
        length = 100
        width = 16
        
        # Punta de la palanca (extremo)
        tx = px + length * math.cos(rad)
        ty = py - length * math.sin(rad)
        
        # Esquinas para el cuerpo rectangular de la palanca
        dx = (width / 2) * math.sin(rad)
        dy = (width / 2) * math.cos(rad)
        
        p1_x, p1_y = px - dx, py - dy
        p2_x, p2_y = px + dx, py + dy
        p3_x, p3_y = tx + dx, ty + dy
        p4_x, p4_y = tx - dx, ty - dy
        
        # 1. Dibujar el soporte de base
        self.canvas.create_oval(px-20, py-20, px+20, py+20, fill="#252636", outline="#3A3D5A", width=2)
        
        # 2. Dibujar el mango físico de la palanca (el cuerpo)
        self.canvas.create_polygon(
            p1_x, p1_y, p2_x, p2_y, p3_x, p3_y, p4_x, p4_y,
            fill=lever_color, outline="#5B5F84", width=1.5
        )
        
        # 3. Botón de liberación en la punta de la palanca
        bx = tx + 8 * math.cos(rad)
        by = ty - 8 * math.sin(rad)
        self.canvas.create_line(tx, ty, bx, by, fill="#FFD200", width=6)
        
        # 4. Anillo de estado brillante en la base (Glow indicativo de freno)
        self.canvas.create_oval(px-10, py-10, px+10, py+10, fill=glow_color, outline="#FFFFFF", width=1.5)
        
        # 5. Texto de estado en el canvas
        status_text = "FRENANDO" if self.is_pulled else "LIBERADO"
        self.canvas.create_text(
            135, 60, 
            text=status_text, 
            fill=glow_color, 
            font=("Outfit", 12, "bold")
        )

    def set_pulled(self, pulled):
        """Activa o desactiva la palanca del freno."""
        self.is_pulled = pulled
        # Si se jala el freno, el ángulo objetivo sube (ej: 48°), si se libera, baja (ej: 12°)
        self.target_angle = 48.0 if pulled else 12.0

    def _update_animation(self):
        """Suaviza la rotación de la palanca con interpolación para efecto premium de animación."""
        diff = self.target_angle - self.current_angle
        if abs(diff) > 0.5:
            # Acercarse al objetivo (15% del trayecto restante por frame)
            self.current_angle += diff * 0.20
            self.draw_lever()
            
        self.after(30, self._update_animation)
