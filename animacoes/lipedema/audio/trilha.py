"""Trilha sonora sintetizada da animação "3 sinais de lipedema" (18 s).

Teclas de máquina de escrever sincronizadas a cada letra (teclas.json, exportado
da camada de texto), sino de fim de linha, batidas de dor, impacto nas trocas,
tensão grave e silêncio antes do "É LIPEDEMA.".
Uso: python3 trilha.py teclas.json saida.wav
"""
import json
import sys
import wave
import numpy as np

SR = 44100
dados = json.load(open(sys.argv[1]))
DUR = dados["duracao"]
N = int(SR * DUR)
t = np.arange(N) / SR
rng = np.random.default_rng(11)


def janela(a, b, ataque=.3, soltura=.3):
    e = np.clip((t - a) / max(ataque, 1e-3), 0, 1) * np.clip((b - t) / max(soltura, 1e-3), 0, 1)
    return e * ((t >= a) & (t <= b))


def colocar(mix, sinal, inicio, vol=1.0):
    i0 = int(inicio * SR)
    n = min(len(sinal), N - i0)
    if n > 0 and i0 >= 0:
        mix[i0:i0 + n] += sinal[:n] * vol


def tecla(forte=1.0):
    """Clique mecânico: ruído curto filtrado + batida grave do tipo."""
    n = int(.07 * SR)
    tt = np.arange(n) / SR
    ruido = rng.standard_normal(n)
    clique = np.diff(ruido, prepend=0) * np.exp(-tt * 260) * .5          # agudo, seco
    corpo = np.sin(2 * np.pi * (180 + 60 * rng.random()) * tt) * np.exp(-tt * 90)   # batida do tipo no papel
    return (clique + corpo * .8) * forte


def sino():
    n = int(1.4 * SR)
    tt = np.arange(n) / SR
    return (np.sin(2 * np.pi * 2637 * tt) + .4 * np.sin(2 * np.pi * 5274 * tt) + .2 * np.sin(2 * np.pi * 3951 * tt)) * np.exp(-tt * 3.2)


def grave(freq, dur, decai):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    return np.sin(2 * np.pi * freq * tt) * np.exp(-tt * decai) * np.clip(tt / .004, 0, 1)


mix = np.zeros(N)

# teclas (espaço e quebra de linha mais suaves)
for k in dados["teclas"]:
    forte = .45 if k["c"] in " \n" else .8 + .25 * rng.random()
    colocar(mix, tecla(forte), k["t"], .5)
# sino no fim de cada linha digitada
for f in dados["fins"]:
    colocar(mix, sino(), f + .08, .07)

# tensão grave (lá menor desafinado), crescendo até o fechamento
tensao = sum(np.sin(2 * np.pi * f * t) for f in (55.0, 55.6, 82.4, 110.0)) * .05
tensao += np.sin(2 * np.pi * 220 * t) * .015 * (.5 + .5 * np.sin(2 * np.pi * .25 * t))
mix += tensao * (.5 + .5 * np.clip(t / 12.9, 0, 1)) * janela(0, 12.95, ataque=.8, soltura=.1)

# batidas de dor (pulso vermelho do item 1)
for b in (1.6, 2.4, 3.1):
    colocar(mix, grave(52, .5, 9) + grave(44, .5, 11), b, .7)

# impacto + respiro de ruído nas trocas de item
for f in dados["flashes"]:
    colocar(mix, grave(45, 1.2, 3.5), f, .8)
    env = janela(f - .35, f + .05, ataque=.3, soltura=.05)
    mix += np.convolve(rng.standard_normal(N), np.ones(30) / 30, mode="same") * env * .5

# fechamento: impacto forte no "É LIPEDEMA." e acorde grave que se resolve
colocar(mix, grave(38, 2.2, 1.8) + grave(76, 1.0, 4) * .4, dados["impacto"], 1.0)
fecho = sum(np.sin(2 * np.pi * f * t) for f in (110.0, 164.8, 220.0, 261.6)) * .035
mix += fecho * janela(dados["impacto"], DUR, ataque=.4, soltura=1.2)

mix *= .89 / np.max(np.abs(mix))
with wave.open(sys.argv[2], "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((mix * 32767).astype(np.int16).tobytes())
print("ok", sys.argv[2])
