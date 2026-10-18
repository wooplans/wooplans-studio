# VSL Catalogue Premium (motion design)

- `scripts/*.json` : voix off + texte écran validés par Tao (source unique du texte).
- `motion.py` : charte, fond animé, illustrations vectorielles, voix (aperçu muet ou LeTao).
- `vsl1.py`, `vsl2.py`, `vsl3.py` : une scène par VSL ; chaque animation est accrochée à un mot de la voix (`self.say`).
- `python -m vsl.build` : garde-fous + `SCRIPTS.md` + liens UTM.

Rendu (dans `vsl/`) :
```
manimgx render vsl1.py VSL1 -r 1080x1920 --fps 30 -o out/VSL1.mp4                    # aperçu muet
VSL_VOICE=letao ELEVENLABS_API_KEY=… manimgx render vsl1.py VSL1 -r 1080x1920 --fps 30  # voix LeTao, calage au mot
```
La voix est mise en cache dans `voice/` (non versionné) : un nouveau rendu ne regénère pas la voix.
