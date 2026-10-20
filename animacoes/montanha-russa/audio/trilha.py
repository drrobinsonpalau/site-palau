"""Trilha sonora sintetizada da animação "montanha-russa hormonal".

Homem: calmo e alegre. Mulher: tensão crescente fase a fase.
Perimenopausa: caos até o grito em 16,4 s. Final: alívio.
Uso: python3 trilha.py grito.raw saida.wav
"""
import sys
import wave
import numpy as np

SR = 44100
DUR = 21.0
N = int(SR * DUR)
t = np.arange(N) / SR
rng = np.random.default_rng(7)


def janela(a, b, ataque=.3, soltura=.3):
    """Envelope 0..1 ligado entre a e b, com rampas suaves."""
    e = np.clip((t - a) / max(ataque, 1e-3), 0, 1) * np.clip((b - t) / max(soltura, 1e-3), 0, 1)
    return e * ((t >= a) & (t <= b))


def nota(freq, inicio, dur, forma="seno", decai=4.0, vol=1.0):
    out = np.zeros(N)
    i0 = int(inicio * SR)
    n = min(int(dur * SR), N - i0)
    if n <= 0:
        return out
    tt = np.arange(n) / SR
    if forma == "seno":
        s = np.sin(2 * np.pi * freq * tt)
    elif forma == "sino":  # caixinha de música
        s = np.sin(2 * np.pi * freq * tt) + .35 * np.sin(2 * np.pi * freq * 2.01 * tt) + .15 * np.sin(2 * np.pi * freq * 3.99 * tt)
    elif forma == "quadrada":
        s = np.sign(np.sin(2 * np.pi * freq * tt)) * .5
    env = np.exp(-decai * tt) * np.clip(tt / .005, 0, 1)
    out[i0:i0 + n] = s * env * vol
    return out


def passa_baixa(x, corte):
    """Filtro de um polo com corte variável (array ou escalar, em Hz)."""
    corte = np.broadcast_to(corte, x.shape)
    a = 1 - np.exp(-2 * np.pi * corte / SR)
    y = np.zeros_like(x)
    acc = 0.0
    for i in range(len(x)):
        acc += a[i] * (x[i] - acc)
        y[i] = acc
    return y


def eco(x, atraso=.23, ganho=.35, vezes=4):
    y = x.copy()
    d = int(atraso * SR)
    for k in range(1, vezes + 1):
        y[d * k:] += x[:-d * k] * ganho ** k
    return y


mix = np.zeros(N)

# ---------------- 0–4,55 s: homem, tranquilo ----------------
calmo = np.zeros(N)
for f in (174.6, 220.0, 261.6, 329.6):           # Fá maior com sétima: acolhedor
    calmo += np.sin(2 * np.pi * f * t) * .07
calmo *= janela(0, 4.7, ataque=.8, soltura=.5)
melodia = [523.3, 587.3, 659.3, 784.0, 659.3, 587.3, 523.3, 440.0]   # pentatônica
for i, f in enumerate(melodia):
    calmo += nota(f, .3 + i * .5, 1.6, "sino", decai=3, vol=.13)
# assobio do bonequinho
assobio_t = [(1.0, 1568), (1.35, 1760), (1.7, 1975), (2.2, 1568), (2.55, 1318), (2.9, 1568)]
for ini, f in assobio_t:
    n = int(.3 * SR); i0 = int(ini * SR)
    tt = np.arange(n) / SR
    vib = 1 + .012 * np.sin(2 * np.pi * 6 * tt)
    s = np.sin(2 * np.pi * f * vib * tt) * np.sin(np.pi * tt / .3) * .05
    calmo[i0:i0 + n] += s
mix += eco(calmo)

# ---------------- whooshes das cortinas ----------------
for ini in (4.2, 11.2):
    env = janela(ini, ini + .75, ataque=.35, soltura=.4)
    ruido = rng.standard_normal(N) * env
    corte = 300 + 5000 * env
    mix += passa_baixa(ruido, corte) * .35

# ---------------- 4,55–11,55 s: mulher, tensão crescente ----------------
seg = janela(4.55, 11.6, ataque=.5, soltura=.15)
prog = np.clip((t - 4.55) / 7.0, 0, 1)                 # 0 → 1 ao longo do ciclo
tensao = np.zeros(N)
for f in (110.0, 130.8, 164.8):                         # Lá menor, cada vez mais desafinado
    tensao += np.sin(2 * np.pi * f * t) * .06
    tensao += np.sin(2 * np.pi * f * (1 + .012 * prog) * t) * .06 * prog
