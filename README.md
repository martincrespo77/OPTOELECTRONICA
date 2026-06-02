# Comunicacion laser FSO con ESP32

Proyecto de practica para validar comunicacion optica por laser entre dos ESP32. El
objetivo de esta etapa es probar el enlace fisico y transportar telemetria solar
simulada, tomada del trabajo de Tecnicas Digitales 2, sin duplicar el proyecto TD2
completo dentro de este repositorio.

El repositorio actual contiene solamente el firmware PlatformIO necesario para la
practica de comunicacion laser:

- `src/main_tx.cpp`: nodo transmisor. Genera telemetria simulada y la envia por
  GPIO17 usando codificacion Manchester.
- `src/main_rx.cpp`: nodo receptor. Lee el haz con un LDR en ADC GPIO34, decodifica
  Manchester, valida CRC32 y publica un dashboard web en modo AP.
- `platformio.ini`: entornos de compilacion y carga para TX y RX.
- `docs/`: documentacion tecnica vigente del enlace.

La documentacion vieja basada en MicroPython, JSON por UART y pruebas cableadas de
1200 baudios queda obsoleta para esta practica. Si se necesita como antecedente, se
mantiene fuera del repo activo en el respaldo local creado durante la migracion.

## Estado actual

- Enlace: laser/FSO entre ESP32.
- Codificacion fisica: Manchester a 20 bps.
- Periodo de envio automatico: 20 s.
- Trama: preambulo, byte de sincronismo, longitud, payload binario y CRC32.
- Telemetria: datos simulados de panel solar/tracker (`F0..F3`, error de azimut,
  error de elevacion, motores, tension, corriente y potencia).
- RX: dashboard web local desde el AP `FSO-RX`.

## Hardware usado

### Nodo TX

- ESP32 DOIT DevKit V1.
- Salida laser en GPIO17.
- Pulsador en GPIO4 con `INPUT_PULLUP`.

Modos:

- Normal: envia una trama cada 20 s.
- Apuntado: laser fijo encendido para alinear el haz.

### Nodo RX

- ESP32 DevKit/WROOM.
- LDR o detector optico conectado al ADC GPIO34.
- Pulsador en GPIO14 con `INPUT_PULLUP`.
- LEDs de estado:
  - Rojo: GPIO25.
  - Verde: GPIO26.
  - Azul: GPIO27.

Modos:

- Normal: decodifica tramas y muestra estado del enlace.
- Direccionamiento: usa el LED azul para indicar incidencia del haz sobre el LDR.

## Compilacion y carga

Instalar PlatformIO. Luego, desde la raiz del repo:

```powershell
pio run -e tx
pio run -e rx
```

Para cargar firmware:

```powershell
pio run -e tx -t upload
pio run -e rx -t upload
```

Los puertos configurados actualmente en `platformio.ini` son:

- TX: `COM4`.
- RX: `COM5`.

Si Windows asigna otros puertos, actualizar `upload_port` y `monitor_port`.

## Dashboard RX

El RX levanta un punto de acceso WiFi:

- SSID: `FSO-RX`.
- Password: `fso12345`.
- IP: `192.168.4.1`.

Despues de conectarse al AP, abrir:

```text
http://192.168.4.1/
```

API de estado:

```text
http://192.168.4.1/api/state
```

## Documentacion tecnica

- [Contrato de trama](docs/CONTRATO_TRAMA.md)
- [Plan de pruebas](docs/PRUEBAS.md)
- [Arquitectura](docs/ARQUITECTURA.md)

## Relacion con Tecnicas Digitales 2

Este repo no debe mezclar todo el proyecto de Tecnicas Digitales 2. Solo toma el
modelo de telemetria solar necesario para probar el enlace:

- cuatro lecturas `F0..F3`;
- errores `errAz` y `errEl`;
- estados de motores `motAz` y `motEl`;
- tension, corriente y potencia.

La regla es simple: si el archivo sirve para compilar, cargar, probar o documentar
la comunicacion laser actual, va en este repo. Si pertenece al desarrollo completo
del tracker solar o a una version anterior en MicroPython, no se duplica aca.
