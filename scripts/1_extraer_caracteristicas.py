import os
import cv2
import csv
import sys

# Asegurar que Python pueda encontrar la carpeta 'core' importando la raíz del proyecto
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(PROJECT_ROOT)

from core.face_mesh import FaceMeshDetector

def extract_features_from_dataset():
    dataset_dir = os.path.join(PROJECT_ROOT, "dataset")
    output_csv = os.path.join(PROJECT_ROOT, "dataset_caracteristicas.csv")
    
    print("==================================================")
    print("INICIANDO EXTRACCIÓN DE CARACTERÍSTICAS (PASO 1)")
    print("==================================================")
    print(f"Buscando dataset en: {dataset_dir}")
    print(f"El resultado se guardará en: {output_csv}\n")
    
    # max_num_faces=1 porque cada imagen del dataset suele tener 1 solo rostro principal
    detector = FaceMeshDetector(max_num_faces=1)
    
    # Carpetas del formato YOLO
    splits = ["train", "valid", "test"]
    
    total_processed = 0
    total_errors = 0
    
    # Abrir archivo CSV para escribir (Sobrescribe si ya existe)
    with open(output_csv, mode='w', newline='') as file:
        writer = csv.writer(file)
        # Escribir la cabecera (Nombres de las columnas)
        writer.writerow(["EAR", "MAR", "Pitch", "Yaw", "Label"])
        
        for split in splits:
            images_dir = os.path.join(dataset_dir, split, "images")
            labels_dir = os.path.join(dataset_dir, split, "labels")
            
            if not os.path.exists(images_dir):
                print(f"Saltando carpeta '{split}': No se encontró la ruta {images_dir}")
                continue
                
            print(f"\nProcesando subconjunto: [{split.upper()}] ...")
            
            # Obtener todas las imágenes en la carpeta
            image_files = [f for f in os.listdir(images_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
            
            if not image_files:
                print("No hay imágenes en esta carpeta.")
                continue
                
            for filename in image_files:
                image_path = os.path.join(images_dir, filename)
                # El archivo de etiqueta tiene el mismo nombre pero termina en .txt
                label_filename = os.path.splitext(filename)[0] + ".txt"
                label_path = os.path.join(labels_dir, label_filename)
                
                # Leer la etiqueta (Respuesta correcta de si está despierto o dormido)
                if not os.path.exists(label_path):
                    continue
                
                with open(label_path, 'r') as lf:
                    lines = lf.readlines()
                    if not lines:
                        continue
                    # La primera línea del TXT de YOLO tiene el formato: "clase_id x y w h"
                    parts = lines[0].strip().split()
                    class_id = int(parts[0]) # 0 = awake (despierto), 1 = drowsy (somnoliento)
                
                # Leer la imagen con OpenCV
                frame = cv2.imread(image_path)
                if frame is None:
                    continue
                
                # Procesar la imagen con MediaPipe (Nuestro código actual)
                metrics = detector.process(frame)
                
                # Si MediaPipe logró detectar un rostro
                if metrics["detected"]:
                    ear = metrics['ear']
                    mar = metrics['mar']
                    pitch = metrics['pitch']
                    yaw = metrics['yaw']
                    
                    # Escribir los números en el archivo Excel (CSV)
                    writer.writerow([ear, mar, pitch, yaw, class_id])
                    total_processed += 1
                else:
                    # MediaPipe falló al encontrar el rostro (imagen borrosa, cortada, etc.)
                    total_errors += 1
                    
                # Mostrar progreso cada 100 imágenes para no saturar la consola
                if total_processed % 100 == 0 and total_processed > 0:
                    print(f" -> Extraídas {total_processed} métricas exitosamente...")
                    
    print("\n==================================================")
    print("¡EXTRACCIÓN FINALIZADA CON ÉXITO!")
    print("==================================================")
    print(f"Imágenes válidas procesadas: {total_processed}")
    print(f"Imágenes ignoradas (Rostro no detectado): {total_errors}")
    print(f"Tu tabla de Excel está lista en: dataset_caracteristicas.csv")
    print("Ya podemos pasar al Paso 2 (Entrenar el modelo).")

if __name__ == "__main__":
    extract_features_from_dataset()
