import subprocess,sys
T={"KE":[0,3.44,9.0,12.97,17.73,22.96,28.08,31.13,33.28,36.2],"GH":[0,3.69,10.89,14.4,17.93,23.4,27.96,31.35,33.51,36.5]}
def ff(*a): subprocess.run(["ffmpeg","-y","-hide_banner","-loglevel","error",*map(str,a)],check=True)
for cc,t in T.items():
    clips=[]
    for i in range(9):
        d=t[i+1]-t[i]; n=round(d*30); out=f"{cc}-c{i}.mp4"
        z="min(zoom+0.0007,1.10)" if i%2==0 else "if(eq(on,0),1.10,max(zoom-0.0007,1.0))"
        ff("-loop","1","-i",f"{cc}-s{i+1}.png","-vf",f"scale=2160:-1,zoompan=z='{z}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={n}:s=1080x1920:fps=30,format=yuv420p","-frames:v",n,"-c:v","libx264","-preset","veryfast","-crf","20",out)
        clips.append(out)
    open(f"{cc}.txt","w").write("".join(f"file '{c}'\n" for c in clips))
    ff("-f","concat","-safe","0","-i",f"{cc}.txt","-c","copy",f"{cc}-mid.mp4")
    fc=("[1:v]format=rgba,scale=390:-1,colorchannelmixer=aa=0.55[w1];[2:v]format=rgba,scale=390:-1,colorchannelmixer=aa=0.55[w2];"
        "[0:v][w1]overlay=x='(W-w)*(0.5+0.5*sin(0.53*t))':y='(H-h)*(0.5+0.5*sin(0.37*t+1.1))'[a];"
        "[a][w2]overlay=x='(W-w)*(0.5+0.5*sin(0.41*t+2.6))':y='(H-h)*(0.5+0.5*sin(0.29*t+4.0))'[v];"
        "[3:a]volume=1.0[vo];[4:a]volume=0.10,afade=t=out:st=%.1f:d=1.5[mu];[vo][mu]amix=inputs=2:duration=first:dropout_transition=0[au]"%(t[-1]-1.6))
    ff("-i",f"{cc}-mid.mp4","-i","wm_logo.png","-i","wm_logo.png","-i",f"vo-{cc}.mp3","-i","music.mp3","-filter_complex",fc,
       "-map","[v]","-map","[au]","-t",t[-1],"-c:v","libx264","-preset","veryfast","-crf","20","-pix_fmt","yuv420p","-r","30","-c:a","aac","-b:a","160k",
       "-metadata","comment=© WooPlans - wooplans.com","-metadata","copyright=© WooPlans",f"WOOPLANS-EN-{cc}.mp4")
    print("ok",cc)
