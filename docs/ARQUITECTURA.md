# Arquitectura del proyecto

Este repositorio queda organizado como practica de enlace optico FSO. No es el
repositorio completo del tracker solar ni del trabajo de Tecnicas Digitales 2.

## Separacion de responsabilidades

### TX

Archivo: `src/main_tx.cpp`.

Responsabilidades:

- Generar telemetria simulada.
- Empaquetar `TelemetryData`.
- Calcular CRC32.
- Transmitir preambulo, sync, longitud y payload por Manchester.
- Permitir modo apuntado con laser fijo.

### RX

Archivo: `src/main_rx.cpp`.

Responsabilidades:

- Leer el detector optico por ADC.
- Detectar flancos mediante histeresis.
- Decodificar Manchester.
- Reconstruir tramas binarias.
- Validar longitud y CRC32.
- Publicar metricas por dashboard web.
- Permitir modo direccionamiento con LED azul.

## Flujo de datos

```text
Telemetria simulada TD2
        |
        v
TelemetryData + CRC32
        |
        v
Manchester por GPIO17
        |
        v
Laser / espacio libre
        |
        v
LDR en ADC GPIO34
        |
        v
Decodificador Manchester
        |
        v
Validacion CRC32
        |
        v
Dashboard RX
```

## Que pertenece al repo

- Firmware PlatformIO vigente.
- Documentacion del protocolo actual.
- Plan de pruebas de la practica laser.
- Datos simulados necesarios para representar el tracker solar.

## Que no pertenece al repo

- Entornos virtuales (`.venv`).
- Firmwares viejos de MicroPython.
- PDFs generados como respaldo si ya existe Markdown fuente.
- Copias completas del proyecto TD2.
- Documentacion de contratos antiguos que contradiga el protocolo actual.

## Criterio de mantenimiento

La fuente de verdad es el codigo en `src/` y la documentacion en `docs/`.
Cualquier cambio de pines, velocidad, estructura de payload o CRC debe actualizar
estos tres lugares al mismo tiempo:

- `src/main_tx.cpp`.
- `src/main_rx.cpp`.
- `docs/CONTRATO_TRAMA.md`.
