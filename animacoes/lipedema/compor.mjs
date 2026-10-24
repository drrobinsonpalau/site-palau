// Compõe o vídeo da paciente (câmera lenta, aproximação, granulação) com a camada HTML transparente.
// Uso: node compor.mjs <video> <sobreposicao.html> <saida.mp4> <teclas.json>
import { chromium } from '/opt/node22/lib/node_modules/playwright/index.mjs';
import { spawn } from 'node:child_process';
import { writeFileSync } from 'node:fs';

const [,, video, overlay, out, teclasJson] = process.argv;
const fps = 30, dur = 18, n = Math.round(dur * fps);

const filtro = [
  // 75% da velocidade; última imagem congelada para o fechamento
  `[0:v]setpts=PTS*4/3,fps=${fps},tpad=stop_mode=clone:stop_duration=5,trim=0:${dur},setpts=PTS-STARTPTS,`,
  // aproximação lenta, preto e branco com contraste e granulação de filme
  `scale=w='2*trunc(540*(1+0.07*t/${dur}))':h=-2:eval=frame:flags=lanczos,crop=1080:1920:'(iw-1080)/2':'(ih-1920)/2',`,
  `hue=s=0,eq=contrast=1.12:brightness=-0.02,noise=alls=9:allf=t+u,format=yuv420p[base];`,
  `[base][1:v]overlay=0:0:format=auto[v]`
].join('');

const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-i', video,
  '-f', 'image2pipe', '-framerate', String(fps), '-i', '-',
  '-filter_complex', filtro, '-map', '[v]', '-an', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '18', '-r', String(fps), out],
  { stdio: ['pipe', 'inherit', 'inherit'] });

const b = await chromium.launch({ args: ['--no-sandbox', '--disable-dev-shm-usage', '--disable-gpu'] });
const p = await b.newPage({ viewport: { width: 1080, height: 1920 } });
await p.goto('file://' + overlay + '?render=1', { waitUntil: 'networkidle' });
await p.evaluate(() => document.fonts.ready);
writeFileSync(teclasJson, JSON.stringify(await p.evaluate(() => ({ teclas: window.TECLAS, fins: window.FINS, impacto: window.IMPACTO, flashes: window.FLASHES, duracao: window.DURACAO }))));
for (let i = 0; i < n; i++) {
  await p.evaluate(t => { window.tl.seek(t, false); }, i / fps);
  const buf = await p.screenshot({ type: 'png', omitBackground: true });
  if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
}
ff.stdin.end();
await new Promise(r => ff.on('close', r));
await b.close();
console.log('frames', n);
