from pathlib import Path

from wooplans import catalogue_a3 as C

D4_004 = ("De type contemporain et très élégant, ce plan de 314m2 a été conçu pour accueillir 01 grande famille. "
          "Son plan nous offre: Au RDC : 01 spacieux salon.\n\nCaractéristiques :\n- 02 Living (02 Salons)\n"
          "- 01 Dining (Salle à Manger)\n- 04 Bedrooms (04 Chambres\n- 01 Cinema\n\nGros œuvre : à partir de 28 274 410 FCFA (estimation indicative).")

PAGE = """<html><head><meta name="description" content="Un duplex &amp; sa terrasse."/></head><body>
<h1 class="x">Duplex D4-004<span>Plan de duplex</span></h1>
<a aria-label="Voir l&#x27;image 1" class="a"><img alt="" src="/media/public/d4-004/aaa.webp?w=160"/></a>
<a aria-label="Voir l&#x27;image 2" class="a"><img alt="" src="/media/public/d4-004/bbb.webp?w=160"/></a>
<dl><div><dt class="t">Chambres</dt><dd class="v">4</dd></div><div><dt class="t">Salles de bain</dt><dd class="v">3</dd></div>
<div><dt>Niveaux</dt><dd>R+1</dd></div><div><dt>Surface totale</dt><dd>313 m²</dd></div>
<div><dt>Dimensions du bâtiment</dt><dd>15,5 m × 13 m</dd></div><div><dt>Terrain nécessaire</dt><dd>400 m² (18 m × 20 m)</dd></div></dl>
</body></html>"""


def snap(code="D4-004", cat="duplex", **kw):
    s = {"code": code, "slug": f"{cat}-{code.lower()}", "category": cat, "bedrooms": 4, "bathrooms": 3, "levels": 2, "surface_total": 313,
         "land_area": 400, "building_width": 15, "building_depth": 13, "land_width": 18, "land_depth": 20, "renders": ["/media/public/x/a.webp"],
         "estimate_total": 300, "estimate_lots": [{"label": "A", "amount": 100}, {"label": "B", "amount": 200}], "description": D4_004}
    s.update(kw)
    return s


def model(code, cat="duplex", **kw):
    return C.model_data(snap(code, cat, **kw), plans=[Path("/p/1.png")], renders=[Path("/r/1.png")] * 3)


# ---- texte
def test_norm_text():
    assert C.norm_text("01 salon+ salle, 155,88m2 et 40 m²") == "1 salon + salle, 155,88 m² et 40 m²"
    assert C.norm_text("D4-004 et 2026") == "D4-004 et 2026"          # les codes ne sont pas touchés


def test_intro_cuts_features_and_gros_oeuvre():
    t = C.intro_paragraph(snap())
    assert "Caractéristiques" not in t and "Gros" not in t and "28" not in t
    assert t.startswith("De type contemporain") and "1 grande famille" in t


def test_intro_truncates_at_sentence_and_falls_back_to_summary():
    long = ("Phrase une. " * 60).strip()
    t = C.intro_paragraph({"description": long})
    assert len(t) <= 520 and t.endswith(".")
    assert C.intro_paragraph({"description": "", "summary": "Résumé du site."}) == "Résumé du site."


def test_features_french_wins_and_plurals():
    f = C.parse_features(D4_004)
    assert f == ["2 salons", "1 salle à manger", "4 chambres", "1 cinema"]
    d = "x\n\nCaractéristiques :\n- 05 Bathrooms (Salle de Bain)\n- 01 Chambre (Visiteur)\n- 01 Living+Dining (Salon+SAM)\n- 02 Master's Bedroom (Chambre Principale)\n"
    assert C.parse_features(d) == ["5 salles de bain", "1 chambre (visiteur)", "1 salon + SAM", "2 chambres principales"]


def test_features_ignores_sentences_and_headings():
    d = "x\n\nCaractéristiques :\n- RDC :\n- 2 chambres secondaires (12,67 m² et 12,66 m²) avec une salle d'eau\n- Séjour : espace de 32 m²\n- 01 Guest toilet(WC V.)\n"
    assert C.parse_features(d) == ["1 WC visiteurs"]
    assert C.parse_features("Aucune liste ici") == []


def test_numbers():
    assert C.fr_num(20.759999999999998) == "20,76" and C.fr_num(15.0) == "15" and C.fr_num(15.55) == "15,55"
    assert C.money(62832010) == "62 832 010"


