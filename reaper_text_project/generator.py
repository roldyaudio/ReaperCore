from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .models import FXChain, Item, Project, Track, VolumeEnvelope, guessed_item_length
from .script_order import load_script_order

AUDIO_EXTENSIONS = {".wav", ".mp3", ".flac", ".ogg", ".aif", ".aiff", ".m4a"}


@dataclass
class GeneratorConfig:
    source_root: Path
    output_file: Path
    min_db: float = -3.0
    max_db: float = 3.0
    use_fx_chain: bool = True
    include_ds: bool = True
    include_comp: bool = True
    include_eq: bool = True
    include_multiband: bool = True
    include_limiter: bool = True
    include_script_order: bool = False
    script_path: Path | None = None
    start_offset: float = 0.0
    spacing_seconds: float = 3.0


def _sorted_audio_files(folder: Path) -> list[Path]:
    files = [p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in AUDIO_EXTENSIONS]
    return sorted(files, key=lambda p: p.name.lower())


def _folder_display_name(root: Path, folder: Path) -> str:
    if folder == root:
        return root.name
    return folder.name


def _collect_track_tree(folder: Path, root: Path) -> tuple[Track, Path] | None:
    track = Track(name=_folder_display_name(root, folder))
    children: list[Track] = []

    for child_folder in sorted([d for d in folder.iterdir() if d.is_dir()], key=lambda p: p.name.lower()):
        collected = _collect_track_tree(child_folder, root)
        if collected:
            child_track, _ = collected
            children.append(child_track)

    has_audio = bool(_sorted_audio_files(folder))
    if not has_audio and not children:
        return None

    track.children = children
    return track, folder


def _collect_tracks(root: Path) -> list[tuple[Track, Path]]:
    pairs: list[tuple[Track, Path]] = []
    root_has_audio = bool(_sorted_audio_files(root))

    if root_has_audio:
        collected_root = _collect_track_tree(root, root)
        if collected_root:
            pairs.append(collected_root)
    else:
        for child_folder in sorted([d for d in root.iterdir() if d.is_dir()], key=lambda p: p.name.lower()):
            collected = _collect_track_tree(child_folder, root)
            if collected:
                pairs.append(collected)

    if not pairs:
        raise ValueError(f"No audio files found under: {root}")

    return pairs


def _attach_items(
    track: Track,
    folder: Path,
    iid_start: int,
    start_cursor: float,
    cfg: GeneratorConfig,
    order_map: dict[str, int] | None,
) -> tuple[int, float]:
    files = _sorted_audio_files(folder)
    if order_map:
        fallback = {f.name.lower(): i for i, f in enumerate(files)}
        files.sort(key=lambda p: order_map.get(p.name.lower(), 10_000 + fallback[p.name.lower()]))

    cursor = start_cursor
    iid = iid_start
    for f in files:
        length = guessed_item_length(f)
        print(f"[reaper-rpp] Procesando archivo: {f} | duración: {length:.3f}s")
        track.items.append(Item(file_path=f.resolve(), position=cursor, length=length, iid=iid))
        cursor += length + cfg.spacing_seconds
        iid += 1

    if not track.items:
        return iid, cursor

    start = track.items[0].position
    end = track.items[-1].position + track.items[-1].length
    track.volume_envelope = VolumeEnvelope(start_time=start, end_time=end, min_db=cfg.min_db, max_db=cfg.max_db)

    if cfg.use_fx_chain:
        track.use_fx_chain = True
        track.fx_chain = FXChain(
            include_ds=cfg.include_ds,
            include_comp=cfg.include_comp,
            include_eq=cfg.include_eq,
            include_multiband=cfg.include_multiband,
            include_limiter=cfg.include_limiter,
        )

    return iid, cursor


def _attach_track_tree_items(
    track: Track,
    folder: Path,
    iid_start: int,
    start_cursor: float,
    cfg: GeneratorConfig,
    order_map: dict[str, int] | None,
) -> tuple[int, float]:
    iid, cursor = _attach_items(track, folder, iid_start, start_cursor, cfg, order_map)
    for child_track in track.children:
        child_folder = folder / child_track.name
        iid, cursor = _attach_track_tree_items(child_track, child_folder, iid, cursor, cfg, order_map)
    return iid, cursor


def generate_project(cfg: GeneratorConfig) -> Project:
    if not cfg.source_root.exists() or not cfg.source_root.is_dir():
        raise ValueError(f"Source root does not exist or is not a directory: {cfg.source_root}")

    order_map = None
    if cfg.include_script_order and cfg.script_path:
        order_map = load_script_order(cfg.script_path)

    pairs = _collect_tracks(cfg.source_root)
    iid = 1
    timeline_cursor = cfg.start_offset
    tracks: list[Track] = []
    for track, folder in pairs:
        iid, timeline_cursor = _attach_track_tree_items(track, folder, iid, timeline_cursor, cfg, order_map)
        tracks.append(track)

    project = Project(tracks=tracks)
    project.save(cfg.output_file)
    return project
