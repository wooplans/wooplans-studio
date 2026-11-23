# Montage de la VSL Catalogue Premium (acheteurs de l'extrait)

- Moteur : HyperFrames (`npm i hyperframes@0.9.25` dans un projet `init --resolution portrait`), composition générée par `build_vsl.py`.
- Voix off : Gradium, voix 2 choisie par Tao (`voix/voice.json`), fichiers `voix/tts/sNN.wav` + `.chunks.json` (horodatage des mots → sous-titres).
- Témoignages : extraits d'Ibrahim, Bassirou, Francis, Renaud (audio seul : photo + onde sonore calculée sur l'audio réel).
- Images Poyo (gpt-image) : illustrations d'après nos modèles (D4-001, V3-037), jamais présentées comme des maisons de clients.
- Filigranes : 2 logos `wm_logo.png` qui se déplacent du début à la fin.
- Rien n'est publié sans l'accord de Tao.

Étapes : copier les médias dans `vsl/assets/` (voir les noms dans `build_vsl.py`), `python3 build_vsl.py`, `npx hyperframes lint`, `npx hyperframes render -o out/vsl.mp4`.