riser = np.sin(2 * np.pi * np.cumsum(220 + 380 * prog) / SR) * .03 * prog
trem = 1 - .5 * prog * (.5 + .5 * np.sin(2 * np.pi * (2 + 6 * prog) * t))
mix += (tensao + riser) * trem * seg
# TPM (a partir do dia 16 ≈ 8,26 s): rosnado grave
rosnado = np.sign(np.sin(2 * np.pi * 55 * t)) * .5 + np.sign(np.sin(2 * np.pi * 77.8 * t)) * .5   # trítono
mix += passa_baixa(rosnado * janela(8.26, 11.5, ataque=1.2, soltura=.2), 400) * .25
# impacto no pico de LH (ovulação)
mix += nota(48, 7.88, 1.2, "seno", decai=3.5, vol=.6) + nota(1046.5, 7.88, 1.0, "sino", decai=4, vol=.12)

# batimento cardíaco: 70 → 115 bpm (mulher) e 130 → 175 bpm (perimenopausa)
def coracao(a, b, bpm0, bpm1, vol0, vol1):
    out = np.zeros(N)
    tc = a
    while tc < b:
        k = (tc - a) / (b - a)
        bpm = bpm0 + (bpm1 - bpm0) * k
        v = vol0 + (vol1 - vol0) * k
        out += nota(55, tc, .25, "seno", decai=18, vol=v) + nota(48, tc + .12, .25, "seno", decai=20, vol=v * .7)
        tc += 60 / bpm
    return out

mix += coracao(4.9, 11.5, 70, 115, .35, .6)
mix += coracao(11.7, 16.35, 130, 175, .6, .85)

# ---------------- 11,55–16,4 s: perimenopausa, caos ----------------
caos_env = janela(11.6, 16.4, ataque=.4, soltura=.02) * np.clip((t - 11.6) / 4.8, 0, 1) ** 1.2
cluster = np.zeros(N)
for f in (233.1, 246.9, 261.6, 277.2, 369.9, 392.0):   # cluster dissonante
    cluster += np.sin(2 * np.pi * f * (1 + .004 * np.sin(2 * np.pi * .7 * t + f)) * t)
cluster *= .045
ruido = passa_baixa(rng.standard_normal(N), 800 + 6000 * caos_env) * .5
mix += (cluster + ruido) * caos_env
# bipes de pane no contador
for ini in (13.96, 14.55, 15.14):
    for k in range(3):
        mix += nota(1200 + 300 * k, ini + k * .05, .06, "quadrada", decai=10, vol=.12)

# ---------------- 16,4 s: silêncio súbito, impacto e GRITO ----------------
corte_silencio = np.where((t >= 16.4) & (t < 17.6), 0.0, 1.0)
corte_silencio = np.convolve(corte_silencio, np.ones(220) / 220, mode="same")
mix *= corte_silencio
mix += nota(42, 16.4, 1.6, "seno", decai=2.5, vol=.9)
grito = np.frombuffer(open(sys.argv[1], "rb").read(), dtype=np.int16).astype(np.float64) / 32768
i0 = int(16.4 * SR)
n = min(len(grito), N - i0)
fade = np.ones(n); fade[-int(.25 * SR):] = np.linspace(1, 0, int(.25 * SR))
mix[i0:i0 + n] += grito[:n] * fade * .95

# ---------------- 17,75–21 s: alívio ----------------
alivio = np.zeros(N)
for f in (130.8, 196.0, 261.6, 329.6, 392.0):          # Dó maior aberto
    alivio += np.sin(2 * np.pi * f * t) * .05
alivio *= janela(17.75, 21, ataque=1.2, soltura=.8)
alivio += nota(784.0, 17.75, 2.5, "sino", decai=1.5, vol=.12) + nota(659.3, 19.1, 2.5, "sino", decai=1.5, vol=.1)
mix += eco(alivio)

# master
mix *= .89 / np.max(np.abs(mix))
pcm = (mix * 32767).astype(np.int16)
with wave.open(sys.argv[2], "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes(pcm.tobytes())
print("ok", sys.argv[2])
