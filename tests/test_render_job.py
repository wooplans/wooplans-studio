import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "visite_plan"))
import render_job  # noqa: E402


def make_job(tmp_path, *files, nseg=3):
    (tmp_path / "segments.json").write_text(json.dumps([{}] * nseg))
    for f in files:
        (tmp_path / f).write_text("{}")
    return tmp_path


def test_mode_std(tmp_path):
    p = render_job.plan(make_job(tmp_path))
    assert p["mode"] == "std" and [i["part"] for i in p["include"]] == ["seg0", "seg1", "seg2"]
    assert {i["scene"] for i in p["include"]} == {"scene_visite.py"}


def test_mode_bump_rend_hook_estimation_cta(tmp_path):
    p = render_job.plan(make_job(tmp_path, "bump.json", nseg=2))
    assert p["mode"] == "bump"
    assert [i["part"] for i in p["include"]] == ["seg0", "seg1", "hook_raw", "estim_raw", "cta_raw"]
    assert {i["cls"] for i in p["include"][2:]} == {"HookScene", "EstimScene", "CtaScene"}


def test_mode_nf_prioritaire(tmp_path):
    p = render_job.plan(make_job(tmp_path, "bump.json", "nf.json", nseg=1))
    assert p["mode"] == "nf"
    assert [i["part"] for i in p["include"]] == ["seg0", "hook_raw", "cta_raw"]
    assert p["include"][0]["scene"] == "scene_visite_nf.py" and p["include"][1]["scene"] == "scene_bumpers_nf.py"


def test_fichiers_de_marque_presents():
    root = Path(__file__).resolve().parents[1]
    for n in render_job.BRAND:
        assert (root / "assets" / "brand" / n).is_file(), n
    assert render_job.MUSIC.is_file()
