# Documento tecnico - Comunicacion laser FSO con ESP32

## 1. Proposito del documento

Este documento deja trazabilidad tecnica del desarrollo realizado para la practica
de Optoelectronica. El objetivo fue construir y validar un enlace de comunicacion
por laser entre dos ESP32, usando un nodo transmisor (`TX`) y un nodo receptor
(`RX`).

El trabajo no empezo directamente con la solucion actual. Se avanzo por etapas:
primero se probo una comunicacion mas tradicional por UART con tramas JSON, luego
se identificaron sus limitaciones para el enlace optico, y finalmente se migro a
una transmision binaria con codificacion Manchester, estructura C empaquetada y
CRC32.

La idea conservadora fue avanzar de lo conocido a lo especifico:

1. Validar que los datos se pudieran generar y parsear.
2. Validar una trama con control de errores.
3. Probar el enlace fisico.
4. Corregir el protocolo cuando el medio optico mostro sus limitaciones.
5. Documentar el contrato final para que TX y RX no queden desalineados.

## 2. Punto de partida

La primera version tomo como referencia una comunicacion tipo UART entre dos
ESP32. El TX generaba telemetria relacionada con el trabajo de Tecnicas Digitales
2: sensores `F0..F3`, error de azimut, error de elevacion, estados de motores,
tension, corriente y potencia. Esa telemetria se serializaba como JSON compacto y
se protegia con CRC32.

La trama conceptual era:

```text
json_compacto|crc32\n
```

Ese enfoque sirvio para aprender y validar tres cosas:

- que el TX podia generar datos coherentes;
- que el RX podia parsear y validar una trama;
- que una secuencia incremental permitia detectar perdidas.

Pero tambien aparecio un problema de fondo: JSON es comodo para depurar, pero no
es eficiente para un enlace optico lento, sensible a alineacion, ruido y perdida
de sincronismo. En una practica de FSO conviene reducir bytes, hacer el formato
deterministico y simplificar la deteccion de errores.

## 3. Pruebas iniciales realizadas

Las pruebas se plantearon en orden, sin saltar etapas.

### 3.1 Sanity check logico

Antes de usar el laser, se valido el flujo de datos:

- generacion de telemetria;
- serializacion;
- calculo de CRC;
- recepcion;
- validacion;
- conteo de tramas correctas y erroneas.

Este paso permitio separar errores de software de errores del enlace fisico.

### 3.2 Prueba cableada tipo UART

Luego se considero una prueba por cable entre un pin TX y un pin RX. Esta etapa era
util porque permitia comprobar el contrato de trama sin depender todavia del laser,
del receptor optico ni de la luz ambiente.

La conclusion fue correcta: si una trama falla por cable, el problema no es optico;
es de protocolo, temporizacion, parseo, CRC o cableado.

### 3.3 Prueba optica inicial

Con el enlace fisico se detectaron aspectos propios del medio optico:

- la alineacion mecanica pesa tanto como el codigo;
- la luz ambiente puede saturar o mover el umbral de deteccion;
- una trama larga aumenta la probabilidad de error;
- si no hay buena recuperacion de sincronismo, el RX puede interpretar basura como
  datos validos;
- se necesita una forma simple de apuntar el laser antes de transmitir datos.

Estas observaciones justificaron los cambios posteriores.

## 4. Cambio de UART/JSON a comunicacion Manchester binaria

La version actual ya no depende de recibir caracteres por UART. El TX genera una
senal digital en GPIO17, modulada en Manchester. Esa senal conmuta el laser. El RX
no recibe por UART: mide el detector optico con el ADC en GPIO34, detecta flancos y
reconstruye bits.

El cambio fue importante por estas razones:

- Manchester incorpora transiciones frecuentes, utiles para recuperar temporizacion.
- Un formato binario reduce mucho el tamano de la trama.
- Una estructura fija evita parseo costoso y ambiguo.
- CRC32 permite descartar datos corruptos.
- Un preambulo y un byte de sincronismo ayudan al RX a reencontrar una trama.

La comunicacion actual usa:

```text
[0x55 x 4][0x7E][LEN_H][LEN_L][TelemetryData][CRC32]
```

Donde `TelemetryData` es una estructura C empaquetada de 34 bytes y el CRC32 ocupa
4 bytes adicionales. La longitud total del bloque posterior al campo `LEN` es de
38 bytes.

## 5. Cambio de JSON a `struct`

