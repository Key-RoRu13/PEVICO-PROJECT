# Guía de Ensamblaje Físico y Conexión de Hardware Seguro - PEVICO

Esta guía detalla los pasos para ensamblar el circuito físico del sistema de seguridad del conductor PEVICO utilizando un microcontrolador **Arduino UNO**, LEDs, un Buzzer y módulos de Relé para actuar sobre el freno y las luces intermitentes, **poniendo especial énfasis en la seguridad eléctrica para proteger tu ordenador y el microcontrolador.**

---

## ⚠️ CRÍTICO: Reglas de Seguridad Eléctrica (Evita dañar tu PC y Arduino)

Cuando trabajas con actuadores físicos como relés, motores o luces potentes, existe el riesgo de que corrientes inducidas (ruido eléctrico o picos de voltaje) viajen de regreso por el cable USB y dañen el puerto USB de tu computadora o quemen el Arduino. Sigue estas reglas estrictas:

1. **Nunca alimentes motores, solenoides o luces externas directamente del pin de 5V del Arduino.**
   * El pin de 5V del Arduino (y el puerto USB de la PC) solo pueden entregar un máximo de **500 mA**. 
   * Si conectas un motor o una tira de luces de alta potencia directamente al Arduino, intentarás extraer más corriente de la permitida, lo que podría quemar el puerto USB de tu computadora.
2. **Utiliza una Fuente de Alimentación Externa para la Carga:**
   * El Arduino debe encargarse únicamente de enviar la señal de control lógica (bajos miliamperios).
   * La carga real (por ejemplo, un motor de 12V que simule el freno o bombillas potentes) debe alimentarse mediante una fuente externa (batería, cargador de pared, etc.) independiente del circuito del Arduino.
3. **Usa Módulos de Relé Optoacoplados (Recomendado):**
   * Busca módulos de relé que incluyan un chip negro pequeño (optoacoplador). Este chip aísla ópticamente la parte lógica (Arduino) de la parte de potencia (bobina del relé).
   * Si el módulo tiene un jumper (puente plástico) marcado como `RY-VCC` y `VCC`, puedes retirar el puente y alimentar la bobina del relé con una fuente externa de 5V para lograr un **aislamiento eléctrico total** del Arduino.
4. **Instala un Diodo Flyback en Motores/Solenoides (Cargas Inductivas):**
   * Si conectas un motor DC o un actuador solenoide a la salida del relé, debes colocar un diodo (por ejemplo, un `1N4007`) en paralelo con la carga (con la franja del diodo apuntando al lado positivo). Esto absorbe los picos de voltaje destructivos (fuerza contraelectromotriz) que se generan cuando el relé se apaga.
5. **Verifica siempre antes de conectar el USB:**
   * Asegúrate de que no haya cables sueltos haciendo cortocircuito entre las líneas de positivo (`5V`) y tierra (`GND`).

---

## 1. Componentes Necesarios

| Cantidad | Componente | Función |
| :---: | :--- | :--- |
| 1 | Placa Arduino UNO | Cerebro del sistema de actuación física. |
| 1 | LED Verde | Indicador visual de estado seguro (SAFE). |
| 1 | LED Amarillo | Indicador visual de advertencia/distracción (WARNING). |
| 1 | LED Rojo | Indicador visual de alerta crítica/sueño (EMERGENCY). |
| 3 | Resistencias de 220 $\Omega$ | Limitadoras de corriente para proteger los LEDs. |
| 1 | Zumbador (Buzzer Activo) | Emisor de tonos y sirenas acústicas de advertencia. |
| 2 | Módulo Relé de 5V de 1 canal | Interruptores electrónicos para activar el freno y las luces. |
| 1 | Protoboard | Placa de pruebas para realizar el cableado de forma rápida. |
| - | Cables de conexión (Jumpers) | Conexión física entre componentes (Macho-Macho / Macho-Hembra). |
| 1 | Cable USB tipo A-B | Conexión física y de datos entre la laptop y el Arduino. |
| 1 | Fuente de poder externa (ej. batería de 9V o 12V) | Para alimentar los actuadores de simulación en las salidas de los relés. |

---

## 2. Esquema de Conexiones (Pinout)

Realiza las conexiones en la protoboard siguiendo esta distribución de pines del Arduino UNO:

