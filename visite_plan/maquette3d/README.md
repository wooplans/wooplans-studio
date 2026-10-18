# Maquette 3D interactive (essai V3-003)

Basée sur l'outil MIT [wy51ai/floorplan-3d](https://github.com/wy51ai/floorplan-3d) (Three.js, un seul fichier HTML).
Le plan n'est pas importé automatiquement : murs, fenêtres, portes et pièces sont relevés sur
`jobs/V3-003/plan.png` (contour 10,60 m × 11,60 m, `meta.json`) puis convertis en mm.

- Surfaces affichées : étiquettes du plan (PDF), jamais calculées. Aucun prix (module coût retiré).
- Régénérer : `python build_v3_003.py <floorplan-3d>/index.html villa_v3_003_3d.html`
- Ouvrir `villa_v3_003_3d.html` dans un navigateur (Three.js chargé depuis jsDelivr), touche `T` pour la 3D,
  bouton « Walk » pour la visite à la première personne.
