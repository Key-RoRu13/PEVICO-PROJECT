/**
 * PEVICO - Sistema de Actuadores Físicos (Arduino)
 * 
 * Este programa escucha las señales seriales enviadas por el script de Python:
 *   - 'S' : Estado Seguro (Enciende Led Verde, apaga bocina)
 *   - 'W' : Precaución (Enciende Led Amarillo/Azul, hace sonar bocina de forma intermitente)
 *   - 'E' : Emergencia (Enciende Led Rojo, hace sonar bocina continuamente)
 *   - 'F' o 'I' : Activa frenado de emergencia / luces intermitentes físicas
 *   - 'f' o 'i' : Libera frenado / apaga luces intermitentes
 */

// --- CONFIGURACIÓN DE PINES ---
const int PIN_LED_VERDE     = 2;  // Conducir Seguro (SAFE)
const int PIN_LED_AMARILLO  = 3;  // Precaución / Distracción (WARNING)
const int PIN_LED_ROJO      = 4;  // Sueño / Alerta Crítica (EMERGENCY)
const int PIN_BUZZER        = 5;  // Zumbador / Altavoz pequeño
const int PIN_RELE_FRENO    = 6;  // Opcional: Relevador para motor o freno
const int PIN_RELE_LUCES    = 7;  // Relevador para luces intermitentes físicas

// Variables de estado
char comando;
unsigned long ultimoParpadeo = 0;
bool estadoIntermitente = false;
String estadoActual = "SAFE";

void setup() {
  // Configurar los pines como salida
  pinMode(PIN_LED_VERDE, OUTPUT);
  pinMode(PIN_LED_AMARILLO, OUTPUT);
  pinMode(PIN_LED_ROJO, OUTPUT);
  pinMode(PIN_BUZZER, OUTPUT);
  pinMode(PIN_RELE_FRENO, OUTPUT);
  pinMode(PIN_RELE_LUCES, OUTPUT);

  // Inicializar pines en apagado
  digitalWrite(PIN_LED_VERDE, LOW);
  digitalWrite(PIN_LED_AMARILLO, LOW);
  digitalWrite(PIN_LED_ROJO, LOW);
  digitalWrite(PIN_BUZZER, LOW);
  
  // El Relé 1 (Freno) es Active-Low -> HIGH significa apagado (desactivado)
  digitalWrite(PIN_RELE_FRENO, HIGH);
  // El Relé 2 (Luces) es Active-High -> LOW significa apagado (desactivado)
  digitalWrite(PIN_RELE_LUCES, LOW);

  // Iniciar la comunicación serial a 9600 baudios (coincide con config.py)
  Serial.begin(9600);
  
  // Pequeño parpadeo inicial de prueba de LEDs para confirmar que todo sirve
  digitalWrite(PIN_LED_VERDE, HIGH);
  delay(200);
  digitalWrite(PIN_LED_AMARILLO, HIGH);
  delay(200);
  digitalWrite(PIN_LED_ROJO, HIGH);
  delay(200);
  
  // Apagar todos
  digitalWrite(PIN_LED_VERDE, LOW);
  digitalWrite(PIN_LED_AMARILLO, LOW);
  digitalWrite(PIN_LED_ROJO, LOW);
}

void loop() {
  // 1. Escuchar el puerto Serial
  if (Serial.available() > 0) {
    comando = Serial.read();

    switch (comando) {
      case 'S': // ESTADO SEGURO
        estadoActual = "SAFE";
        digitalWrite(PIN_LED_VERDE, HIGH);
        digitalWrite(PIN_LED_AMARILLO, LOW);
        digitalWrite(PIN_LED_ROJO, LOW);
        noTone(PIN_BUZZER);
        digitalWrite(PIN_BUZZER, LOW);
        
        // Apagar relés (Freno es Active-Low -> HIGH | Luces es Active-High -> LOW)
        digitalWrite(PIN_RELE_FRENO, HIGH);
        digitalWrite(PIN_RELE_LUCES, LOW);
        break;

      case 'W': // ADVERTENCIA (Bostezo / Distracción leve)
        estadoActual = "WARNING";
        digitalWrite(PIN_LED_VERDE, LOW);
        digitalWrite(PIN_LED_AMARILLO, HIGH);
        digitalWrite(PIN_LED_ROJO, LOW);
        
        // Encender relés (Freno es Active-Low -> LOW | Luces es Active-High -> HIGH)
        digitalWrite(PIN_RELE_FRENO, LOW);
        digitalWrite(PIN_RELE_LUCES, HIGH);
        break;

      case 'E': // EMERGENCIA (Microsueño / Cabeceo / Teléfono)
        estadoActual = "EMERGENCY";
        digitalWrite(PIN_LED_VERDE, LOW);
        digitalWrite(PIN_LED_AMARILLO, LOW);
        digitalWrite(PIN_LED_ROJO, HIGH);
        
        // Encender relés (Freno es Active-Low -> LOW | Luces es Active-High -> HIGH)
        digitalWrite(PIN_RELE_FRENO, LOW);
        digitalWrite(PIN_RELE_LUCES, HIGH);
        break;

      case 'F': // Control directo manual: Frenado de Emergencia activado
        digitalWrite(PIN_RELE_FRENO, LOW); 
        break;
        
      case 'f': // Control directo manual: Frenado liberado
        digitalWrite(PIN_RELE_FRENO, HIGH);
        break;

      case 'I': // Control directo manual: Luces intermitentes activadas (Active-High -> HIGH)
        digitalWrite(PIN_RELE_LUCES, HIGH);
        break;

      case 'i': // Control directo manual: Luces intermitentes desactivadas (Active-High -> LOW)
        digitalWrite(PIN_RELE_LUCES, LOW);
        break;
    }
  }

  // 2. Controlar la alarma sonora (Buzzer) según el estado
  if (estadoActual == "WARNING") {
    // Sonido intermitente (Pita cada 300 ms)
    unsigned long tiempoActual = millis();
    if (tiempoActual - ultimoParpadeo >= 300) {
      ultimoParpadeo = tiempoActual;
      estadoIntermitente = !estadoIntermitente;
      
      if (estadoIntermitente) {
        tone(PIN_BUZZER, 1000); // Tono de 1000 Hz
      } else {
        noTone(PIN_BUZZER);
      }
    }
  } 
  else if (estadoActual == "EMERGENCY") {
    // Sonido continuo y molesto para despertar al conductor
    tone(PIN_BUZZER, 2500); // Tono agudo y fuerte de 2500 Hz
  } 
  else {
    // Estado SAFE: Silencio total
    noTone(PIN_BUZZER);
  }
}
