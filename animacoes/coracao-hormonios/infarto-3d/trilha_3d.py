"""Trilha do trecho 3D (progressão para o infarto), 14,25 s.

Batimentos de 118 a 165 bpm (batidas-3d.json, exportado da camada de legendas),
bipes de monitor, tensão crescente, impacto a cada etapa e alarme na isquemia.
Uso: python3 trilha_3d.py batidas-3d.json saida.wav
"""
import json
import sys
import wave
import numpy as np

SR = 44100
dados = json.load(open(sys.argv[1]))
BATIDAS, CORTES = dados["batidas"], dados["cortes"]
DUR = CORTES[-1]
N = int(SR * DUR)
t = np.arange(N) / SR


def som(freq, inicio, dur, decai=6.0, vol=1.0, harm=0.0):
    out = np.zeros(N)
    i0 = int(inicio * SR)
    n = min(int(dur * SR), N - i0)
    if n <= 0:
        return out
    tt = np.arange(n) / SR
    s = np.sin(2 * np.pi * freq * tt) + harm * np.sin(2 * np.pi * freq * 2 * tt)
    out[i0:i0 + n] = s * np.exp(-decai * tt) * np.clip(tt / .004, 0, 1) * vol
    return out


mix = np.zeros(N)
for b in BATIDAS:
    forca = .55 + .4 * b / DUR
    mix += som(55, b, .3, 16, forca) + som(46, b + .12, .3, 18, forca * .7)
    mix += som(1046.5, b, .09, 30, .1, .2)

prog = t / DUR
tensao = sum(np.sin(2 * np.pi * f * (1 + .008 * prog * np.sin(2 * np.pi * .6 * t)) * t) for f in (73.4, 77.8, 110.0, 116.5))
riser = np.sin(2 * np.pi * np.cumsum(220 + 600 * prog ** 2) / SR)
mix += (tensao * .05 + riser * .03) * (.4 + .6 * prog)

# impacto a cada etapa (coincide com o mergulho do gráfico para o 3D), mais forte na oclusão e na isquemia
for corte, vol in zip(CORTES[0:4], (.45, .55, .7, .95)):
    mix += som(40, corte, 1.4, 2.8, vol) + som(80, corte, .4, 8, vol * .4)

# alarme hospitalar a partir da isquemia (continua no trecho seguinte)
k = CORTES[3] + .15
while k < DUR:
    mix += som(960, k, .22, 3, .16, .2) + som(770, k + .25, .22, 3, .16, .2)
    k += .5

mix *= .89 / np.max(np.abs(mix))
with wave.open(sys.argv[2], "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((mix * 32767).astype(np.int16).tobytes())
print("ok", sys.argv[2])
