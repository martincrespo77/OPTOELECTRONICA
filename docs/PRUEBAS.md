# Plan de pruebas

Ejecutar en orden. No avanzar al paso siguiente si el anterior falla.

## Paso 0 - Compilacion

Compilar ambos entornos:

```powershell
pio run -e tx
pio run -e rx
```

Criterio de exito:

- Compila `src/main_tx.cpp`.
- Compila `src/main_rx.cpp`.
- No hay errores de dependencias de PlatformIO.

## Paso 1 - Carga y monitor serie

Cargar ambos nodos:

```powershell
pio run -e tx -t upload
pio run -e rx -t upload
```

Abrir monitor serie:

```powershell
pio device monitor -e tx
pio device monitor -e rx
```

Criterio de exito:

- TX imprime inicio en modo binario.
- RX imprime inicio del decodificador ADC binario.
- RX levanta el AP `FSO-RX`.

## Paso 2 - Alineacion fisica

Activar modo apuntado en el TX con el pulsador de GPIO4. El laser queda fijo.

Activar modo direccionamiento en el RX con el pulsador de GPIO14. El LED azul debe
encenderse cuando el haz incide sobre el LDR.

Criterio de exito:

- El LED azul responde de forma clara al alinear/desalinear el haz.
- No hay falsos positivos fuertes con luz ambiente normal.

## Paso 3 - Comunicacion a corta distancia

Volver ambos nodos a modo normal.

Condiciones iniciales:

- Distancia: 10 cm a 30 cm.
- Haz alineado.
- Luz ambiente controlada.

Criterio de exito:

- RX incrementa `rx_ok`.
- `crc_err` y `frame_err` se mantienen bajos.
- `link_quality_pct` se acerca a 100 despues de varias tramas.
- El dashboard muestra `seq`, potencia, tension, corriente y estado.

## Paso 4 - Interrupcion del haz

Interrumpir el laser durante algunos segundos y luego liberar el haz.

Criterio de exito:

- RX deja de recibir tramas validas durante el corte.
- Pueden aumentar `crc_err` o `frame_err`.
- Al restablecer alineacion, `rx_ok` vuelve a aumentar.
- El firmware no se reinicia ni queda bloqueado.

## Paso 5 - Luz ambiente

Probar con iluminacion normal del aula o laboratorio.

Criterio de exito:

- El enlace sigue recibiendo tramas validas.
- Si aumentan errores, ajustar mecanicamente el receptor: tubo opaco, mejor
  alineacion, menor distancia o umbrales ADC.

## Registro de resultados

Anotar cada prueba con este formato:

```text
fecha:
paso:
distancia:
iluminacion:
tx_port:
rx_port:
rx_ok:
crc_err:
frame_err:
seq_gap:
link_quality_pct:
observaciones:
```

## Fallas tipicas

- `rx_ok = 0`: revisar alineacion, polaridad del laser, alimentacion y pin GPIO17.
- Muchos `crc_err`: el RX detecta flancos, pero hay ruido o tiempos inestables.
- Muchos `frame_err`: el RX pierde sincronismo o interpreta mal la longitud.
- LED azul siempre encendido: umbrales ADC demasiado bajos o saturacion por luz.
- LED azul nunca enciende: poca potencia optica, mala alineacion o divisor LDR mal
  dimensionado.
