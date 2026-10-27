import os, sys, json, base64, requests
def key():
    for l in open(os.path.expanduser('~/mnt/VIDEO AUTO/.env'),encoding='utf-8',errors='ignore'):
        if l.startswith('GRADIUM_API_KEY='): return l.split('=',1)[1].strip().strip('"\'')
def tts(text, out_prefix, voice='TsRKBRWZGYldAeEI'):
    r=requests.post('https://api.gradium.ai/api/post/speech/tts',headers={'x-api-key':key()},
        json={'text':text,'voice_id':voice,'output_format':'wav','only_audio':False},stream=True,timeout=170)
    r.raise_for_status()
    audio=b''; ch=[]
    for line in r.iter_lines():
        if not line: continue
        m=json.loads(line); t=m.get('type')
        if t=='audio': audio+=base64.b64decode(m['audio'])
        elif t=='text': ch.append({'text':m.get('text'),'start_s':m.get('start_s'),'stop_s':m.get('stop_s')})
        elif t=='error': raise RuntimeError(str(m)[:300])
    open(out_prefix+'.raw','wb').write(audio); json.dump(ch,open(out_prefix+'.chunks.json','w'),ensure_ascii=False)
    return len(audio), ch