El cambio de JSON a `struct` fue una correccion necesaria, no estetica.

JSON tiene ventajas:

- es legible;
- se puede depurar facil por consola;
- permite agregar campos sin recompilar ambos extremos si se disena bien.

Pero para este caso tenia desventajas claras:

- transmite nombres de campos repetidos en cada trama;
- aumenta la longitud total;
- requiere parseo de texto;
- cualquier cambio de espacios o formato puede afectar el CRC si no se congela el
  payload exacto;
- en un enlace optico lento, cada byte extra cuesta tiempo y probabilidad de error.

La estructura final es:

```cpp
#pragma pack(push, 1)
struct TelemetryData {
  uint32_t seq;
  uint32_t ts;
  uint16_t F0;
  uint16_t F1;
  uint16_t F2;
  uint16_t F3;
  int16_t errAz;
  int16_t errEl;
  uint8_t motAz;
  uint8_t motEl;
  float vdc;
  float idc;
  float pw;
};
#pragma pack(pop)
```

La directiva `#pragma pack(push, 1)` es clave: evita bytes de relleno entre campos.
Sin eso, el tamano real podria cambiar segun compilador o arquitectura y TX/RX
podrian dejar de interpretar la trama igual.

## 6. Codigo TX actual

Archivo: `src/main_tx.cpp`.

Responsabilidades principales:

- configurar GPIO17 como salida hacia el laser;
- generar telemetria simulada;
- calcular errores `errAz` y `errEl`;
- decidir estados de motores `motAz` y `motEl`;
- calcular tension, corriente y potencia simuladas;
- empaquetar `TelemetryData`;
- calcular CRC32 sobre la estructura;
- transmitir la trama por Manchester;
- permitir modo de apuntado mediante pulsador.

Pines actuales del TX:

| Funcion | Pin |
|---------|-----|
| Laser / salida Manchester | GPIO17 |
| Pulsador modo apuntado | GPIO4 |

Temporizacion actual:

| Parametro | Valor |
|-----------|-------|
| Medio bit Manchester | 25 ms |
| Bit completo | 50 ms |
| Velocidad efectiva | 20 bps |
| Periodo automatico de trama | 20 s |

El boton del TX corrige un problema practico: para alinear un laser, no conviene
esperar tramas cada 20 segundos. En modo apuntado se deshabilita el timer y se deja
el laser fijo encendido. Al salir de ese modo, se apaga el laser, se limpia el
pendiente de transmision y se reactiva el timer.

## 7. Codigo RX actual

Archivo: `src/main_rx.cpp`.

Responsabilidades principales:

- leer el detector optico por ADC;
- aplicar histeresis con umbral alto y bajo;
- detectar flancos;
- reconstruir bits Manchester;
- buscar sincronismo;
- leer longitud y payload;
- validar tamano y CRC32;
- publicar metricas de enlace;
- mostrar dashboard web por WiFi AP;
- permitir modo direccionamiento mediante pulsador.

Pines actuales del RX:

| Funcion | Pin |
|---------|-----|
| Entrada analogica LDR/detector | GPIO34 |
| Pulsador modo direccionamiento | GPIO14 |
| LED rojo | GPIO25 |
| LED verde | GPIO26 |
| LED azul | GPIO27 |

Umbrales actuales del ADC:

| Parametro | Valor |
|-----------|-------|
| `THRESHOLD_HIGH` | 3800 |
| `THRESHOLD_LOW` | 3200 |

La histeresis evita que pequenas variaciones alrededor de un unico umbral generen
flancos falsos. Esto es importante porque el LDR y el circuito analogico no
entregan una senal digital perfecta.

El boton del RX activa el modo direccionamiento. En ese modo el LED azul indica si
el laser incide sobre el detector. Es una correccion practica: antes de evaluar CRC,
calidad o dashboard, primero hay que saber si existe acoplamiento optico real.

## 8. Correcciones realizadas durante la evolucion

### 8.1 Reduccion de tamano de trama

La migracion de JSON a `TelemetryData` redujo la cantidad de bytes transmitidos y
elimino nombres de campos repetidos. Esto mejora la robustez en un enlace lento.

### 8.2 Separacion entre contrato y visualizacion

El RX sigue publicando JSON en `/api/state`, pero ese JSON ya no es el formato del
enlace optico. Es solo una salida para el dashboard web.

La regla actual es:

- enlace optico: binario Manchester;
- dashboard/API: JSON local generado por el RX.

