# Contrato de trama FSO binaria

Estado: vigente para la practica de comunicacion laser con ESP32 y PlatformIO.

Este contrato reemplaza la version anterior basada en JSON por UART. El firmware
actual transmite bytes binarios codificados en Manchester. Cambiar este formato sin
actualizar TX y RX al mismo tiempo rompe la comunicacion.

## Capa fisica

- Medio: haz laser/FSO.
- TX: GPIO17.
- RX: ADC GPIO34 con LDR/detector optico.
- Codificacion: Manchester.
- Velocidad efectiva configurada: 20 bps.
- Medio bit: 25 ms.
- Bit completo: 50 ms.

Mapeo Manchester usado por el TX:

| Bit logico | Primer medio bit | Segundo medio bit |
|------------|------------------|-------------------|
| `1`        | HIGH             | LOW               |
| `0`        | LOW              | HIGH              |

El RX reconstruye bits detectando flancos sobre el ADC mediante dos umbrales con
histeresis:

- `THRESHOLD_HIGH = 3800`.
- `THRESHOLD_LOW = 3200`.

## Formato de trama

```text
[0x55 x 4][0x7E][LEN_H][LEN_L][PAYLOAD + CRC32]
```

Campos:

| Campo | Tamano | Descripcion |
|-------|--------|-------------|
| Preambulo | 4 bytes | Cuatro bytes `0x55` para estabilizar la deteccion. |
| Sync | 1 byte | Byte fijo `0x7E`. |
| Longitud | 2 bytes | Longitud del bloque siguiente, big-endian. |
| Payload | 34 bytes | Estructura `TelemetryData` empaquetada. |
| CRC32 | 4 bytes | CRC32 IEEE calculado sobre `TelemetryData`. |

La longitud enviada por el TX es:

```text
sizeof(TelemetryData) + sizeof(uint32_t) = 38 bytes
```

## Payload `TelemetryData`

La estructura esta empaquetada con `#pragma pack(push, 1)`, por lo que no hay
padding entre campos.

```cpp
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
```

Tabla de campos:

| Campo | Tipo | Unidad | Descripcion |
|-------|------|--------|-------------|
| `seq` | `uint32_t` | - | Secuencia incremental desde el arranque del TX. |
| `ts` | `uint32_t` | s | Tiempo desde arranque del TX. |
| `F0`..`F3` | `uint16_t` | ADC | Lecturas simuladas de sensores del tracker solar. |
| `errAz` | `int16_t` | ADC | Error de azimut. |
| `errEl` | `int16_t` | ADC | Error de elevacion. |
| `motAz` | `uint8_t` | - | `1` si el motor de azimut deberia moverse. |
| `motEl` | `uint8_t` | - | `1` si el motor de elevacion deberia moverse. |
| `vdc` | `float` | V | Tension simulada del panel. |
| `idc` | `float` | A | Corriente simulada del panel. |
| `pw` | `float` | W | Potencia simulada. |

## CRC32

- Polinomio: `0xEDB88320`.
- Valor inicial: `0xFFFFFFFF`.
- XOR final: `~crc`.
- El CRC se calcula solamente sobre los 34 bytes de `TelemetryData`.
- El CRC se agrega al final del payload extendido como `uint32_t`.

Regla conservadora: no calcular el CRC sobre el preambulo, sync ni longitud.

## Reglas del RX

1. Buscar byte de sincronismo `0x7E`.
2. Leer dos bytes de longitud.
3. Rechazar longitudes `0` o mayores que `MAX_PAYLOAD`.
4. Acumular `LEN` bytes.
5. Verificar que `LEN == sizeof(TelemetryData) + sizeof(uint32_t)`.
6. Separar `TelemetryData` y CRC recibido.
7. Calcular CRC32 sobre `TelemetryData`.
8. Si el CRC coincide, publicar datos y actualizar metricas.
9. Si falla, incrementar `crcErr` o `frameErr` segun corresponda.

El RX no debe bloquearse por tramas invalidas. Toda trama mala se descarta y el
receptor vuelve a buscar sincronismo.
