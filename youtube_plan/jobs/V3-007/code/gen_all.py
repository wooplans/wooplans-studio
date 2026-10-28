# Génère les voix (Gradium) de chaque séquence du job YT_JOB. Clé : secret GRADIUM_API_KEY (jamais en clair).
import os, sys, subprocess, time
JOB = os.environ['YT_JOB']; CODE = os.path.join(JOB, 'code'); V = os.path.join(JOB, 'voix')
sys.path.insert(0, CODE)
from gtts import tts
from script import S
os.makedirs(V, exist_ok=True)
for k in S:
    wav = os.path.join(V, k + '.wav'); raw = os.path.join(V, k + '.raw')
    for attempt in range(3):
        try:
            n, ch = tts(S[k], os.path.join(V, k))
            subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', raw, '-ar', '48000', '-ac', '1', wav], check=True)
            os.remove(raw)
            print(k, 'ok', ch[-1]['stop_s'], flush=True); break
        except Exception as e:
            print(k, 'retry', attempt, str(e)[:150], flush=True); time.sleep(5)
    else:
        raise SystemExit('échec voix : ' + k)
