"""Trilha sonora sintetizada da animação "coração e hormônios".

Batimentos e bipes do monitor seguem batidas.json (exportado da própria animação).
Calma até os 50 anos, tensão crescente com a queda hormonal, alarme e
fibrilação no infarto, linha reta do monitor e recuperação.
Uso: python3 trilha.py batidas.json saida.wav
"""
import json
import sys
import wave
import numpy as np

SR = 44100
dados = json.load(open(sys.argv[1]))
BATIDAS = dados["batidas"]
EV = dados["eventos"]
DUR = EV["DURACAO"]
N = int(SR * DUR)
t = np.arange(N) / SR
rng = np.random.default_rng(3)


def janela(a, b, ataque=.3, soltura=.3):
    e = np.clip((t - a) / max(ataque, 1e-3), 0, 1) * np.clip((b - t) / max(soltura, 1e-3), 0, 1)
    return e * ((t >= a) & (t <= b))


def som(freq, inicio, dur, decai=6.0, vol=1.0, forma="seno"):
    out = np.zeros(N)
    i0 = int(inicio * SR)
    n = min(int(dur * SR), N - i0)
    if n <= 0 or i0 < 0:
        return out
    tt = np.arange(n) / SR
    if forma == "seno":
        s = np.sin(2 * np.pi * freq * tt)
    elif forma == "sino":
        s = np.sin(2 * np.pi * freq * tt) + .35 * np.sin(2 * np.pi * freq * 2.01 * tt)
    else:  # bipe de monitor (seno com leve harmônico)
        s = np.sin(2 * np.pi * freq * tt) + .2 * np.sin(2 * np.pi * freq * 2 * tt)
    env = np.exp(-decai * tt) * np.clip(tt / .004, 0, 1)
    out[i0:i0 + n] = s * env * vol
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


def eco(x, atraso=.27, ganho=.3, vezes=4):
    y = x.copy()
    d = int(atraso * SR)
    for k in range(1, vezes + 1):
        y[d * k:] += x[:-d * k] * ganho ** k
    return y


mix = np.zeros(N)
T_ISQ, T_FV, T_PLANO, T_VOLTA = EV["T_ISQ"], EV["T_FV"], EV["T_PLANO"], EV["T_VOLTA"]

# ---------- coração + bipe do monitor em cada batida ----------
for b in BATIDAS:
    forca = .45 + .5 * np.clip((b - 10) / (T_FV - 10), 0, 1) if b < T_FV else .45
    mix += som(55, b, .3, 16, forca) + som(46, b + .14, .3, 18, forca * .7)
    mix += som(1046.5, b, .09, 30, .07 + .05 * (b > 15.5 and b < T_FV), "bipe")

# ---------- 0–12,5 s: calma (juventude) ----------
calmo = np.zeros(N)
for f in (130.8, 196.0, 261.6, 329.6):
    calmo += np.sin(2 * np.pi * f * t) * .045
calmo *= janela(0, 13.5, ataque=1.2, soltura=1.5)
mix += eco(calmo)

# ---------- 12,5–21,8 s: tensão crescente ----------
prog = np.clip((t - 12.5) / (T_FV - 12.5), 0, 1)
tensao = np.zeros(N)
for f in (73.4, 77.8, 110.0, 116.5):                    # cluster grave e desafinado
    tensao += np.sin(2 * np.pi * f * (1 + .006 * prog * np.sin(2 * np.pi * .5 * t)) * t)
riser = np.sin(2 * np.pi * np.cumsum(180 + 520 * prog ** 2) / SR)
mix += (tensao * .05 + riser * .025) * prog * janela(12.5, T_FV, ataque=.8, soltura=.05)

# ---------- ronco de terremoto nas quedas (sincronizado com o tremor da tela) ----------
for a, b, vol in ((3.8, 6.0, .18), (12.6, 14.6, .55), (15.5, 20.2, .22), (T_FV, T_PLANO, .6)):
    env = janela(a, b, ataque=.3, soltura=.4)
    mix += passa_baixa(rng.standard_normal(N), 140) * env * vol * 3

# ---------- infarto ----------
mix += som(38, T_ISQ, 1.8, 2.2, .8)                     # coágulo: impacto grave e sombrio
alarme = np.zeros(N)                                    # alarme hospitalar de dois tons
k = T_FV - .3
while k < T_PLANO:
    alarme += som(960, k, .22, 3, .16, "bipe") + som(770, k + .25, .22, 3, .16, "bipe")
    k += .5
mix += alarme
fv = (np.sin(2 * np.pi * 5.3 * t) + np.sin(2 * np.pi * 7.9 * t + 1)) * passa_baixa(rng.standard_normal(N), 900)
mix += fv * janela(T_FV, T_PLANO, ataque=.05, soltura=.1) * .35

# linha reta: tudo some, só o tom contínuo do monitor
corte = np.where((t >= T_PLANO) & (t < T_VOLTA), 0.0, 1.0)
corte = np.convolve(corte, np.ones(300) / 300, mode="same")
mix *= corte
mix += (np.sin(2 * np.pi * 1046.5 * t) + .2 * np.sin(2 * np.pi * 2093 * t)) * janela(T_PLANO, T_VOLTA, ataque=.02, soltura=.02) * .14

# recuperação: choque e volta da calma
mix += som(60, T_VOLTA, 1.0, 4, .9) + passa_baixa(rng.standard_normal(N), 3000) * janela(T_VOLTA, T_VOLTA + .15, .01, .1) * .5
alivio = np.zeros(N)
for f in (130.8, 196.0, 261.6, 329.6, 392.0):
    alivio += np.sin(2 * np.pi * f * t) * .045
alivio *= janela(T_VOLTA + .3, DUR, ataque=1.5, soltura=1.0)
alivio += som(784.0, 28.6, 2.5, 1.5, .12, "sino") + som(659.3, 29.3, 2.0, 1.5, .1, "sino")
mix += eco(alivio)

mix *= .89 / np.max(np.abs(mix))
with wave.open(sys.argv[2], "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((mix * 32767).astype(np.int16).tobytes())
print("ok", sys.argv[2])
