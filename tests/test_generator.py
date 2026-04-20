from pathlib import Path

from reaper_text_project.generator import GeneratorConfig, generate_project


def test_generate_project_from_nested_dirs(tmp_path: Path) -> None:
    root = tmp_path / "ES"
    sub = root / "B1" / "Character_Select"
    sub.mkdir(parents=True)

    for name in ["b.wav", "a.wav"]:
        (sub / name).write_bytes(b"0" * 48000)

    out = tmp_path / "out.rpp"
    cfg = GeneratorConfig(source_root=root, output_file=out)
    project = generate_project(cfg)

    assert out.exists()
    content = out.read_text(encoding="utf-8")
    assert "<TRACK" in content
    assert "<ITEM" in content
    assert "<VOLENV" in content
    assert "Pro-Q 3" in content
    assert project.tracks[0].name == "B1 :: Character_Select"
