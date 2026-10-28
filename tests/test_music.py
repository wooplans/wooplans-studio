import json
from collections import Counter

from wooplans import music


def _setup(tmp_path, monkeypatch, ids=(1, 2, 3), analysed=(1, 2, 3)):
    d = tmp_path / "music"
    d.mkdir()
    (d / "library.json").write_text(json.dumps({"tracks": [{"id": i, "title": f"T{i}", "artist": "A", "use": True}
                                                           for i in ids]}), encoding="utf-8")
    (d / "tracks.json").write_text(json.dumps({f"mixkit-{i}.mp3": {"beat_interval": 0.5} for i in analysed}),
                                   encoding="utf-8")
    monkeypatch.setattr(music, "MUSIC", d)
    monkeypatch.setattr(music, "LIB", d / "library.json")
    monkeypatch.setattr(music, "TRACKS", d / "tracks.json")
    monkeypatch.setattr(music, "SHORTS_OUT", tmp_path / "out")


def test_pick_least_used(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch)
    assert music.pick("job", Counter({"mixkit:1": 2, "mixkit:2": 1, "mixkit:3": 1})) in {"mixkit:2", "mixkit:3"}
    assert music.pick("job", Counter({"mixkit:1": 1, "mixkit:2": 1})) == "mixkit:3"


def test_pick_rotates_through_whole_pool(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch)
    used, seen = Counter(), []
    for k in range(3):
        s = music.pick(f"job{k}", used)
        used[s] += 1
        seen.append(s)
    assert sorted(seen) == ["mixkit:1", "mixkit:2", "mixkit:3"]


def test_pick_ignores_unanalysed(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch, analysed=(2,))
    assert music.pick("job", Counter()) == "mixkit:2"


def test_usage_reads_render_logs(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch)
    out = tmp_path / "out"
    out.mkdir()
    (out / "a.json").write_text(json.dumps({"music": "mixkit:1"}), encoding="utf-8")
    (out / "b.json").write_text(json.dumps({"music": "mixkit:1"}), encoding="utf-8")
    assert music.usage()["mixkit:1"] == 2
    assert music.describe("mixkit:2")["title"] == "T2"
