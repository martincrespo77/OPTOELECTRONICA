"""
Generador del diagrama de circuito del Nodo RX (FSO Sun Tracker)
Salida: docs/circuito_rx.png
Usa matplotlib con símbolos electrónicos estándar IEEE/IEC.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import os

# ══════════════════════════════════════════════════════════════
# PRIMITIVAS DE DIBUJO
# ══════════════════════════════════════════════════════════════

LW = 1.6   # grosor de línea principal


def wire(ax, x1, y1, x2, y2):
    ax.plot([x1, x2], [y1, y2], color='black', lw=LW, solid_capstyle='round')


def dot(ax, x, y, r=0.07):
    ax.add_patch(plt.Circle((x, y), r, color='black'))


def gnd(ax, x, y):
    """Símbolo de tierra (tres líneas horizontales decrecientes)."""
    for i, w in enumerate([0.30, 0.20, 0.10]):
        yi = y - i * 0.18
        ax.plot([x - w, x + w], [yi, yi], color='black', lw=LW)


def vdd_label(ax, x, y, label, color='#cc0000'):
    """Símbolo de alimentación: triángulo + texto."""
    tri_h = 0.28
    triangle = plt.Polygon(
        [[x, y + tri_h], [x - 0.20, y], [x + 0.20, y]],
        closed=True, facecolor=color, edgecolor=color, lw=1.2, alpha=0.85,
    )
    ax.add_patch(triangle)
    ax.text(x, y + tri_h + 0.12, label,
            ha='center', va='bottom', fontsize=8.5,
            color=color, fontweight='bold', multialignment='center')


def resistor_h(ax, x1, y, x2, label='', lbl_offset=0.28):
    """Resistor horizontal (zigzag IEEE)."""
    n = 8
    body_frac = 0.60
    lx = x2 - x1
    bstart = x1 + lx * (1 - body_frac) / 2
    bend   = x2 - lx * (1 - body_frac) / 2
    blen   = bend - bstart
    seg    = blen / n
    h      = 0.14
    wire(ax, x1, y, bstart, y)
    wire(ax, bend, y, x2, y)
    xs = [bstart]
    ys = [y]
    for i in range(n):
        xs.append(bstart + seg * (i + 0.5))
        ys.append(y + h * (1 if i % 2 == 0 else -1))
        xs.append(bstart + seg * (i + 1))
        ys.append(y)
    ax.plot(xs, ys, color='black', lw=LW)
    if label:
        ax.text((x1 + x2) / 2, y + lbl_offset, label,
                ha='center', va='bottom', fontsize=7.5)


def resistor_v(ax, x, y1, y2, label='', lbl_offset=0.32):
    """Resistor vertical (zigzag IEEE)."""
    n = 8
    body_frac = 0.60
    ly     = y2 - y1
    bstart = y1 + ly * (1 - body_frac) / 2
    bend   = y2 - ly * (1 - body_frac) / 2
    blen   = bend - bstart
    seg    = blen / n
    h      = 0.14
    wire(ax, x, y1, x, bstart)
    wire(ax, x, bend, x, y2)
    xs = [x]
    ys = [bstart]
    for i in range(n):
        xs.append(x + h * (1 if i % 2 == 0 else -1))
        ys.append(bstart + seg * (i + 0.5))
        xs.append(x)
        ys.append(bstart + seg * (i + 1))
    ax.plot(xs, ys, color='black', lw=LW)
    if label:
        ax.text(x + lbl_offset, (y1 + y2) / 2, label,
                ha='left', va='center', fontsize=7.5)


def ldr_v(ax, x, y1, y2, label='LDR'):
    """LDR vertical: zigzag + flechas de luz oblicuas."""
    resistor_v(ax, x, y1, y2)
    my = (y1 + y2) / 2
    for dy in [-0.20, 0.20]:
        ax.annotate('',
            xy=(x + 0.55, my + dy + 0.38),
            xytext=(x + 0.30, my + dy + 0.08),
            arrowprops=dict(arrowstyle='->', color='#dd8800', lw=1.3),
        )
    if label:
        ax.text(x - 0.32, (y1 + y2) / 2, label,
                ha='right', va='center', fontsize=7.5)


def led_h(ax, x1, y, x2, label='', led_color='#ff4444'):
    """LED horizontal: triángulo + barra + flechas de luz."""
    mid = (x1 + x2) / 2
    h   = 0.22
    wire(ax, x1, y, mid - h, y)
    wire(ax, mid + h, y, x2, y)
    tri = plt.Polygon(
        [[mid - h, y - h], [mid - h, y + h], [mid + h, y]],
        closed=True, facecolor=led_color, edgecolor='black', lw=1.4, alpha=0.60,
    )
    ax.add_patch(tri)
    # Barra del cátodo
    ax.plot([mid + h, mid + h], [y - h * 1.1, y + h * 1.1],
            color='black', lw=2.2)
    # Flechas de emisión
    for dx in [0.06, 0.20]:
        ax.annotate('',
            xy=(mid + dx + 0.26, y + h + 0.28),
            xytext=(mid + dx + 0.04, y + h + 0.04),
            arrowprops=dict(arrowstyle='->', color=led_color, lw=1.2),
        )
    if label:
        ax.text((x1 + x2) / 2, y - h - 0.22, label,
                ha='center', va='top', fontsize=7.8,
                color=led_color, fontweight='bold')


def switch_h(ax, x1, y, x2, label=''):
    """Pulsador NA horizontal."""
    gap = (x2 - x1) * 0.38
    mid = (x1 + x2) / 2
    wire(ax, x1, y, mid - gap / 2, y)
    wire(ax, mid + gap / 2, y, x2, y)
    ax.plot(mid - gap / 2, y, 'o', color='black', ms=4.5)
    ax.plot(mid + gap / 2, y, 'o', color='black', ms=4.5)
    ax.plot([mid - gap / 2, mid + gap / 2 - 0.08],
            [y, y + 0.24], color='black', lw=LW)
    if label:
        ax.text((x1 + x2) / 2, y + 0.40, label,
                ha='center', va='bottom', fontsize=8.0, multialignment='center')


def usb_connector(ax, cx, cy):
    """Símbolo simplificado de conector USB."""
    w, h = 0.55, 0.42
    trap = plt.Polygon(
        [[cx - w/2, cy - h/2], [cx + w/2, cy - h/2],
         [cx + w/2 - 0.08, cy + h/2], [cx - w/2 + 0.08, cy + h/2]],
        closed=True, facecolor='#ddeeff', edgecolor='#334466', lw=1.6,
    )
    ax.add_patch(trap)
    ax.text(cx, cy, 'USB', ha='center', va='center',
            fontsize=7.0, fontweight='bold', color='#223366')


def ic_box(ax, x, y, w, h, label, pins_left, pins_right):
    """
    Dibuja caja del CI + pines.
    Retorna dict {nombre_pin: (x_extremo, y)}
    """
    rect = mpatches.FancyBboxPatch(
        (x, y), w, h, boxstyle='round,pad=0.06',
        facecolor='#eeeeff', edgecolor='#222244', lw=2.4,
    )
    ax.add_patch(rect)
    ax.text(x + w / 2, y + h / 2, label,
            ha='center', va='center', fontsize=11.5,
            fontweight='bold', color='#111133', multialignment='center')

    pin_len = 0.50
    positions = {}

    for pname, py in pins_left:
        px = x
        ax.plot([px - pin_len, px], [py, py], color='black', lw=LW)
        ax.text(px + 0.14, py, pname,
                ha='left', va='center', fontsize=8.2, color='#222244')
        positions[pname] = (px - pin_len, py)

    for pname, py in pins_right:
        px = x + w
        ax.plot([px, px + pin_len], [py, py], color='black', lw=LW)
        ax.text(px - 0.14, py, pname,
                ha='right', va='center', fontsize=8.2, color='#222244')
        positions[pname] = (px + pin_len, py)

    return positions


# ══════════════════════════════════════════════════════════════
# CANAL LED (helper)
# ══════════════════════════════════════════════════════════════

def draw_led_channel(ax, x_pin, y_pin, r_label, led_label, led_color):
    """pin → R220 → LED → GND (horizontal, a la derecha)."""
    total = 4.8
    r_end   = x_pin + total * 0.33
    led_end = x_pin + total * 0.76
    gnd_x   = x_pin + total

    resistor_h(ax, x_pin, y_pin, r_end,   label=r_label,   lbl_offset=0.26)
    led_h(     ax, r_end,  y_pin, led_end, label=led_label, led_color=led_color)
    wire(      ax, led_end, y_pin, gnd_x,  y_pin)
    gnd(       ax, gnd_x,   y_pin)


# ══════════════════════════════════════════════════════════════
# DIAGRAMA PRINCIPAL
# ══════════════════════════════════════════════════════════════

def draw_rx_circuit(out_path):
    fig, ax = plt.subplots(figsize=(22, 15))
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_xlim(0, 22)
    ax.set_ylim(0, 15)
    fig.patch.set_facecolor('white')

    # ── Marco de documento técnico ────────────────────────────
    ax.add_patch(mpatches.Rectangle(
        (0.15, 0.15), 21.70, 14.70,
        fill=False, edgecolor='#333355', lw=2.5,
    ))

    # ── Cajetín de título ─────────────────────────────────────
    ax.add_patch(mpatches.Rectangle(
        (12.2, 0.15), 9.75, 2.55,
        fill=True, facecolor='#f0f0f8', edgecolor='#333355', lw=1.5,
    ))
    ax.text(17.08, 2.38, 'NODO RX — CIRCUITO ELECTRÓNICO',
            ha='center', va='top', fontsize=10.5,
            fontweight='bold', color='#111133')
    ax.text(17.08, 1.92, 'Sistema FSO Sun Tracker · Optoelectrónica',
            ha='center', va='top', fontsize=8.5, color='#333355')
    ax.text(17.08, 1.50, 'ESP32 WROOM-32 · Decodificador Manchester · Dashboard WiFi',
            ha='center', va='top', fontsize=7.5, color='#555577')
    ax.text(17.08, 1.08, 'GPIO34=ADC  GPIO14=SW  GPIO25=R  GPIO26=G  GPIO27=B',
            ha='center', va='top', fontsize=7.0, color='#666688', family='monospace')
    ax.text(17.08, 0.62, 'TD2 · FIE · UNER  —  Rev 1.0',
            ha='center', va='top', fontsize=7.5, color='#777799')

    # ── IC ESP32 ──────────────────────────────────────────────
    IC_X = 7.8
    IC_Y = 3.6
    IC_W = 5.2
    IC_H = 9.2

    vin_y  = IC_Y + IC_H - 1.0
    gnd_y  = IC_Y + IC_H - 2.3
    v33_y  = IC_Y + IC_H - 3.6
    adc_y  = IC_Y + IC_H - 5.1

    sw_y   = IC_Y + IC_H - 1.0
    r_y    = IC_Y + IC_H - 2.6
    g_y    = IC_Y + IC_H - 4.1
    b_y    = IC_Y + IC_H - 5.6

    pins_left  = [('VIN',    vin_y),
                  ('GND',    gnd_y),
                  ('3V3',    v33_y),
                  ('GPIO34', adc_y)]

    pins_right = [('GPIO14', sw_y),
                  ('GPIO25', r_y),
                  ('GPIO26', g_y),
                  ('GPIO27', b_y)]

    pp = ic_box(ax, IC_X, IC_Y, IC_W, IC_H,
                'ESP32\nWROOM-32', pins_left, pins_right)

    # ── VIN ← USB 5 V ─────────────────────────────────────────
    vx, vy = pp['VIN']
    usb_x  = vx - 2.2
    wire(ax, vx, vy, usb_x + 0.30, vy)
    usb_connector(ax, usb_x, vy)
    vdd_label(ax, usb_x, vy + 0.26, '5 V\n(USB)', color='#cc2200')

    # ── GND del IC ────────────────────────────────────────────
    gx, gy = pp['GND']
    wire(ax, gx, gy, gx - 0.7, gy)
    gnd(ax, gx - 0.7, gy)

    # ── 3V3 rail ──────────────────────────────────────────────
    vx3, vy3 = pp['3V3']
    wire(ax, vx3, vy3, vx3 - 1.0, vy3)
    vdd_label(ax, vx3 - 1.0, vy3, '3.3 V', color='#0055cc')

    # ── GPIO34 ← divisor LDR / R10k ───────────────────────────
    adcx, adcy = pp['GPIO34']
    node_x = adcx - 2.0
    node_y = adcy

    wire(ax, adcx, adcy, node_x, adcy)
    dot(ax, node_x, node_y)

    # LDR arriba: 3.3V → nodo
    ldr_top = node_y + 3.0
    wire(ax, node_x, ldr_top, node_x, ldr_top + 0.05)
    vdd_label(ax, node_x, ldr_top + 0.05, '3.3 V', color='#0055cc')
    ldr_v(ax, node_x, node_y, ldr_top, label='LDR\nGL5528')

    # R10k abajo: nodo → GND
    r_bot = node_y - 2.6
    resistor_v(ax, node_x, r_bot, node_y, label='R5 10 kΩ')
    gnd(ax, node_x, r_bot)

    # Etiqueta nodo ADC
    ax.text(node_x + 0.14, node_y - 0.06, 'V_ADC',
            ha='left', va='top', fontsize=7.0,
            color='#666600', style='italic')

    # ── GPIO14 → SW2 → GND ────────────────────────────────────
    swx, swy = pp['GPIO14']
    switch_h(ax, swx, swy, swx + 2.2, label='SW2\n(ALIGN)')
    wire(ax, swx + 2.2, swy, swx + 3.2, swy)
    gnd(ax, swx + 3.2, swy)

    # ── GPIO25/26/27 → R220 → LED (R/G/B) → GND ─────────────
    draw_led_channel(ax, pp['GPIO25'][0], pp['GPIO25'][1],
                     'R6  220 Ω', 'LED\nROJO',  '#dd2222')
    draw_led_channel(ax, pp['GPIO26'][0], pp['GPIO26'][1],
                     'R7  220 Ω', 'LED\nVERDE', '#22aa22')
    draw_led_channel(ax, pp['GPIO27'][0], pp['GPIO27'][1],
                     'R8  220 Ω', 'LED\nAZUL',  '#2255ee')

    # ── Cuadro: Modos LED ─────────────────────────────────────
    ax.add_patch(mpatches.Rectangle(
        (0.30, 6.00), 4.20, 3.80,
        fill=True, facecolor='#fafafa', edgecolor='#9999bb', lw=1.2,
    ))
    ax.text(2.40, 9.50, 'MODOS LED RGB',
            ha='center', va='bottom', fontsize=9.0,
            fontweight='bold', color='#333355')
    modos = [
        ('#22aa22', 'VERDE',    'Trama válida (quality ≥ 70 %)'),
        ('#dd2222', 'ROJO',     'Sin trama > 45 s (timeout)'),
        ('#ddaa00', 'AMARILLO', 'Recibiendo, quality < 70 %'),
        ('#2255ee', 'AZUL',     'Modo alineación (láser detec.)'),
    ]
    for i, (c, name, desc) in enumerate(modos):
        yi = 9.10 - i * 0.82
        ax.add_patch(plt.Circle((0.68, yi), 0.16, color=c))
        ax.text(1.00, yi + 0.05, name, ha='left', va='center',
                fontsize=7.5, color=c, fontweight='bold')
        ax.text(1.00, yi - 0.18, desc, ha='left', va='center',
                fontsize=7.0, color='#333344')

    # ── Cuadro: Notas ─────────────────────────────────────────
    ax.add_patch(mpatches.Rectangle(
        (0.30, 0.28), 11.75, 2.30,
        fill=True, facecolor='#fafafa', edgecolor='#9999bb', lw=1.2,
    ))
    ax.text(6.18, 2.30, 'NOTAS TÉCNICAS',
            ha='center', va='bottom', fontsize=8.5,
            fontweight='bold', color='#333355')
    notas = [
        '① ADC: GPIO34 · res. 12 bits · atenuación ADC_11dB (rango 0–3.9 V)',
        '② Histéresis: umbral_alto = 3800  /  umbral_bajo = 3200',
        '③ SW2 usa INPUT_PULLUP interno — sin resistor externo',
        '④ LED RGB cátodo común: cátodo a GND; ánodos a GPIO 25/26/27',
        '⑤ ESP32 alimentado por USB 5 V en VIN; 3.3 V generado internamente',
    ]
    for i, nota in enumerate(notas):
        ax.text(0.55, 2.00 - i * 0.34, nota,
                ha='left', va='top', fontsize=7.3, color='#333344')

    # ── Cuadro: descripción LDR ───────────────────────────────
    ax.add_patch(mpatches.Rectangle(
        (0.30, 9.90), 4.20, 2.80,
        fill=True, facecolor='#fffff8', edgecolor='#9999bb', lw=1.2,
    ))
    ax.text(2.40, 12.42, 'DIVISOR LDR / R10 kΩ',
            ha='center', va='bottom', fontsize=9.0,
            fontweight='bold', color='#333355')
    ax.text(2.40, 12.05,
            r'$V_{ADC} = \frac{R_{5}}{R_{LDR}+R_{5}} \cdot 3{,}3\ \mathrm{V}$',
            ha='center', va='top', fontsize=10.5, color='#111133')
    ax.text(2.40, 11.35,
            'R₅ = 10 kΩ  ·  LDR GL5528',
            ha='center', va='top', fontsize=7.5, color='#444455')
    ax.text(2.40, 10.98,
            'Luz intensa → R_LDR↓ → V_ADC↑',
            ha='center', va='top', fontsize=7.5, color='#444455')
    ax.text(2.40, 10.60,
            'Poll ADC 1 ms (FreeRTOS core 1)',
            ha='center', va='top', fontsize=7.5, color='#444455')

    # ── Guardado ──────────────────────────────────────────────
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    fig.savefig(out_path, dpi=180, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close(fig)
    print(f"OK → {out_path}")


if __name__ == '__main__':
    base = os.path.dirname(os.path.abspath(__file__))
    draw_rx_circuit(os.path.join(base, 'docs', 'circuito_rx.png'))
