import cv2
import sys
import time

def test_ip_webcam(url):
    print(f"Intentando conectar a: {url} ...")
    print("Por favor, asegúrate de que el celular tenga IP Webcam encendido en 'Start Server'.")
    
    # Intentar abrir la cámara
    cap = cv2.VideoCapture(url)
    
    # Tiempo de espera para que el buffer de red se llene
    time.sleep(2)
    
    if not cap.isOpened():
        print("❌ ERROR CRÍTICO: Python no puede conectarse a la cámara.")
        print("Posibles causas:")
        print("1. La IP es incorrecta o falta el /video")
        print("2. La laptop y el celular NO ESTÁN en la misma red WiFi.")
        print("3. La red tiene bloqueo de seguridad (Aislamiento de clientes). Solución: Usa el Hotspot del celular.")
        sys.exit(1)
        
    print("✅ ¡Conexión establecida! Leyendo el primer fotograma...")
    
    # Intentar leer un fotograma
    ret, frame = cap.read()
    
    if not ret or frame is None:
        print("❌ ERROR: Se conectó, pero el video está vacío o corrupto (pantalla negra).")
        sys.exit(1)
        
    print(f"✅ ¡Fotograma leído con éxito! Resolución: {frame.shape[1]}x{frame.shape[0]}")
    print("Mostrando video de prueba. Presiona la tecla 'q' en el teclado para salir.")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("❌ Se cortó la conexión.")
            break
            
        cv2.imshow("Prueba de IP Webcam (Presiona Q para salir)", frame)
        
        # Salir si se presiona la tecla 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
            
    cap.release()
    cv2.destroyAllWindows()
    print("Prueba finalizada.")

if __name__ == "__main__":
    # Lee la configuración de tu archivo actual para probar lo mismo que prueba tu app
    import config
    url_camara = config.CAMERA_INDEX
    
    if isinstance(url_camara, int):
        print(f"ADVERTENCIA: Tu config.py dice {url_camara} (que es USB).")
        print("Cámbialo al enlace de IP Webcam (ej. 'http://192.168.1.5:8080/video') y vuelve a intentar.")
    else:
        test_ip_webcam(url_camara)
