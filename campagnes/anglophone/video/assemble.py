import subprocess, sys, glob
CC = sys.argv[1]
def dur(f): return float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',f]))
clips = sorted(glob.glob(f'clips_{CC}/*.mp4'))
open(f'list_{CC}.txt','w').write(''.join(f"file '{c}'\n" for c in clips))
subprocess.run(['ffmpeg','-v','error','-y','-f','concat','-safe','0','-i',f'list_{CC}.txt','-c','copy',f'video_{CC}.mp4'],check=True)
d = [dur(c) for c in clips]; starts=[sum(d[:i]) for i in range(len(d))]; total=sum(d)
t_pa = starts[2]; t_a2 = starts[3]; t_pb = starts[10]
inp = ['-i',f'video_{CC}.mp4','-i',f'{CC}_a1.mp3','-i',f'PA_{CC}.mp4','-i',f'{CC}_a2.mp3','-i',f'PB_{CC}.mp4','-i','music.mp3','-i','boom.wav','-i','boom.wav']
f = [f"[1:a]adelay=0|0[v1]", f"[2:a]atrim=0:3.0,adelay={int(t_pa*1000)}|{int(t_pa*1000)}[v2]",
     f"[3:a]adelay={int(t_a2*1000)}|{int(t_a2*1000)}[v3]", f"[4:a]adelay={int(t_pb*1000)}|{int(t_pb*1000)}[v4]",
     f"[5:a]atrim=0:{total:.2f},volume=0.20,afade=t=out:st={total-1:.2f}:d=1[m]",
     "[6:a]volume=0.9[b0]", f"[7:a]adelay={int((t_pa+1.5)*1000)}|{int((t_pa+1.5)*1000)},volume=0.7[b1]"]
mix = ['[v1]','[v2]','[v3]','[v4]','[m]','[b0]','[b1]']
for i, s in enumerate(starts[1:]):
    inp += ['-i','whoosh.wav']; ms=int(max(0,s-0.15)*1000)
    f.append(f"[{8+i}:a]adelay={ms}|{ms}[w{i}]"); mix.append(f'[w{i}]')
f.append(''.join(mix)+f"amix=inputs={len(mix)}:normalize=0,alimiter=limit=0.95[a]")
subprocess.run(['ffmpeg','-v','error','-y',*inp,'-filter_complex',';'.join(f),'-map','0:v','-map','[a]','-t',f'{total:.2f}',
  '-c:v','copy','-c:a','aac','-b:a','160k','-metadata','comment=© WooPlans - wooplans.com',f'WOOPLANS-EN-E-{CC}.mp4'],check=True)
print(CC, round(total,2), [round(x,2) for x in starts])
