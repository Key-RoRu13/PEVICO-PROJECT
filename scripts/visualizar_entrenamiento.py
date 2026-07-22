import os
import sys
import pandas as pd
import numpy as np

# 1. Asegurar la existencia de las librerías gráficas
try:
    import matplotlib.pyplot as plt
    import seaborn as sns
except ImportError:
    print("--------------------------------------------------")
    print("AVISO: Faltan las librerías gráficas 'matplotlib' y 'seaborn'.")
    print("Instalándolas en tu entorno virtual...")
    print("--------------------------------------------------")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "matplotlib", "seaborn"])
    import matplotlib.pyplot as plt
    import seaborn as sns

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.metrics import confusion_matrix, classification_report

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
csv_path = os.path.join(PROJECT_ROOT, "dataset_caracteristicas.csv")
report_img_path = os.path.join(PROJECT_ROOT, "assets", "reporte_entrenamiento.png")

def generar_reporte_grafico():
    print("==================================================")
    print("GENERADOR DE REPORTE Y ANÁLISIS DE DATOS (PEVICO)")
    print("==================================================")
    
    if not os.path.exists(csv_path):
        print(f"ERROR: No se encontró el archivo {csv_path}.")
        print("Ejecuta 'python scripts/1_extraer_caracteristicas.py' primero.")
        return

    # Cargar datos
    df = pd.read_csv(csv_path)
    print(f"Cargados {len(df)} registros para análisis.")
    
    # Separar características y etiquetas
    X = df[['EAR', 'MAR', 'Pitch', 'Yaw']]
    y = df['Label']
    
    # Dividir en entrenamiento y prueba
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    # Entrenar modelo rápido para análisis
    print("Entrenando clasificador Random Forest...")
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    clf = RandomForestClassifier(n_estimators=100, random_state=42, max_depth=10)
    clf.fit(X_train_scaled, y_train)
    
    y_pred = clf.predict(X_test_scaled)
    
    # Obtener matriz de confusión e importancia de características
    cm = confusion_matrix(y_test, y_pred)
    importances = clf.feature_importances_
    features = ['EAR (Ojos)', 'MAR (Boca)', 'Pitch (Cabeceo)', 'Yaw (Mirar a los lados)']
    
    # Configurar estilo de gráficos
    sns.set_theme(style="darkgrid")
    
    # Asegurar que exista el directorio assets
    assets_dir = os.path.join(PROJECT_ROOT, "assets")
    os.makedirs(assets_dir, exist_ok=True)
    
    # --------------------------------------------------
    # FIGURA 1: Matriz de Confusión
    # --------------------------------------------------
    plt.figure(figsize=(7, 6))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                xticklabels=['Despierto', 'Somnoliento'], 
                yticklabels=['Despierto', 'Somnoliento'],
                annot_kws={"size": 14, "weight": "bold"})
    plt.title('1. Matriz de Confusión (Evaluación del Modelo)', fontsize=14, fontweight='bold', pad=15)
    plt.xlabel('Predicción de la IA', fontsize=12)
    plt.ylabel('Estado Real del Conductor', fontsize=12)
    plt.tight_layout()
    path_1 = os.path.join(assets_dir, "reporte_1_confusion.png")
    plt.savefig(path_1, dpi=150)
    print(f"[REPORTE] Guardado: {path_1}")
    
    # --------------------------------------------------
    # FIGURA 2: Importancia de Características
    # --------------------------------------------------
    plt.figure(figsize=(8, 5))
    importances_df = pd.DataFrame({'Característica': features, 'Importancia': importances})
    importances_df = importances_df.sort_values(by='Importancia', ascending=False)
    
    sns.barplot(x='Importancia', y='Característica', data=importances_df, palette='viridis')
    plt.title('2. Importancia de las Características en la Decisión', fontsize=14, fontweight='bold', pad=15)
    plt.xlabel('Peso relativo en la predicción (0.0 a 1.0)', fontsize=12)
    plt.ylabel('')
    for i, v in enumerate(importances_df['Importancia']):
        plt.text(v + 0.01, i, f"{v*100:.1f}%", va='center', fontweight='bold', fontsize=11)
    plt.tight_layout()
    path_2 = os.path.join(assets_dir, "reporte_2_importancia.png")
    plt.savefig(path_2, dpi=150)
    print(f"[REPORTE] Guardado: {path_2}")
    
    # --------------------------------------------------
    # FIGURA 3: Distribución del EAR (Ojos)
    # --------------------------------------------------
    plt.figure(figsize=(8, 5))
    sns.kdeplot(data=df, x='EAR', hue='Label', fill=True, common_norm=False, palette='coolwarm', alpha=0.6)
    plt.title('3. Separación de Datos: EAR (Ojos abiertos/cerrados)', fontsize=14, fontweight='bold', pad=15)
    plt.xlabel('EAR (Eye Aspect Ratio)', fontsize=12)
    plt.ylabel('Densidad de muestras', fontsize=12)
    legend = plt.gca().get_legend()
    if legend:
        legend.set_title("Estado")
        for t, l in zip(legend.texts, ['Despierto', 'Somnoliento']):
            t.set_text(l)
    plt.tight_layout()
    path_3 = os.path.join(assets_dir, "reporte_3_ear.png")
    plt.savefig(path_3, dpi=150)
    print(f"[REPORTE] Guardado: {path_3}")
    
    # --------------------------------------------------
    # FIGURA 4: Distribución del MAR (Boca)
    # --------------------------------------------------
    plt.figure(figsize=(8, 5))
    sns.kdeplot(data=df, x='MAR', hue='Label', fill=True, common_norm=False, palette='coolwarm', alpha=0.6)
    plt.title('4. Separación de Datos: MAR (Bostezos)', fontsize=14, fontweight='bold', pad=15)
    plt.xlabel('MAR (Mouth Aspect Ratio)', fontsize=12)
    plt.ylabel('Densidad de muestras', fontsize=12)
    legend = plt.gca().get_legend()
    if legend:
        legend.set_title("Estado")
        for t, l in zip(legend.texts, ['Despierto', 'Somnoliento']):
            t.set_text(l)
    plt.tight_layout()
    path_4 = os.path.join(assets_dir, "reporte_4_mar.png")
    plt.savefig(path_4, dpi=150)
    print(f"[REPORTE] Guardado: {path_4}")
    
    # --------------------------------------------------
    # FIGURA 5: Métricas de Rendimiento y Glosario (Combinado en una sola figura de 2 columnas)
    # --------------------------------------------------
    fig, (ax_table, ax_text) = plt.subplots(1, 2, figsize=(15, 6))
    
    # Lado izquierdo: Heatmap de Métricas
    report_dict = classification_report(y_test, y_pred, target_names=['Despierto', 'Somnoliento'], output_dict=True)
    report_df = pd.DataFrame(report_dict).T
    report_df_filtered = report_df.drop(index=['accuracy'])
    
    sns.heatmap(report_df_filtered.iloc[:, :-1], annot=True, cmap='Greens', cbar=False, fmt='.3f', ax=ax_table, 
                annot_kws={"size": 13, "weight": "bold"})
    ax_table.set_title('5. Métricas: Precision, Recall, F1-Score', fontsize=13, fontweight='bold', pad=10)
    ax_table.set_xlabel('Métricas de Rendimiento', fontsize=11)
    ax_table.set_ylabel('Clases y Promedios', fontsize=11)
    
    # Lado derecho: Tarjeta de Glosario y Soporte
    ax_text.axis('off')
    total_samples = len(y_test)
    accuracy = clf.score(X_test_scaled, y_test)
    conteo_test = y_test.value_counts()
    
    texto_resumen = (
        f"RESUMEN GENERAL Y DEFINICIÓN DE MÉTRICAS\n\n"
        f"• Exactitud (Accuracy): {accuracy * 100:.2f}%\n"
        f"• Soporte Total (Muestras de Examen): {total_samples} imágenes\n"
        f"   - Soporte Despiertos: {conteo_test.get(0, 0)} imágenes\n"
        f"   - Soporte Somnolientos: {conteo_test.get(1, 0)} imágenes\n\n"
        f"¿Qué significa cada métrica?\n"
        f"1. Precision (Precisión): De todas las alertas hechas por la IA,\n"
        f"    ¿cuántas eran fatiga real? (Evita falsas alarmas).\n"
        f"2. Recall (Sensibilidad): De todas las fatigas reales del conductor,\n"
        f"    ¿cuántas logró detectar la IA? (Evita omitir un microsueño).\n"
        f"3. F1-Score: Media de balance óptimo entre Precision y Recall.\n"
        f"4. Support (Soporte): La cantidad real de imágenes evaluadas por clase."
    )
    
    ax_text.text(0.05, 0.5, texto_resumen, fontsize=10, fontweight='medium',
                 va='center', ha='left', color='#2c3e50',
                 bbox=dict(boxstyle="round,pad=1.2", facecolor='#f8f9fa', edgecolor='#27ae60', lw=2))
    ax_text.set_title('6. Soporte (Support) y Glosario Técnico', fontsize=13, fontweight='bold', pad=10)
    
    plt.tight_layout()
    path_5 = os.path.join(assets_dir, "reporte_5_metricas.png")
    plt.savefig(path_5, dpi=150)
    print(f"[REPORTE] Guardado: {path_5}")
    
    # Imprimir reporte técnico en consola
    print("\n==================================================")
    print("REPORTE DETALLADO EN TERMINAL")
    print("==================================================")
    print(classification_report(y_test, y_pred, target_names=['Despierto (0)', 'Somnoliento (1)']))
    
    # Mostrar todas las ventanas
    print("\nAbriendo todas las ventanas gráficas de forma independiente...")
    print("Cierra todas las ventanas para finalizar el script.")
    plt.show()

if __name__ == "__main__":
    generar_reporte_grafico()