| Componente | Pin en Arduino | Pin en Componente | Notas |
| :--- | :---: | :---: | :--- |
| **LED Verde** | `D2` | Ánodo (pata larga) | Conectar cátodo (pata corta) a GND mediante R de 220 $\Omega$. |
| **LED Amarillo** | `D3` | Ánodo (pata larga) | Conectar cátodo (pata corta) a GND mediante R de 220 $\Omega$. |
| **LED Rojo** | `D4` | Ánodo (pata larga) | Conectar cátodo (pata corta) a GND mediante R de 220 $\Omega$. |
| **Buzzer** | `D5` | Terminal Positivo (+) | Terminal Negativo (-) directo al pin `GND` de Arduino. |
| **Relé de Freno** | `D6` | Entrada de Señal (`IN`/`SIG`) | Conectar `VCC` a `5V` y `GND` a `GND` de Arduino. |
| **Relé de Luces** | `D7` | Entrada de Señal (`IN`/`SIG`) | Conectar `VCC` a `5V` y `GND` a `GND` de Arduino. |
| **Tierra Común** | `GND` | Línea de Tierra (-) | Conectar al canal negativo principal de la protoboard. |
| **Alimentación** | `5V` | Línea de Corriente (+) | Conectar al canal positivo principal de la protoboard. |

---

## 3. Conexión de los Módulos de Relé paso a paso

Un módulo de relé tiene dos secciones claramente diferenciadas: la entrada (lado de bajo voltaje / control lógica) y la salida (lado de alto voltaje / potencia de carga).

```mermaid
graph TD
    subgraph Lado de Control (Arduino)
        A[Arduino Pin D6/D7] -->|Señal lógica| B[Pin IN del Relé]
        C[Arduino 5V] -->|Alimentación lógica| D[Pin VCC del Relé]
        E[Arduino GND] -->|Tierra común| F[Pin GND del Relé]
    end
    
    subgraph Lado de Potencia (Aislado)
        G[Fuente Externa +] --> H[Borna Central COM del Relé]
        I[Borna NO Normalmente Abierto] --> J[Carga: Motor / Foco]
        J --> K[Fuente Externa -]
    end
```

### Paso A: Lado del Control (Conexión al Arduino)
Los pines de entrada del módulo de relé suelen estar etiquetados como `VCC`, `GND` e `IN` (o `IN1`/`IN2`).
1. Conecta el pin **`GND`** del módulo de relé a la línea negativa de la protoboard (tierra común de Arduino).
2. Conecta el pin **`VCC`** del módulo de relé al pin **`5V`** del Arduino. (Esto energiza los circuitos lógicos internos del módulo).
3. Conecta el pin **`IN`** del Relé de Freno al pin **`D6`** del Arduino.
4. Conecta el pin **`IN`** del Relé de Luces al pin **`D7`** del Arduino.

### Paso B: Lado de Salida y Potencia (Conexión a la Carga Externa)
El lado opuesto del relé consta de una borna con 3 terminales de tornillo:
* **`COM`** (Común): Entrada de la corriente que se va a distribuir.
* **`NO`** (Normalmente Abierto): No pasa corriente hasta que el Arduino lo activa. **(Esta es la terminal que utilizaremos)**.
* **`NC`** (Normalmente Cerrado): Siempre pasa corriente hasta que el Arduino lo activa (abre el circuito).

Para conectar de forma segura una carga simulada (como un motor DC de 12V para el freno o una tira LED externa de 12V):
1. Toma el cable **positivo** de tu fuente de alimentación externa (ej. una batería de 9V o 12V, **nunca** el pin de 5V de Arduino) y conéctalo al tornillo **`COM`** del relé.
2. Conecta un cable desde la terminal **`NO`** (Normalmente Abierto) del relé al cable positivo del motor/carga externa.
3. Conecta el cable **negativo** del motor/carga externa de regreso directamente al polo **negativo** de tu fuente de alimentación externa.
4. **¡Importante!** Si es un motor o bobina magnética, suelda o atornilla un diodo rectificador **1N4007** en paralelo con los dos terminales del motor. El lado con la franja plateada debe ir conectado al terminal positivo del motor.

---

## 4. Instrucciones Finales de Puesta en Marcha

1. **Ensamblaje final en frío:** Realiza todo el cableado con el cable USB del Arduino desconectado de tu computadora.
2. **Revisión visual:** Asegúrate de que los cables pelados no estén haciendo contacto físico directo.
3. **Conexión de datos:** Enchufa el cable USB al Arduino y a la computadora.
4. **Carga el Sketch:** Sube el código corregido [arduino_buzzer_leds.ino](file:///c:/Users/keyba/OneDrive/Documentos/PEVICO-PROJECT/arduino/arduino_buzzer_leds/arduino_buzzer_leds.ino).
5. **Conexión de potencia externa:** Una vez que el programa se ha subido correctamente, conecta la fuente de alimentación externa (batería) a tus motores/cargas.
6. **Activa el sistema en Python:** Cambia `SERIAL_ENABLED = True` en tu archivo [config.py](file:///c:/Users/keyba/OneDrive/Documentos/PEVICO-PROJECT/config.py) y corre la aplicación principal. 

¡De esta manera, el relé actuará de puente seguro y tu computadora y tu Arduino estarán 100% protegidos contra cortocircuitos o picos inductivos!
