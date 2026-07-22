import pandas as pd
import numpy as np
import os
import sys
import pickle
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
csv_path = os.path.join(PROJECT_ROOT, "dataset_caracteristicas.csv")
model_dir = os.path.join(PROJECT_ROOT, "assets", "models")
model_path = os.path.join(model_dir, "clasificador_fatiga.pkl")

def entrenar_modelo():
    print("==================================================")
    print("INICIANDO ENTRENAMIENTO DEL MODELO (PASO 2)")
    print("==================================================")
    
    if not os.path.exists(csv_path):
        print(f"ERROR: No se encontró el archivo {csv_path}.")
        print("Asegúrate de haber ejecutado el Paso 1 (1_extraer_caracteristicas.py) primero.")
        sys.exit(1)
        
    print(f"Cargando datos tabulares desde: {csv_path}...")
    df = pd.read_csv(csv_path)
    
    print(f"Total de rostros analizados: {len(df)}")
    if len(df) == 0:
        print("ERROR: El archivo CSV está vacío.")
        sys.exit(1)
        
    # Verificar cuántos de cada clase hay
    conteo = df['Label'].value_counts()
    print(f"\nDistribución de datos extraídos:")
    print(f"- Conductores Despiertos (Etiqueta 0): {conteo.get(0, 0)}")
    print(f"- Conductores Somnolientos (Etiqueta 1): {conteo.get(1, 0)}\n")
    
    # Separar características (X) y respuestas/etiquetas (y)
    X = df[['EAR', 'MAR', 'Pitch', 'Yaw']]
    y = df['Label']
    
    # Dividir en datos de Entrenamiento (80%) y Prueba/Examen (20%)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    print("Construyendo y Entrenando Algoritmo Clasificador (Random Forest)...")
    # Usamos Random Forest porque es excelente aprendiendo umbrales no-lineales
    # Y metemos un StandardScaler para normalizar los datos en un solo "Tubo" (Pipeline)
    modelo = make_pipeline(
        StandardScaler(),
        RandomForestClassifier(n_estimators=100, random_state=42, max_depth=8, class_weight='balanced')
    )
    
    # ¡Aquí ocurre la magia del aprendizaje!
    modelo.fit(X_train, y_train)
    
    # Evaluar el modelo
    print("\nEvaluando la Inteligencia de la IA con datos que nunca ha visto (20% del examen)...")
    y_pred = modelo.predict(X_test)
    
    accuracy = accuracy_score(y_test, y_pred)
    print(f"\n---> PRECISIÓN OBTENIDA (Accuracy): {accuracy * 100:.2f}% <---")
    
    print("\nMatriz de Confusión (En qué se equivocó):")
    print(confusion_matrix(y_test, y_pred))
    
    print("\nReporte de Clasificación Detallado:")
    print(classification_report(y_test, y_pred, target_names=['Despierto', 'Somnoliento']))
    
    # Guardar el "cerebro" entrenado en un archivo
    os.makedirs(model_dir, exist_ok=True)
    with open(model_path, 'wb') as f:
        pickle.dump(modelo, f)
        
    print("\n==================================================")
    print("¡ENTRENAMIENTO FINALIZADO CON ÉXITO!")
    print("==================================================")
    print(f"El 'Cerebro' de la IA ha sido guardado en: {model_path}")
    print("Ya podemos pasar al Paso 3: Integrarlo en el Dashboard (main.py).")

if __name__ == "__main__":
    entrenar_modelo()
