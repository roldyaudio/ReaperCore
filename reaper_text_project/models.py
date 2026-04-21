from __future__ import annotations

import importlib.util
import math
import uuid
import wave
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path


def new_guid() -> str:
    return "{" + str(uuid.uuid4()).upper() + "}"


def db_to_amplitude(db: float) -> float:
    return 10 ** (db / 20.0)


@dataclass
class RPPNode:
    name: str
    args: list[str] = field(default_factory=list)
    lines: list[str] = field(default_factory=list)
    children: list["RPPNode"] = field(default_factory=list)

    def render(self, indent: int = 0) -> str:
        p = "  " * indent
        header = f"{p}<{self.name}"
        if self.args:
            header += " " + " ".join(self.args)
        header += "\n"
        out = [header]
        for line in self.lines:
            out.append(f"{p}  {line}\n")
        for child in self.children:
            out.append(child.render(indent + 1))
        out.append(f"{p}>\n")
        return "".join(out)


@dataclass
class Item:
    file_path: Path
    position: float
    length: float
    iid: int
    guid: str = field(default_factory=new_guid)
    iguid: str = field(default_factory=new_guid)

    @property
    def name(self) -> str:
        return self.file_path.name

    def to_node(self) -> RPPNode:
        node = RPPNode("ITEM")
        node.lines.extend(
            [
                f"POSITION {self.position:.8f}",
                "SNAPOFFS 0",
                f"LENGTH {self.length:.8f}",
                "LOOP 1",
                "ALLTAKES 0",
                "FADEIN 1 0 0 1 0 0 0",
                "FADEOUT 1 0 0 1 0 0 0",
                "MUTE 0 0",
                "SEL 0",
                f"IGUID {self.iguid}",
                f"IID {self.iid}",
                f"NAME {self.name}",
                "VOLPAN 1 0 1 -1",
                "SOFFS 0",
                "PLAYRATE 1 1 0 -1 0 0.0025",
                "CHANMODE 0",
                f"GUID {self.guid}",
            ]
        )
        src = RPPNode("SOURCE", ["WAVE"])
        src.lines.append(f'FILE "{str(self.file_path)}"')
        node.children.append(src)
        return node


@dataclass
class VolumeEnvelope:
    start_time: float
    end_time: float
    min_db: float
    max_db: float
    eguid: str = field(default_factory=new_guid)

    def to_node(self) -> RPPNode:
        node = RPPNode("VOLENV")
        node.lines.extend(
            [
                f"EGUID {self.eguid}",
                "ACT 1 -1",
                "VIS 1 1 1",
                "LANEHEIGHT 0 0",
                "ARM 1",
                "DEFSHAPE 0 -1 -1",
                f"PT {self.start_time:.8f} {db_to_amplitude(self.min_db):.8f} 0",
                f"PT {self.end_time:.8f} {db_to_amplitude(self.max_db):.8f} 0 0 1",
            ]
        )
        return node


@dataclass
class FXPreset:
    name: str
    file_name: str
    vst_id: str

    def to_node(self) -> RPPNode:
        node = RPPNode(
            "VST",
            [
                f'"VST3: {self.name} (FabFilter)"',
                f'"{self.file_name}"',
                "0",
                '""',
                self.vst_id,
                '""',
            ],
        )
        node.lines.extend(
            [
                "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
                "AFByb2dyYW0gMQAAAAAA",
            ]
        )
        return node


@dataclass
class FXChain:
    include_ds: bool = True
    include_comp: bool = True
    include_eq: bool = True
    include_multiband: bool = True
    include_limiter: bool = True

    def _selected(self) -> list[FXPreset]:
        pool = [
            (self.include_ds, FXPreset("Pro-DS", "FabFilter Pro-DS.vst3", "838599213{59E324D08EE811E1B8578101BBE59B18}")),
            (self.include_comp, FXPreset("Pro-C 2", "FabFilter Pro-C 2.vst3", "1000537396{79F415E3C8E74807AD5DA3CF7024F618}")),
            (self.include_eq, FXPreset("Pro-Q 3", "FabFilter Pro-Q 3.vst3", "756089518{72C4DB717A4D459AB97E51745D84B39D}")),
            (self.include_multiband, FXPreset("Pro-MB", "FabFilter Pro-MB.vst3", "1847376412{C3B68142C79846F282B73CABDF139076}")),
            (self.include_limiter, FXPreset("Pro-L 2", "FabFilter Pro-L 2.vst3", "1938458649{AFD92F729A0447B7B5E8D1D568DEA985}")),
        ]
        return [fx for enabled, fx in pool if enabled]

    def to_node(self) -> RPPNode:
        node = RPPNode("FXCHAIN")
        node.lines.extend(["WNDRECT 24 52 1020 593", "SHOW 0", "LASTSEL 0", "DOCKED 0", "BYPASS 0 0 0"])
        for fx in self._selected():
            node.children.append(fx.to_node())
            node.lines.extend(["PRESETNAME \"Program 1\"", "FLOATPOS 0 0 0 0", f"FXID {new_guid()}", "WAK 0 0", "BYPASS 0 0 0"])
        return node


