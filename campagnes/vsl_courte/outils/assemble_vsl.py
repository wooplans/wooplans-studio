import subprocess
T=[(0,2.6,'P1',0,1),(2.6,4.6,'B_terrain',0.5,1),(4.6,6.6,'P1',4.6,1.12),(6.6,8.6,'B_abandon',0.5,1),(8.6,10.5,'P1',8.6,1.25),
(10.5,12.6,'B_macons2',0.3,1),(12.6,15.0,'P1',12.6,1),(15.0,16.6,'B_tropgrand',0.5,1),(16.6,18.4,'M_budget',0,1),(18.4,20.3,'B_abandon',2.0,1),
(20.3,24.3,'B_archi',0,1),(24.3,28.4,'M_propositions',0,1),(28.4,31.4,'P_A',0,1.1),(31.4,34.6,'M_cent',0,1),(34.6,37.7,'B_famille',0,1),
(37.7,41.8,'M_plan',0,1),(41.8,48.3,'M_devis',0,1),(48.3,55.6,'M_terrain',0,1),(55.6,61.2,'M_ov_chantier',0,1),(61.2,64.3,'P_B1',0,1.12),
(64.3,69.2,'M_ov_brouette',0,1),(69.2,73.5,'M_compare',0,1),(73.5,77.4,'B_couple',0,1),(77.4,79.2,'P_B2',0,1),(79.2,81.1,'M_deux_bonus',0,1),
(81.1,90.2,'M_bonus1',0,1),(90.2,93.4,'B_whatsapp',0,1),(93.4,96.4,'M_whatsapp',0,1),(96.4,104.5,'M_garantie',0,1),(104.5,112.7,'M_prix',0,1),
(112.7,118.3,'P_B4',0,1),(118.3,120.8,'M_final',0,1)]
args=['ffmpeg','-v','error','-y'];fl=[]
for i,(a,b,src,off,z) in enumerate(T):
    args+=['-ss',str(off),'-i',src+'.mp4']
    Wz=int(720*z)//2*2; Hz=int(1310*z)//2*2
    fl.append(f'[{i}:v]scale={Wz}:{Hz},crop=720:1280,setsar=1,fps=30,tpad=stop_mode=clone:stop_duration=3,trim=duration={b-a:.3f},setpts=PTS-STARTPTS[v{i}]')
n=len(T)
args+=['-i','voix_s1_3.wav','-i','voix_A.wav','-i','voix_B2.wav','-i','musique.mp3']
fl.append(''.join(f'[v{i}]' for i in range(n))+f'concat=n={n}:v=1:a=0,ass=subs_full.ass[v]')
fl.append(f'[{n}:a]aresample=44100,aformat=channel_layouts=mono[a0];[{n+1}:a]aresample=44100,aformat=channel_layouts=mono,adelay=15000[a1];[{n+2}:a]aresample=44100,aformat=channel_layouts=mono,adelay=55600[a2]')
fl.append('[a0][a1][a2]amix=inputs=3:normalize=0,pan=stereo|c0=c0|c1=c0[voice]')
fl.append(f'[{n+3}:a]aresample=44100,atempo=0.965,atrim=0:120.8,volume=0.38,afade=t=in:d=1.5,afade=t=out:st=119.4:d=1.4[mus]')
fl.append('[voice][mus]amix=inputs=2:normalize=0:duration=longest,loudnorm=I=-15:TP=-1.5:LRA=11[a]')
args+=['-filter_complex',';'.join(fl),'-map','[v]','-map','[a]','-t','120.8','-c:v','libx264','-crf','23','-preset','medium','-pix_fmt','yuv420p','-c:a','aac','-b:a','128k','-ar','44100','-movflags','+faststart','VSL_courte_v1.mp4']
subprocess.run(args,check=True)