# ---- lecture du site
def test_parse_public_page():
    d = C.parse_public_page(PAGE, "D4-004")
    assert (d["bedrooms"], d["bathrooms"], d["levels"], d["surface_total"]) == (4, 3, 2, 313)
    assert (d["building_width"], d["building_depth"]) == (15.5, 13)
    assert (d["land_area"], d["land_width"], d["land_depth"]) == (400, 18, 20)
    assert d["summary"] == "Un duplex & sa terrasse." and d["name"] == "Duplex D4-004"
    assert d["renders"] == ["/media/public/d4-004/aaa.webp", "/media/public/d4-004/bbb.webp"]      # sans ?w=160
    assert C.parse_public_page("<html>page cassée</html>", "D4-004") == {}


def test_apply_public_site_wins_and_clears_removed_dims():
    s = snap()
    C.apply_public(s, {"bedrooms": 5, "land_area": None})
    assert s["bedrooms"] == 5 and s["land_area"] is None and s["building_width"] is None     # dimension disparue du site = effacée
    assert s["estimate_total"] == 300                                                          # le Premium n'est pas touché


def test_parse_sitemap():
    xml = "<urlset><url><loc>https://www.wooplans.com/catalogue/villa-v3-002</loc></url><url><loc>https://www.wooplans.com/catalogue/duplex-d4-004</loc></url><url><loc>https://www.wooplans.com/catalogue-premium</loc></url></urlset>"
    assert C.parse_sitemap(xml) == [{"code": "D4-004", "slug": "duplex-d4-004", "category": "duplex"}, {"code": "V3-002", "slug": "villa-v3-002", "category": "villa"}]


def test_parse_levels():
    assert (C.parse_levels("R+1"), C.parse_levels("Plain-pied"), C.parse_levels("R+2"), C.parse_levels("2")) == (2, 1, 3, 2)


# ---- données Premium
def test_ingest_compact_and_connector_shapes():
    s = C.ingest_payload({"code": "V4-002", "total": 24800000, "lots": [3124800, 4575600, 3459600, 3273600, 2455200, 2046000, 2864400, 3000800],
                          "plans": ["private/v4-002/p.png"], "description": "d"})
    assert s["estimate_lots"][1] == {"label": "Élévations", "amount": 4575600} and sum(l["amount"] for l in s["estimate_lots"]) == 24800000
    s2 = C.ingest_payload({"code": "D4-004", "description": "d", "premium": {"estimate_total": 3, "estimate_lots": [{"label": "A", "amount": 3}],
                                                                              "floor_plans": [{"key": "k1", "url": "u"}]}})
    assert s2["floor_plans"] == ["k1"] and s2["estimate_total"] == 3
    s3 = C.ingest_payload({"code": "X", "total": 5, "lots": [["Gros", 2], ["Fin", 3]], "plans": []})
    assert s3["estimate_lots"] == [{"label": "Gros", "amount": 2}, {"label": "Fin", "amount": 3}]


def test_missing_data():
    assert C.missing_data(snap(), [Path("p.png")]) == []
    assert C.missing_data(snap(), []) == ["plan de distribution"]
    assert C.missing_data(snap(estimate_lots=[], estimate_total=0, renders=[]), [Path("p.png")]) == ["devis", "rendus"]


def test_model_problems_flags_sum_and_copy():
    assert C.model_problems(model("D4-004")) == []
    bad = model("D4-004", estimate_total=999)
    assert any("somme des lots" in p for p in C.model_problems(bad))
    assert any("expire" in p or "urgence" in p for p in C.model_problems(model("D4-004", description="L'offre expire dans 3 heures.")))


# ---- fichiers
def test_render_sources_hires_override_and_site(tmp_path):
    cache, hires = tmp_path / "cache", tmp_path / "hires"
    (hires / "D4-004").mkdir(parents=True)
    (hires / "D4-004" / "1.png").write_bytes(b"x")
    s = snap(renders=["/media/public/d4-004/a.webp", "/media/public/d4-004/b.webp", "/media/public/d4-004/c.webp", "/media/public/d4-004/d.webp"])
    got = C.render_sources(s, {"D4-004": {"render_picks": [1, 2, 4]}}, cache, hires)
    assert got == [hires / "D4-004" / "1.png", cache / "D4-004" / "b.webp", cache / "D4-004" / "d.webp"]
    got = C.render_sources(snap("V4-002", "villa", renders=["/m/a.webp", "/m/b.webp"]), {"V4-002": {"cover_file": "visite_plan/x.png"}}, cache, hires)
    assert got[0] == C.ROOT / "visite_plan/x.png" and got[1] == cache / "V4-002" / "b.webp"


