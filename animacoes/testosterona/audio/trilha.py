"""Efeitos sonoros da animação "como a testosterona envelhece" (sem música).

Tic a cada década (marcos.json, exportado da animação), subida na puberdade,
impacto no auge, tom descendo na queda, enchimento da barra e impacto final.
Uso: python3 trilha.py marcos.json saida.wav
"""
import json
import sys
import wave
import numpy as np

SR = 44100
m = json.load(open(sys.argv[1]))
DUR = m["duracao"]
N = int(SR * DUR)
t = np.arange(N) / SR
rng = np.random.default_rng(8)


def janela(a, b, ataque=.3, soltura=.3):
    e = np.clip((t - a) / max(ataque, 1e-3), 0, 1) * np.clip((b - t) / max(soltura, 1e-3), 0, 1)
    return e * ((t >= a) & (t <= b))


def som(freq, inicio, dur, decai=6.0, vol=1.0):
    out = np.zeros(N)
    i0 = int(inicio * SR)
    n = min(int(dur * SR), N - i0)
    if n <= 0:
        return out
    tt = np.arange(n) / SR
    out[i0:i0 + n] = np.sin(2 * np.pi * freq * tt) * np.exp(-decai * tt) * np.clip(tt / .004, 0, 1) * vol
    return out


def varredura(f0, f1, a, b, vol):
    """Tom que desliza de f0 a f1 entre a e b."""
    k = np.clip((t - a) / (b - a), 0, 1)
    fase = 2 * np.pi * np.cumsum(f0 + (f1 - f0) * k) / SR
    return np.sin(fase) * janela(a, b, ataque=.4, soltura=.4) * vol


mix = np.zeros(N)
# tic seco a cada década
for i, td in enumerate(m["decadas"]):
    mix += som(1800, td, .06, 60, .35) + som(900, td, .05, 70, .2)
# puberdade: subida (11 → 19 anos)
mix += varredura(180, 720, 3.7, 7.6, .14)
# auge: impacto + brilho
mix += som(46, m["auge"], 1.4, 3, .9) + som(1568, m["auge"], 1.5, 3, .12)
# queda: tom descendo devagar (30 → 90 anos)
mix += varredura(620, 160, 10.6, 23.6, .1)
# fechamento: whoosh, enchimento da barra e impacto
env = janela(m["final"] - .2, m["final"] + .5, ataque=.4, soltura=.3)
mix += np.convolve(rng.standard_normal(N), np.ones(25) / 25, mode="same") * env * .6
mix += varredura(300, 520, m["barra"], m["barra"] + 1.6, .1)
mix += som(42, m["barra"] + 1.6, 1.6, 2.5, .8)

mix *= .89 / np.max(np.abs(mix))
with wave.open(sys.argv[2], "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((mix * 32767).astype(np.int16).tobytes())
print("ok", sys.argv[2])