@dataclass
class Track:
    name: str
    items: list[Item] = field(default_factory=list)
    children: list["Track"] = field(default_factory=list)
    use_fx_chain: bool = False
    fx_chain: FXChain | None = None
    volume_envelope: VolumeEnvelope | None = None
    guid: str = field(default_factory=new_guid)

    def to_node(self, folder_depth: int = 0) -> RPPNode:
        if folder_depth > 0:
            isbus_line = f"ISBUS 1 {folder_depth}"
        elif folder_depth < 0:
            isbus_line = f"ISBUS 2 {folder_depth}"
        else:
            isbus_line = "ISBUS 0 0"

        node = RPPNode("TRACK", [self.guid])
        node.lines.extend(
            [
                f'NAME "{self.name}"',
                "PEAKCOL 16576",
                "BEAT -1",
                "AUTOMODE 0",
                "PANLAWFLAGS 3",
                "VOLPAN 1 0 -1 -1 1",
                "MUTESOLO 0 0 0",
                "IPHASE 0",
                "PLAYOFFS 0 1",
                isbus_line,
                "BUSCOMP 0 0 0 0 0",
                "SHOWINMIX 1 0.6667 0.5 1 0.5 0 0 0 0",
                "FIXEDLANES 9 0 0 0 0",
                "SEL 0",
                "REC 0 0 0 0 0 0 0 0",
                "VU 2",
                "TRACKHEIGHT 0 0 0 0 0 0 0",
                "INQ 0 0 0 0.5 100 0 0 100",
                "NCHAN 2",
                "FX 1",
                f"TRACKID {self.guid}",
                "PERF 0",
                "MIDIOUT -1",
                "MAINSEND 1 0",
            ]
        )
        if self.volume_envelope:
            node.children.append(self.volume_envelope.to_node())
        if self.use_fx_chain and self.fx_chain:
            node.children.append(self.fx_chain.to_node())
        for item in self.items:
            node.children.append(item.to_node())
        return node


@dataclass
class Project:
    tracks: list[Track]
    name: str = "Generated from text"
    reaper_version: str = '"7.69/win64"'
    sample_rate: int = 48_000

    def _header_lines(self) -> list[str]:
        ts = int(datetime.now(tz=timezone.utc).timestamp())
        return [
            f"<REAPER_PROJECT 0.1 {self.reaper_version} {ts} 0",
            "  <NOTES 0 2",
            "  >",
            "  RIPPLE 0 0",
            "  GROUPOVERRIDE 0 0 0 0",
            "  AUTOXFADE 135",
            "  RECORD_PATH \"Media\" \"\"",
            "  GLOBAL_AUTO -1",
            "  TEMPO 120 4 4 0",
            "  PLAYRATE 1 0 0.25 4",
            f"  SAMPLERATE {self.sample_rate} 1 0",
            "  MASTER_NCH 2 2",
            "  MASTER_VOLUME 1 0 -1 -1 1",
            "  MASTER_PANMODE 3",
            "  MASTER_FX 1",
        ]

    def render(self) -> str:
        out = [line + "\n" for line in self._header_lines()]
        for track, folder_depth in self._iter_tracks_with_folder_depth():
            out.append(track.to_node(folder_depth=folder_depth).render(indent=1))
        out.append("  <EXTENSIONS\n")
        out.append("  >\n")
        out.append(">\n")
        return "".join(out)

    def _iter_tracks_with_folder_depth(self) -> list[tuple[Track, int]]:
        def flatten(track: Track) -> list[tuple[Track, int]]:
            entries: list[tuple[Track, int]] = [(track, 1 if track.children else 0)]
            for child in track.children:
                entries.extend(flatten(child))
            if track.children:
                last_track, last_depth = entries[-1]
                entries[-1] = (last_track, last_depth - 1)
            return entries

        flattened: list[tuple[Track, int]] = []
        for root_track in self.tracks:
            flattened.extend(flatten(root_track))
        return flattened

    def save(self, output_path: Path) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(self.render(), encoding="utf-8")


def guessed_item_length(audio_file: Path) -> float:
    """Estimate duration in seconds, preferring exact decoders when available."""
    if importlib.util.find_spec("soundfile"):
        import soundfile as sf

        try:
            info = sf.info(str(audio_file))
            if info.samplerate > 0:
                exact_seconds = info.frames / info.samplerate
                return math.ceil(exact_seconds * 1000) / 1000
        except Exception:
            pass

    if importlib.util.find_spec("pydub"):
        from pydub import AudioSegment

        try:
            segment = AudioSegment.from_file(str(audio_file))
            exact_seconds = len(segment) / 1000.0
            return math.ceil(exact_seconds * 1000) / 1000
        except Exception:
            pass

    if audio_file.suffix.lower() == ".wav":
        try:
            with wave.open(str(audio_file), "rb") as wav_file:
                frame_rate = wav_file.getframerate()
                if frame_rate > 0:
                    exact_seconds = wav_file.getnframes() / frame_rate
                    return math.ceil(exact_seconds * 1000) / 1000
        except wave.Error:
            pass

    size_bytes = audio_file.stat().st_size
    approx_seconds = max(0.25, min(30.0, size_bytes / (48000 * 2 * 2)))
    return math.ceil(approx_seconds * 1000) / 1000
