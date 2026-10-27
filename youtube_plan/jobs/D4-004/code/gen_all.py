import sys, subprocess, os
sys.path.insert(0,'/tmp/d4/code')
from gtts import tts
from script import S
for k in S:
    if os.path.exists(f'/tmp/d4/voix/{k}.wav'): continue
    for attempt in range(3):
        try:
            n,ch=tts(S[k],f'/tmp/d4/voix/{k}')
            subprocess.run(['ffmpeg','-v','error','-y','-i',f'/tmp/d4/voix/{k}.raw','-ar','48000','-ac','1',f'/tmp/d4/voix/{k}.wav'])
            print(k,'ok',ch[-1]['stop_s'],flush=True); break
        except Exception as e:
            print(k,'retry',str(e)[:150],flush=True)