Esto evita confundir protocolo fisico con formato de visualizacion.

### 8.3 Sincronismo explicito

Se agrego preambulo `0x55` y sync `0x7E`. El RX busca el byte de sincronismo y no
asume que empieza leyendo justo al principio de una trama.

### 8.4 CRC32 sobre payload binario

El CRC32 se calcula sobre los bytes reales de `TelemetryData`, no sobre texto ni
sobre el preambulo. Esto deja una regla simple y repetible.

### 8.5 Control de errores

El RX mantiene contadores:

- `rx_ok`;
- `crc_err`;
- `frame_err`;
- `seq_gap`;
- `link_quality_pct`.

Estos valores permiten distinguir problemas:

- si sube `frame_err`, probablemente hay perdida de sincronismo o longitud invalida;
- si sube `crc_err`, llegan tramas con estructura plausible pero bytes corruptos;
- si sube `seq_gap`, se estan perdiendo tramas completas;
- si `rx_ok` queda en cero, primero se revisa alineacion y senal analogica.

### 8.6 Correccion de nomenclatura interna

Se elimino una referencia interna a UART en el nombre de la rutina de lectura de
tramas del RX. La funcion actual se llama `readDecodedFrames()`, porque procesa
tramas ya reconstruidas desde la decodificacion Manchester, no bytes UART.

## 9. Aplicacion actual

La aplicacion vigente es una demostracion funcional de enlace optico para
Optoelectronica:

1. El TX simula telemetria solar/tracker.
2. El TX empaqueta la informacion en estructura binaria.
3. El TX calcula CRC32.
4. El TX modula el laser por Manchester.
5. El RX detecta luz con ADC.
6. El RX reconstruye bits y trama.
7. El RX valida CRC32.
8. El RX publica datos y metricas en un dashboard local.

El dashboard se accede conectandose al AP:

```text
SSID: FSO-RX
Password: fso12345
URL: http://192.168.4.1/
```

## 10. Trazabilidad del aprendizaje

La evolucion del proyecto muestra una secuencia tecnica razonable:

| Etapa | Que se probo | Que se aprendio | Correccion aplicada |
|-------|--------------|-----------------|---------------------|
| JSON inicial | Tramas legibles con CRC | Facil de depurar, pesado para FSO | Mantener JSON solo para dashboard |
| UART/cable | Separar software de optica | Si falla cableado, no culpar al laser | Probar por capas |
| Enlace optico | Laser + receptor | La alineacion y luz ambiente dominan | Agregar modos de apuntado |
| Trama larga | Envio de muchos bytes | Mas bytes implican mas error | Pasar a `struct` |
| RX por detector | Lectura analogica | Un umbral unico es fragil | Histeresis alta/baja |
| Sincronismo | Recepcion asincronica | El RX puede empezar a mitad de trama | Preambulo + sync |
| Robustez | Tramas corruptas | El firmware no debe bloquearse | Descartar y contar errores |

## 11. Criterios para no volver a duplicar informacion

El repositorio actual debe conservar solamente:

- firmware vigente de TX y RX;
- contrato de trama vigente;
- plan de pruebas vigente;
- documentacion tecnica del proceso;
- referencias minimas a TD2 solo cuando expliquen la telemetria.

No corresponde volver a incluir:

- copias completas del proyecto TD2;
- entornos virtuales;
- firmwares MicroPython anteriores;
- PDFs duplicados si existe Markdown fuente;
- documentacion que diga que el enlace actual usa JSON por UART.

La fuente de verdad tecnica queda asi:

- Codigo TX: `src/main_tx.cpp`.
- Codigo RX: `src/main_rx.cpp`.
- Contrato de trama: `docs/CONTRATO_TRAMA.md`.
- Plan de pruebas: `docs/PRUEBAS.md`.
- Trazabilidad tecnica: este documento.

## 12. Proximos pasos recomendados

1. Registrar resultados reales de distancia, iluminacion y errores.
2. Medir valores ADC con laser apagado, luz ambiente y laser alineado.
3. Ajustar `THRESHOLD_HIGH` y `THRESHOLD_LOW` segun mediciones reales.
4. Probar encapsulado mecanico del receptor para reducir luz ambiente.
5. Si se aumenta velocidad, hacerlo de a un parametro por vez y actualizar el
   contrato de trama.
6. Si se agregan campos a `TelemetryData`, actualizar TX, RX y documentacion en el
   mismo commit.
