#!/bin/bash
# Monta o vídeo intercalando gráfico (base) e animação 3D, com transições de ida e volta.
set -e
S=/tmp/claude-0/-home-user-site-palau/aa0c7d38-7a04-54b3-80d5-643ce013a61c/scratchpad
M=/home/user/site-palau/animacoes/coracao-hormonios
cd $S
node comp.mjs $S/infarto-3d-original.mp4 $M/infarto-3d/sobreposicao.html $S/seg2.mp4 $M/infarto-3d > comp.log 2>&1
python3 -I $M/infarto-3d/trilha_3d.py $M/infarto-3d/batidas-3d.json $S/seg2.wav
TOTAL=42.65
ffmpeg -v error -y -i $S/coracao-mudo.mp4 -i $S/seg2.mp4 -i $S/coracao-trilha.wav -i $S/seg2.wav -filter_complex "\
[0:v]split=4[b1][b2][b3][b4];[1:v]split=3[d1][d2][d3];\
[b1]trim=0:16.3,setpts=PTS-STARTPTS[s1];[d1]trim=0:4.92,setpts=PTS-STARTPTS[s2];\
[b2]trim=16.3:18.2,setpts=PTS-STARTPTS[s3];[d2]trim=4.92:7.42,setpts=PTS-STARTPTS[s4];\
[b3]trim=18.2:20.2,setpts=PTS-STARTPTS[s5];[d3]trim=7.42:14.25,setpts=PTS-STARTPTS[s6];\
[b4]trim=20.4:31,setpts=PTS-STARTPTS[s7];\
[s1][s2]xfade=transition=zoomin:duration=0.4:offset=15.9[x1];\
[x1][s3]xfade=transition=circleclose:duration=0.4:offset=20.42[x2];\
[x2][s4]xfade=transition=zoomin:duration=0.4:offset=21.92[x3];\
[x3][s5]xfade=transition=circleclose:duration=0.4:offset=24.02[x4];\
[x4][s6]xfade=transition=zoomin:duration=0.4:offset=25.62[x5];\
[x5][s7]xfade=transition=fadewhite:duration=0.4:offset=32.05,\
drawbox=x=0:y=0:w=iw:h=10:color=0x1C1D20:t=fill,drawbox=x=0:y=0:w='iw*t/$TOTAL':h=10:color=0xFF2A4F:t=fill[v];\
[2:a]asplit=4[p1][p2][p3][p4];[3:a]asplit=3[q1][q2][q3];\
[p1]atrim=0:16.3,asetpts=PTS-STARTPTS[a1];[q1]atrim=0:4.92,asetpts=PTS-STARTPTS[a2];\
[p2]atrim=16.3:18.2,asetpts=PTS-STARTPTS[a3];[q2]atrim=4.92:7.42,asetpts=PTS-STARTPTS[a4];\
[p3]atrim=18.2:20.2,asetpts=PTS-STARTPTS[a5];[q3]atrim=7.42:14.25,asetpts=PTS-STARTPTS[a6];\
[p4]atrim=20.4:31,asetpts=PTS-STARTPTS[a7];\
[a1][a2]acrossfade=d=0.4[y1];[y1][a3]acrossfade=d=0.4[y2];[y2][a4]acrossfade=d=0.4[y3];\
[y3][a5]acrossfade=d=0.4[y4];[y4][a6]acrossfade=d=0.4[y5];[y5][a7]acrossfade=d=0.4,loudnorm=I=-14:TP=-1.5:LRA=11[a]" \
-map "[v]" -map "[a]" -c:v libx264 -pix_fmt yuv420p -crf 18 -r 30 -c:a aac -b:a 192k -ar 44100 $M/coracao-hormonios-infarto-3d.mp4
ffprobe -v error -show_entries stream=codec_type,duration -of compact $M/coracao-hormonios-infarto-3d.mp4
