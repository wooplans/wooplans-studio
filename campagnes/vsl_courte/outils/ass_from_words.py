import json,re,sys
src,dst=sys.argv[1],sys.argv[2]
ws=json.load(open(src))
def t(s): return f"{int(s//3600)}:{int(s%3600//60):02d}:{s%60:05.2f}"
m=[]
for a,b,w in ws:
    if m and (m[-1][2].endswith("'") or w.startswith("'") or w.startswith("-")): m[-1]=[m[-1][0],b,m[-1][2]+w]; continue
    m.append([a,b,w])
FIX={"jusqu'au":"jusqu'aux"}
m=[[a,b,FIX.get(w,w)] for a,b,w in m]
chunks=[];cur=[]
for x in m:
    cur.append(x); txt=' '.join(y[2] for y in cur)
    if len(cur)>=3 or re.search(r'[.,!?]$',x[2]) or len(txt)>16: chunks.append(cur);cur=[]
if cur: chunks.append(cur)
allw=[x for c in chunks for x in c]; L=[]
for c in chunks:
    for wi,x in enumerate(c):
        i=allw.index(x); nxt=allw[i+1][0] if i+1<len(allw) else x[1]+0.3
        en=nxt if nxt-x[1]<0.6 else x[1]+0.25
        parts=[]
        for wj,y in enumerate(c):
            word=re.sub(r'[.,!?]$','',y[2]).upper()
            parts.append(r"{\c&H00E6FF&\fscx112\fscy112}"+word+r"{\c&HFFFFFF&\fscx100\fscy100}" if wj==wi else word)
        L.append(f"Dialogue: 0,{t(x[0])},{t(en)},H,,0,0,0,,{' '.join(parts)}")
open(dst,'w').write("""[Script Info]
ScriptType: v4.00+
PlayResX: 720
PlayResY: 1280
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: H,Inter Display Black,64,&H00FFFFFF,&H00FFFFFF,&H00000000,&H96000000,-1,0,0,0,100,100,0,0,1,7,3,2,30,30,MARGV,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
""".replace("MARGV",sys.argv[3] if len(sys.argv)>3 else "250")+"\n".join(L)+"\n")
