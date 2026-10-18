from vsl.build import load_scripts, problems


def test_three_scripts_pass_guardrails():
    scripts = load_scripts()
    assert len(scripts) == 3
    for s in scripts:
        assert problems(s) == []
        assert any("39 000 FCFA" in b["voix"] for b in s["beats"])
        assert s["beats"][-1]["type"] == "cta"
