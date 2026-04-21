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
    assert "<VOLENV" not in content
    assert "PROJECT_SRATE 48000 0 0" in content
    assert "Pro-Q 3" in content
    assert project.tracks[0].name == "B1"
    assert project.tracks[0].children[0].name == "Character_Select"
    assert "ISBUS 1 1" in content
    assert "ISBUS 2 -1" in content


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


def test_items_continue_from_previous_track_end(tmp_path: Path) -> None:
    root = tmp_path / "ES"
    first = root / "A"
    second = root / "B"
    first.mkdir(parents=True)
    second.mkdir(parents=True)

    sample_rate = 48_000
    frame_count = sample_rate  # 1 second

    for wav_path in [first / "a.wav", second / "b.wav"]:
        with wave.open(str(wav_path), "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(b"\x00\x00" * frame_count)

    out = tmp_path / "out.rpp"
    cfg = GeneratorConfig(source_root=root, output_file=out, spacing_seconds=3.0)
    project = generate_project(cfg)

    assert len(project.tracks) == 2
    assert project.tracks[0].items[0].position == 0.0
    assert project.tracks[1].items[0].position == 4.0


def test_pre_fx_volume_envelope_can_be_enabled(tmp_path: Path) -> None:
    root = tmp_path / "ES"
    folder = root / "A"
    folder.mkdir(parents=True)
    (folder / "a.wav").write_bytes(b"0" * 48000)

    out = tmp_path / "out.rpp"
    cfg = GeneratorConfig(
        source_root=root,
        output_file=out,
        enable_pre_fx_volume_envelope=True,
        pre_fx_volume_envelope_range_db=6.0,
        sample_rate=96_000,
    )
    generate_project(cfg)

    content = out.read_text(encoding="utf-8")
    assert "<VOLENV" in content
    assert "PROJECT_SRATE 96000 0 0" in content
