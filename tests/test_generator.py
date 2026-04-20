from pathlib import Path
import wave

from reaper_text_project.generator import GeneratorConfig, generate_project
from reaper_text_project.models import guessed_item_length


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


def test_guessed_item_length_reads_exact_wav_duration(tmp_path: Path) -> None:
    wav_path = tmp_path / "exact.wav"
    sample_rate = 48_000
    duration_seconds = 1.5
    frame_count = int(sample_rate * duration_seconds)

    with wave.open(str(wav_path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(b"\x00\x00" * frame_count)

    assert guessed_item_length(wav_path) == 1.5
