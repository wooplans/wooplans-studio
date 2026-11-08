from visitelib import *
def R(x0, y0, x1, y1): return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
ROOMS = [
 ("Terrasse d'entrée", 11, R(360, 606, 666, 698), (512, 650), 1.7, 'terrasse', 0),
 ("Salle à manger", 22, R(458, 342, 658, 600), (558, 470), 1.8, 'manger', 0),
 ("Salon", 39, R(670, 338, 972, 688), (820, 510), 1.5, 'salon', 0),
 ("Couloir", None, R(268, 226, 828, 322), (548, 274), 1.4, 'couloir', 0),
 ("Cuisine", 15, R(580, 100, 822, 250), (700, 175), 1.9, 'cuisine', 0),
 ("Terrasse de service", None, R(578, 40, 812, 96), (692, 68), 2.4, 'terrasse', 1),
 ("Magasin", 9, R(832, 70, 926, 240), (880, 150), 2.6, 'magasin', 0),
 ("WC visiteurs", None, R(836, 246, 940, 312), (888, 278), 2.8, 'toilettes', 0),
 ("Chambre 1", 15, R(96, 70, 254, 250), (175, 155), 2.2, 'première', 0),
 ("Chambre 2", 15, R(396, 76, 568, 240), (482, 160), 2.2, 'deuxième', 0),
 ("Salle d'eau", None, R(266, 60, 392, 214), (329, 138), 2.6, "d'eau", 0),
 ("Chambre parentale", 24, R(216, 330, 444, 590), (330, 460), 1.9, 'parentale', 0),
 ("Salle de bain", 8, R(80, 256, 260, 380), (170, 318), 2.4, 'bain', 0),
 ("Dressing", 10, R(66, 392, 210, 590), (136, 500), 2.4, 'dressing', 0),
]
WAY = [
 [(600, 612)],
 [(662, 420)],
 [(780, 335), (700, 300)],
 [(604, 262), (606, 230)],
 [(650, 104)],
 [(762, 120), (816, 205)],
 [(880, 240)],
 [(850, 284), (400, 276), (272, 262), (240, 232)],
 [(250, 244), (300, 272), (404, 252)],
 [(380, 252), (366, 200)],
 [(312, 238), (286, 336)],
 [(252, 352), (216, 372)],
 [(192, 392)],
]
frame, ARR, DUR = make('visite', 'visite', 'rdc3d.png', ROOMS, WAY, 'Visite du plan', 'Villa de plain-pied', '201 m²', 'Cuisine · 3 chambres', big_size=120, rb_start=0,
    notes={'Couloir': 'dessert tout', 'Terrasse de service': 'petite terrasse', 'WC visiteurs': 'visiteurs', "Salle d'eau": 'partagée'})
if __name__ == '__main__':
    for tt in [float(x) for x in sys.argv[1:]]:
        frame(tt).save(OUTDIR + f'/test_visite_{tt:05.1f}.png')
