import os
import cv2
import csv
import sys

# Asegurar que Python pueda encontrar la carpeta 'core' importando la raíz del proyecto
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(PROJECT_ROOT)

from core.face_mesh import FaceMeshDetector

def extract_new_dataset():
    new_dataset_dir = os.path.join(PROJECT_ROOT, "dataset", "newdataset", "Multi class", "train")
    output_csv = os.path.join(PROJECT_ROOT, "dataset_caracteristicas.csv")
    
    print("==================================================")
    print("EXTRACTOR DE CARACTERÍSTICAS: NUEVO DATASET (NTHU)")
    print("==================================================")
    print(f"Buscando imágenes en: {new_dataset_dir}")
    print(f"Los datos se agregarán a: {output_csv}\n")
    
    if not os.path.exists(new_dataset_dir):
        print(f"ERROR: No se encontró la ruta {new_dataset_dir}")
        print("Asegúrate de haber descomprimido el dataset en esa ubicación.")
        return

    # Inicializar detector (max_num_faces=1 porque hay un conductor por imagen)
    detector = FaceMeshDetector(max_num_faces=1)
    
    # Definir carpetas y sus respectivas clases (0 = despierto, 1 = fatiga)
    categories = [
        {"folder": "notdrowsy", "label": 0},
        {"folder": "drowsy", "label": 1}
    ]
    
    total_processed = 0
    total_errors = 0
    
    # Abrir archivo CSV en modo APPEND ('a') para agregar filas al final
    # Si el archivo no existe, lo crea e inserta la cabecera
    file_exists = os.path.exists(output_csv)
    
    with open(output_csv, mode='a', newline='') as file:
        writer = csv.writer(file)
        
        # Si el CSV es nuevo, escribir la cabecera
        if not file_exists or os.path.getsize(output_csv) == 0:
            writer.writerow(["EAR", "MAR", "Pitch", "Yaw", "Label"])
            print("Creado archivo CSV con cabecera.")
        else:
            print("Archivo CSV existente detectado. Agregando nuevas filas al final...")
            
        for category in categories:
            folder_path = os.path.join(new_dataset_dir, category["folder"])
            label = category["label"]
            
            if not os.path.exists(folder_path):
                print(f"Saltando carpeta '{category['folder']}': No existe la ruta.")
                continue
                
            print(f"\nProcesando categoría: [{category['folder'].upper()}] (Etiqueta {label}) ...")
            
            # Obtener todas las imágenes de la carpeta
            image_files = [f for f in os.listdir(folder_path) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
            total_imgs = len(image_files)
            
            if total_imgs == 0:
                print("No hay imágenes en esta carpeta.")
                continue
                
            print(f"Encontradas {total_imgs} imágenes. Procesando...")
            
            for idx, filename in enumerate(image_files):
                image_path = os.path.join(folder_path, filename)
                
                # Leer la imagen
                frame = cv2.imread(image_path)
                if frame is None:
                    continue
                    
                # Extraer características
                metrics = detector.process(frame)
                
                if metrics["detected"]:
                    ear = metrics['ear']
                    mar = metrics['mar']
                    pitch = metrics['pitch']
                    yaw = metrics['yaw']
                    
                    # Escribir en el CSV
                    writer.writerow([ear, mar, pitch, yaw, label])
                    total_processed += 1
                else:
                    total_errors += 1
                    
                # Mostrar progreso cada 200 imágenes
                if total_processed % 200 == 0 and total_processed > 0:
                    print(f" -> Extraídos {total_processed} rostros exitosamente...")
                    
    print("\n==================================================")
    print("¡EXTRACCIÓN DEL NUEVO DATASET COMPLETADA!")
    print("==================================================")
    print(f"Imágenes válidas agregadas: {total_processed}")
    print(f"Imágenes ignoradas (Rostro no detectado): {total_errors}")
    print("El archivo 'dataset_caracteristicas.csv' ha sido enriquecido.")
    print("Ahora puedes volver a entrenar tu modelo ejecutando:")
    print("   python scripts/2_entrenar_modelo.py")

if __name__ == "__main__":
    extract_new_dataset()
