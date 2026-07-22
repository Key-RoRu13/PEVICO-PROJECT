# core/face_mesh.py
"""
Detector de Landmarks Faciales y Estimador de Pose mediante MediaPipe FaceLandmarker (API Moderna).
Calcula EAR (Eye Aspect Ratio), MAR (Mouth Aspect Ratio) y ángulos de rotación de la cabeza.
Descarga automáticamente el modelo si no está presente.
"""

import cv2
import os
import urllib.request
import numpy as np
import math
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

class FaceMeshDetector:
    def __init__(self, max_num_faces=3, min_detection_confidence=0.5, min_tracking_confidence=0.5):
        # Configurar y verificar modelo .task de MediaPipe
        self.model_dir = "assets/models"
        self.model_path = os.path.join(self.model_dir, "face_landmarker.task")
        self._ensure_model_exists()
        
        # Inicializar el FaceLandmarker usando la API moderna de MediaPipe Tasks
        try:
            self.base_options = python.BaseOptions(model_asset_path=self.model_path)
            self.options = vision.FaceLandmarkerOptions(
                base_options=self.base_options,
                output_face_blendshapes=True,
                output_facial_transformation_matrixes=True,
                num_faces=max_num_faces
            )
            self.detector = vision.FaceLandmarker.create_from_options(self.options)
            print("[MediaPipe] FaceLandmarker moderno inicializado correctamente.")
        except Exception as e:
            print(f"[MediaPipe] Error al inicializar FaceLandmarker: {e}")
            raise e
        
        # Índices de landmarks de MediaPipe para los ojos y boca (idénticos a la versión clásica)
        # Ojo Izquierdo
        self.LEFT_EYE = [362, 385, 386, 387, 263, 373, 374, 380]
        # Ojo Derecho
        self.RIGHT_EYE = [33, 160, 159, 158, 133, 153, 145, 144]
        
        # Puntos del Ojo para calcular EAR (Pares verticales y extremos horizontales)
        self.LEFT_EYE_VERT = [(385, 380), (386, 374), (387, 373)]
        self.LEFT_EYE_HORIZ = (362, 263)
        
        self.RIGHT_EYE_VERT = [(160, 144), (159, 145), (158, 153)]
        self.RIGHT_EYE_HORIZ = (33, 133)
        
        # Boca (Bostezos): Labios Internos
        self.MOUTH_VERT = [(82, 87), (13, 14), (312, 317)]
        self.MOUTH_HORIZ = (78, 308)

        # Landmarks faciales de referencia para estimación de pose 3D de cabeza (SolvePnP)
        self.POSE_LANDMARKS = [4, 152, 263, 33, 308, 61]
        
        # Puntos 3D genéricos del modelo de cabeza humana (en milímetros)
        self.model_points_3d = np.array([
            (0.0, 0.0, 0.0),             # Punta de la nariz
            (0.0, -330.0, -65.0),        # Mentón/Barbilla
            (-225.0, 170.0, -135.0),     # Extremo exterior Ojo Izquierdo
            (225.0, 170.0, -135.0),      # Extremo exterior Ojo Derecho
            (-150.0, -150.0, -125.0),    # Comisura Boca Izquierda
            (150.0, -150.0, -125.0)      # Comisura Boca Derecha
        ], dtype=np.float64)

    def _ensure_model_exists(self):
        """Asegura que el archivo face_landmarker.task exista, descargándolo si es necesario."""
        if not os.path.exists(self.model_path):
            print(f"[MediaPipe] No se encontró '{self.model_path}'. Descargando modelo oficial de Google...")
            os.makedirs(self.model_dir, exist_ok=True)
            url = "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task"
            try:
                # Descargar con barra de progreso simple en consola
                urllib.request.urlretrieve(url, self.model_path)
                print("[MediaPipe] Descarga finalizada con éxito.")
            except Exception as e:
                print(f"[MediaPipe] Error crítico al descargar el modelo: {e}")
                raise e

    def _euclidean_distance(self, p1, p2):
        """Calcula la distancia euclidiana entre dos puntos np.array."""
        return np.linalg.norm(p1 - p2)

    def _calculate_ear(self, landmarks, vert_indices, horiz_indices):
        """Calcula el Eye Aspect Ratio (EAR) para un ojo."""
        # Distancias verticales
        d_vert = 0.0
        for top, bottom in vert_indices:
            p_top = landmarks[top]
            p_bottom = landmarks[bottom]
            d_vert += self._euclidean_distance(p_top, p_bottom)
        d_vert /= len(vert_indices)
        
        # Distancia horizontal
        left, right = horiz_indices
        p_left = landmarks[left]
        p_right = landmarks[right]
        d_horiz = self._euclidean_distance(p_left, p_right)
        
        # Evitar división por cero
        if d_horiz == 0:
            return 0.0
        return d_vert / d_horiz

    def _calculate_mar(self, landmarks):
        """Calcula el Mouth Aspect Ratio (MAR) para la boca."""
        d_vert = 0.0
        for top, bottom in self.MOUTH_VERT:
            p_top = landmarks[top]
            p_bottom = landmarks[bottom]
            d_vert += self._euclidean_distance(p_top, p_bottom)
        d_vert /= len(self.MOUTH_VERT)
        
        left, right = self.MOUTH_HORIZ
        p_left = landmarks[left]
        p_right = landmarks[right]
        d_horiz = self._euclidean_distance(p_left, p_right)
        
        if d_horiz == 0:
            return 0.0
        return d_vert / d_horiz

    def _estimate_head_pose(self, landmarks_2d, frame_shape):
        """Estima la rotación de la cabeza (Pitch, Yaw, Roll) usando SolvePnP."""
        h, w, _ = frame_shape
        # Matriz de la cámara (Intrinsics aproximados)
        focal_length = w
        center = (w / 2, h / 2)
        camera_matrix = np.array([
            [focal_length, 0.0, center[0]],
            [0.0, focal_length, center[1]],
            [0.0, 0.0, 1.0]
        ], dtype=np.float64)
        
        dist_coeffs = np.zeros((4, 1)) # Sin distorsión de lente asumida
        
        # Resolver SolvePnP
        success, rvec, tvec = cv2.solvePnP(
            self.model_points_3d, 
            landmarks_2d, 
            camera_matrix, 
            dist_coeffs, 
            flags=cv2.SOLVEPNP_ITERATIVE
        )
        
        if not success:
            return 0.0, 0.0, 0.0, None, None, None
            
        # Obtener matriz de rotación
        rotation_matrix, _ = cv2.Rodrigues(rvec)
        
        # Descomponer los ángulos de Euler
        sy = math.sqrt(rotation_matrix[0,0]**2 + rotation_matrix[1,0]**2)
        singular = sy < 1e-6
        
        if not singular:
            pitch = math.atan2(rotation_matrix[2,1], rotation_matrix[2,2]) * 180.0 / math.pi
            yaw = math.atan2(-rotation_matrix[2,0], sy) * 180.0 / math.pi
            roll = math.atan2(rotation_matrix[1,0], rotation_matrix[0,0]) * 180.0 / math.pi
        else:
            pitch = math.atan2(-rotation_matrix[1,2], rotation_matrix[1,1]) * 180.0 / math.pi
            yaw = math.atan2(-rotation_matrix[2,0], sy) * 180.0 / math.pi
            roll = 0.0
            
        return pitch, yaw, roll, rvec, tvec, camera_matrix

    def process(self, frame):
        """Procesa un frame y extrae métricas del rostro."""
        # Convertir BGR a RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Convertir frame a formato mp.Image de la nueva API
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
        
        # Ejecutar detector
        results = self.detector.detect(mp_image)
        
        metrics = {
            "detected": False,
            "ear": 0.0,
            "left_ear": 0.0,
            "right_ear": 0.0,
            "mar": 0.0,
            "pitch": 0.0,
            "yaw": 0.0,
            "roll": 0.0,
            "landmarks_px": None,
            "pose_projection_lines": None
        }
        
        if results.face_landmarks:
            metrics["detected"] = True
            
            # Buscar la cara más grande (la más cercana a la cámara, probablemente el conductor)
            largest_area = 0
            best_face = results.face_landmarks[0]
            
            for face in results.face_landmarks:
                xs = [lm.x for lm in face]
                ys = [lm.y for lm in face]
                area = (max(xs) - min(xs)) * (max(ys) - min(ys))
                if area > largest_area:
                    largest_area = area
                    best_face = face
                    
            face_landmarks = best_face # Tomar la cara más prominente
            h, w, _ = frame.shape
            
            # Obtener todos los puntos en coordenadas de píxeles y reales normalizadas
            landmarks_px = []
            landmarks_norm = []
            for lm in face_landmarks:
                px_x = int(lm.x * w)
                px_y = int(lm.y * h)
                # lm.z es la profundidad relativa, la escalamos por el ancho para normalizar
                px_z = lm.z 
                landmarks_px.append([px_x, px_y])
                landmarks_norm.append(np.array([lm.x * w, lm.y * h, lm.z * w]))
                
            landmarks_norm = np.array(landmarks_norm)
            
            # 1. Calcular EAR
            left_ear = self._calculate_ear(landmarks_norm, self.LEFT_EYE_VERT, self.LEFT_EYE_HORIZ)
            right_ear = self._calculate_ear(landmarks_norm, self.RIGHT_EYE_VERT, self.RIGHT_EYE_HORIZ)
            metrics["left_ear"] = left_ear
            metrics["right_ear"] = right_ear
            metrics["ear"] = (left_ear + right_ear) / 2.0
            
            # 2. Calcular MAR
            metrics["mar"] = self._calculate_mar(landmarks_norm)
            
            # 3. Estimar Pose de Cabeza
            # Extraer puntos 2D para solvePnP
            pose_points_2d = []
            for idx in self.POSE_LANDMARKS:
                lm = face_landmarks[idx]
                pose_points_2d.append([lm.x * w, lm.y * h])
            pose_points_2d = np.array(pose_points_2d, dtype=np.float64)
            
            pitch, yaw, roll, rvec, tvec, camera_matrix = self._estimate_head_pose(pose_points_2d, frame.shape)
            
            metrics["pitch"] = pitch
            metrics["yaw"] = yaw
            metrics["roll"] = roll
            metrics["landmarks_px"] = landmarks_px
            
            # Calcular líneas de proyección de la pose (eje de la nariz)
            if rvec is not None and tvec is not None:
                # Proyectar eje 3D en la pantalla
                axis_points_3d = np.array([
                    (0.0, 0.0, 0.0),    # Origen (nariz)
                    (0.0, 0.0, 150.0)   # Línea apuntando hacia afuera de la nariz
                ], dtype=np.float64)
                
                dist_coeffs = np.zeros((4, 1))
                imgpts, _ = cv2.projectPoints(axis_points_3d, rvec, tvec, camera_matrix, dist_coeffs)
                
                metrics["pose_projection_lines"] = {
                    "start": (int(imgpts[0].ravel()[0]), int(imgpts[0].ravel()[1])),
                    "end": (int(imgpts[1].ravel()[0]), int(imgpts[1].ravel()[1]))
                }
                
        return metrics

    def draw_annotations(self, frame, metrics, alert_level="SAFE"):
        """Dibuja los landmarks y ejes de pose en el frame."""
        if not metrics["detected"] or metrics["landmarks_px"] is None:
            return frame
            
        annotated_frame = frame.copy()
        
        # Color dinámico basado en el nivel de alerta
        # SAFE: Verde neón, WARNING: Amarillo, CRITICAL: Rojo neón
        if alert_level == "SAFE":
            color_primary = (0, 255, 66)      # Verde brillante
            color_secondary = (0, 180, 40)
        elif alert_level == "WARNING":
            color_primary = (0, 210, 255)     # Amarillo/Oro brillante
            color_secondary = (0, 140, 190)
        else: # CRITICAL
            color_primary = (0, 0, 255)       # Rojo puro
            color_secondary = (0, 0, 180)
            
        lms = metrics["landmarks_px"]
        
        # Calcular y dibujar el Bounding Box (Recuadro) del rostro
        xs = [p[0] for p in lms]
        ys = [p[1] for p in lms]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        
        # Expandir un poco el recuadro (padding)
        pad_x = int((max_x - min_x) * 0.1)
        pad_y = int((max_y - min_y) * 0.1)
        x1, y1 = max(0, min_x - pad_x), max(0, min_y - pad_y)
        x2, y2 = max_x + pad_x, max_y + pad_y
        
        # Dibujar recuadro y etiqueta
        cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color_primary, 2)
        cv2.putText(annotated_frame, "CONDUCTOR", (x1, y1 - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color_primary, 1, cv2.LINE_AA)
        
        # Dibujar contornos simplificados de ojos
        for idx in self.LEFT_EYE:
            cv2.circle(annotated_frame, tuple(lms[idx]), 2, color_secondary, -1)
        for idx in self.RIGHT_EYE:
            cv2.circle(annotated_frame, tuple(lms[idx]), 2, color_secondary, -1)
            
        # Dibujar labios
        for idx in [78, 95, 88, 178, 87, 14, 317, 402, 318, 324, 308, 415, 310, 311, 312, 13, 82, 81, 80, 191]:
            if idx < len(lms):
                cv2.circle(annotated_frame, tuple(lms[idx]), 1, color_secondary, -1)
                
        # Dibujar puntos clave de pose
        for idx in self.POSE_LANDMARKS:
            cv2.circle(annotated_frame, tuple(lms[idx]), 4, color_primary, -1)
            
        # Dibujar vector de dirección de la pose
        proj = metrics["pose_projection_lines"]
        if proj is not None:
            cv2.line(annotated_frame, proj["start"], proj["end"], color_primary, 3)
            cv2.circle(annotated_frame, proj["end"], 5, color_primary, -1)
            
        return annotated_frame
