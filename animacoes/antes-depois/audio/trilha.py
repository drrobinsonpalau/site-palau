"""Trilha sonora sintetizada da animação "antes e depois" (22 s).

Pad otimista em progressão, sino em cada medição (quando a linha passa pela data),
whoosh e impacto na revelação do depois, contagem e acorde final nos cartões.
Uso: python3 trilha.py saida.wav
"""
import sys
import wave
import numpy as np

SR = 44100
DUR = 22.0
N = int(SR * DUR)
t = np.arange(N) / SR
rng = np.random.default_rng(4)

# mesmas datas e tempos da animação (linha avança de 2,4 s a 12,9 s com power1.inOut)
DATAS = [0, 320, 335, 347, 349, 390, 432, 467, 488]   # dias desde 13/06/2025
INICIO, DURACAO_LINHA = 2.4, 10.5


def tempo_da_data(d):
    f = d / DATAS[-1]
    u = np.sqrt(f / 2) if f < .5 else 1 - np.sqrt(2 * (1 - f)) / 2
    return INICIO + DURACAO_LINHA * u


def janela(a, b, ataque=.3, soltura=.3):
    e = np.clip((t - a) / max(ataque, 1e-3), 0, 1) * np.clip((b - t) / max(soltura, 1e-3), 0, 1)
    return e * ((t >= a) & (t <= b))


def som(freq, inicio, dur, decai=4.0, vol=1.0, sino=True):
    out = np.zeros(N)
    i0 = int(inicio * SR)
    n = min(int(dur * SR), N - i0)
    if n <= 0:
        return out
    tt = np.arange(n) / SR
    s = np.sin(2 * np.pi * freq * tt)
    if sino:
        s += .35 * np.sin(2 * np.pi * freq * 2.01 * tt) + .12 * np.sin(2 * np.pi * freq * 3.98 * tt)
    out[i0:i0 + n] = s * np.exp(-decai * tt) * np.clip(tt / .004, 0, 1) * vol
    return out


def passa_baixa(x, corte):
    corte = np.broadcast_to(corte, x.shape)
    a = 1 - np.exp(-2 * np.pi * corte / SR)
    y = np.zeros_like(x)
    acc = 0.0
    for i in range(len(x)):
        acc += a[i] * (x[i] - acc)
        y[i] = acc
    return y


def eco(x, atraso=.25, ganho=.3, vezes=4):
    y = x.copy()
    d = int(atraso * SR)
    for k in range(1, vezes + 1):
        y[d * k:] += x[:-d * k] * ganho ** k
    return y


mix = np.zeros(N)

# pad em progressão C – G – Am – F, subindo de intensidade até a revelação
acordes = [(130.8, 164.8, 196.0), (98.0, 123.5, 146.8), (110.0, 130.8, 164.8), (87.3, 110.0, 130.8)]
pad = np.zeros(N)
for i in range(4):
    a = i * 3.3
    for f in acordes[i]:
        for oit in (1, 2):
            pad += np.sin(2 * np.pi * f * oit * t) * .03 * janela(a, a + 3.6, ataque=.6, soltura=.6)
pad *= .6 + .4 * np.clip(t / 13, 0, 1)
mix += pad

# pulso leve (100 bpm) durante a linha
k = 2.4
while k < 13.1:
    mix += som(65.4, k, .3, 12, .25, sino=False)
    k += .6

# sino em cada medição, subindo na escala pentatônica
escala = [523.3, 587.3, 659.3, 784.0, 880.0, 1046.5, 1174.7, 1318.5, 1568.0]
for d, f in zip(DATAS, escala):
    mix += som(f, tempo_da_data(d), 1.2, 4, .12)

# whoosh e impacto na revelação do depois
env = janela(12.9, 13.75, ataque=.6, soltura=.15)
mix += passa_baixa(rng.standard_normal(N), 300 + 6000 * env) * env * .9
mix += som(45, 13.8, 1.5, 3, .9, sino=False) + som(1568, 13.8, 1.8, 2.5, .15)

# contagem dos cartões e acorde final
k = 14.8
while k < 16.4:
    mix += som(2093, k, .05, 40, .05)
    k += .08
final = np.zeros(N)
for f in (261.6, 329.6, 392.0, 523.3, 659.3):
    final += np.sin(2 * np.pi * f * t) * .05
final *= janela(16.4, DUR, ataque=.05, soltura=2.5) * np.exp(-np.clip(t - 16.4, 0, None) * .35)
mix += eco(final + som(1046.5, 16.4, 2.5, 1.5, .15))

mix *= .89 / np.max(np.abs(mix))
with wave.open(sys.argv[1], "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((mix * 32767).astype(np.int16).tobytes())
print("ok", sys.argv[1])