def test_plan_files_sorted(tmp_path):
    for n in ("D4-004-2.jpg", "D4-004-1.png", "D4-004-3.txt", "D4-005-1.png"):
        (tmp_path / n).write_bytes(b"x")
    assert [p.name for p in C.plan_files("D4-004", tmp_path)] == ["D4-004-1.png", "D4-004-2.jpg"]


# ---- document : sommaire et pagination
def test_layout_pages_and_split():
    groups = C.group_models([model("V3-002", "villa"), model("D4-005"), model("D4-004"), model("V3-001", "villa")])
    assert [(k, [m["snap"]["code"] for m in ms]) for k, _, ms in groups] == [("duplex", ["D4-004", "D4-005"]), ("villa", ["V3-001", "V3-002"])]
    lay = C.layout(groups)
    # 1 couverture, 2 sommaire, 3 séparateur Duplex, 4-5 duplex, 6 séparateur Villas, 7-8 villas
    assert lay["sommaire_pages"] == 1 and lay["divider_page"] == {"duplex": 3, "villa": 6}
    assert lay["model_page"] == {"D4-004": 4, "D4-005": 5, "V3-001": 7, "V3-002": 8} and lay["total"] == 8
    assert C.layout(C.group_models([model("V3-001", "villa")], "duplex")) == {"sommaire_pages": 1, "model_page": {}, "divider_page": {}, "total": 2}


def test_sommaire_grows_beyond_one_page():
    n = C.ROWS_PER_COL * C.COLS_PER_PAGE + 1
    ms = [model(f"V3-{i:03d}", "villa") for i in range(1, n + 1)]
    lay = C.layout(C.group_models(ms))
    assert lay["sommaire_pages"] == 2 and lay["model_page"]["V3-001"] == 2 + 2 + 1 and lay["total"] == 4 + n


def test_document_links_numbers_and_parts():
    ms = [model("D4-004"), model("D4-005"), model("V3-001", "villa")]
    html, lay = C.build_document(ms)
    for code, page in lay["model_page"].items():
        assert f'id="p-{code}"' in html and f'href="#p-{code}"' in html
        assert f"{code} · page {page} / {lay['total']}" in html
    assert html.count('class="page model"') == 3 and "Sommaire" in html and "Catalogue" in html
    only_villa, lay2 = C.build_document(ms, "villa")
    assert 'id="p-D4-004"' not in only_villa and lay2["model_page"] == {"V3-001": 4} and "Catalogue Premium A3 · Villas" in only_villa


def test_model_page_content_and_layout_rule():
    two = C.model_page(C.model_data(snap(), plans=[Path("/a/p1.png"), Path("/a/p2.png")], renders=[Path("/r/1.png")] * 3), 4, 9, "Duplex")
    assert "Plan du rez-de-chaussée" in two and "Plan de l&#x27;étage" in two and "Caractéristiques" in two and "Composition" not in two
    one = C.model_page(C.model_data(snap("V4-002", "villa", levels=1), plans=[Path("/a/p1.png")], renders=[Path("/r/1.png")] * 3), 5, 9, "Villa")
    assert "Plan de distribution" in one and "Composition" in one and "plain-pied" in one       # un seul plan : liste sous le plan
    assert "300" in two and "15 × 13 m" in two and "18 × 20 m" in two and "400 m²" in two and "À VALIDER" not in two


def test_plan_labels_neutral_unless_rdc_etage():
    three = C.model_page(C.model_data(snap(), plans=[Path("/a/1.png"), Path("/a/2.png"), Path("/a/3.png")], renders=[Path("/r/1.png")] * 3), 4, 9, "Duplex")
    assert "Plan de distribution 3/3" in three and "Plan du rez-de-chaussée" not in three      # le 3e fichier peut être un tableau de surfaces
    villa2 = C.model_page(C.model_data(snap("V3-018", "villa", levels=1), plans=[Path("/a/1.png"), Path("/a/2.png")], renders=[Path("/r/1.png")] * 3), 5, 9, "Villa")
    assert "Plan de distribution 1/2" in villa2


def test_skip_plans_override():
    plans = [Path("/a/1.png"), Path("/a/2.png"), Path("/a/3.png")]
    m = C.model_data(snap(), {"D4-004": {"skip_plans": [3]}}, plans=plans, renders=[])
    assert m["plans"] == plans[:2]
    assert C.model_data(snap(), {}, plans=plans, renders=[])["plans"] == plans
