"""Génère les voix de script.S (hors 'catalogue', réutilisé) dans <job>/voix. Usage: YT_JOB=<job> GRADIUM_API_KEY=... python gen_all.py"""
import sys, subprocess, os
J = os.path.abspath(os.environ['YT_JOB']); sys.path.insert(0, J + '/code')
from gtts import tts
from script import S
os.makedirs(J + '/voix', exist_ok=True)
bad = 0
for k in S:
    if os.path.exists(f'{J}/voix/{k}.wav'): continue
    for attempt in range(3):
        try:
            n, ch = tts(S[k], f'{J}/voix/{k}')
            subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', f'{J}/voix/{k}.raw', '-ar', '48000', '-ac', '1', f'{J}/voix/{k}.wav'], check=True)
            os.remove(f'{J}/voix/{k}.raw'); print(k, 'ok', ch[-1]['stop_s'], flush=True); break
        except Exception as e:
            print(k, 'retry', str(e)[:150], flush=True)
    else:
        bad += 1
sys.exit(1 if bad else 0)
