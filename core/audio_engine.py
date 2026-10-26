"""
Alphtech - ClickTrackAdder: Core DSP & Beat Detection Engine
SWE40006 Software Deployment and Evolution - Task 4.4 High Distinction
Author: Dang Duc Minh (105559691)
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, List, Optional, Tuple

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import soundfile as sf

try:
    import librosa
    HAS_LIBROSA = True
except ImportError:
    HAS_LIBROSA = False


@dataclass
class ClickConfig:
    """Acoustic parameters for synthesizing metronome clicks."""
    beat_freq_hz: float = 1000.0      # Normal beat click frequency (Hz)
    downbeat_freq_hz: float = 1800.0  # Downbeat (bar-start) click frequency (Hz)
    duration_ms: float = 35.0         # Duration of click pulse (ms)
    volume: float = 0.85              # Gain scale (0.0 - 1.0)
    beats_per_bar: int = 4            # Meter numerator (e.g. 4 for 4/4)


@dataclass
class DetectionConfig:
    """Beat tracking parameters for handling variable tempo tracks."""
    hop_length: int = 512
    segment_seconds: float = 14.0
    hop_seconds: float = 7.0
    core_fraction: float = 0.5
    tightness: float = 100.0
    dedupe_window_s: float = 0.07


class AudioEngine:
    """Core DSP pipeline for audio loading, beat tracking, and click synthesis."""

    def __init__(self, click_cfg: Optional[ClickConfig] = None, det_cfg: Optional[DetectionConfig] = None):
        self.click_cfg = click_cfg or ClickConfig()
        self.det_cfg = det_cfg or DetectionConfig()

    @staticmethod
    def load_audio(path: Path) -> Tuple[np.ndarray, np.ndarray, int, float]:
        """
        Loads an audio file, preserving native sample rate and duration.
        Returns: (y_mono, y_full, sample_rate, duration_seconds)
        """
        path_str = str(path)
        if HAS_LIBROSA:
            y_full, sr = librosa.load(path_str, sr=None, mono=False)
            if y_full.ndim == 1:
                y_mono = y_full
            else:
                y_mono = librosa.to_mono(y_full)
        else:
            data, sr = sf.read(path_str)
            if data.ndim == 1:
                y_mono = data.astype(np.float32)
                y_full = y_mono
            else:
                y_mono = np.mean(data, axis=1).astype(np.float32)
                y_full = data.T.astype(np.float32)

        duration = len(y_mono) / float(sr)
        return y_mono, y_full, int(sr), duration

    def detect_beats(self, y_mono: np.ndarray, sr: int, progress_cb: Optional[Callable[[float, str], None]] = None) -> Tuple[np.ndarray, np.ndarray]:
        """
        Performs segmented windowed beat detection for variable tempo tracks.
        Returns: (beat_times, downbeat_times) as NumPy arrays in seconds.
        """
        if progress_cb:
            progress_cb(0.15, "Computing onset energy strength envelope...")

        hop_length = self.det_cfg.hop_length
        duration = len(y_mono) / float(sr)

        if HAS_LIBROSA:
            onset_env = librosa.onset.onset_strength(y=y_mono, sr=sr, hop_length=hop_length)

            seg_frames = int(round(self.det_cfg.segment_seconds * sr / hop_length))
            hop_frames = int(round(self.det_cfg.hop_seconds * sr / hop_length))

            all_beats: List[float] = []
            starts = list(range(0, max(1, len(onset_env) - seg_frames // 2), hop_frames))
            if not starts:
                starts = [0]

            for i, st in enumerate(starts):
                en = min(st + seg_frames, len(onset_env))
                sub_env = onset_env[st:en]
                if len(sub_env) < 16:
                    continue

                _, sub_beats = librosa.beat.beat_track(
                    onset_envelope=sub_env,
                    sr=sr,
                    hop_length=hop_length,
                    tightness=self.det_cfg.tightness
                )

                sub_times = librosa.frames_to_time(sub_beats + st, sr=sr, hop_length=hop_length)

                w_start = librosa.frames_to_time(st, sr=sr, hop_length=hop_length)
                w_end = librosa.frames_to_time(en, sr=sr, hop_length=hop_length)
                w_len = w_end - w_start
                pad = w_len * (1.0 - self.det_cfg.core_fraction) / 2.0

                if st == 0:
                    c_start = 0.0
                else:
                    c_start = w_start + pad

                if en == len(onset_env):
                    c_end = duration
                else:
                    c_end = w_end - pad

                for t in sub_times:
                    if c_start <= t <= c_end:
                        all_beats.append(float(t))

                if progress_cb:
                    pct = 0.20 + 0.35 * (float(i + 1) / len(starts))
                    progress_cb(pct, f"Analyzing tempo variations (window {i + 1}/{len(starts)})...")

            if not all_beats:
                # Global fallback
                _, beats = librosa.beat.beat_track(onset_envelope=onset_env, sr=sr, hop_length=hop_length)
                all_beats = librosa.frames_to_time(beats, sr=sr, hop_length=hop_length).tolist()

            # De-duplicate beats closer than threshold
            all_beats.sort()
            merged: List[float] = []
            for b in all_beats:
                if not merged or (b - merged[-1]) >= self.det_cfg.dedupe_window_s:
                    merged.append(b)

            beat_times = np.array(merged, dtype=np.float64)
        else:
            # Fallback pure NumPy/SciPy onset peak detection
            frame_len = 2048
            hop = 512
            n_frames = (len(y_mono) - frame_len) // hop
            energy = np.array([np.sum(y_mono[i * hop:i * hop + frame_len] ** 2) for i in range(n_frames)])
            diff = np.maximum(0, np.diff(energy, prepend=energy[0]))
            thresh = np.mean(diff) + 1.5 * np.std(diff)
            peaks = np.where((diff[1:-1] > diff[:-2]) & (diff[1:-1] > diff[2:]) & (diff[1:-1] > thresh))[0]
            beat_times = peaks * (hop / float(sr))

        if progress_cb:
            progress_cb(0.60, f"Detected {len(beat_times)} beat positions. Estimating musical downbeats...")

        downbeat_times = self.estimate_downbeats(y_mono, sr, beat_times)
        return beat_times, downbeat_times

    def estimate_downbeats(self, y_mono: np.ndarray, sr: int, beat_times: np.ndarray) -> np.ndarray:
        """Estimates musical downbeat (first beat of bar) positions."""
        bpb = max(1, self.click_cfg.beats_per_bar)
        if len(beat_times) < bpb:
            return beat_times[:1] if len(beat_times) > 0 else np.array([])

        hop_length = self.det_cfg.hop_length
        # Measure local spectral energy in low frequencies around each beat
        energies = []
        for t in beat_times:
            idx = int(round(t * sr))
            w = y_mono[max(0, idx - 512): min(len(y_mono), idx + 512)]
            energies.append(np.sum(w ** 2) if len(w) > 0 else 0.0)

        # Find best phase offset (0 through bpb - 1)
        best_phase = 0
        best_score = -1.0
        for phase in range(bpb):
            score = sum(energies[i] for i in range(phase, len(energies), bpb))
            if score > best_score:
                best_score = score
                best_phase = phase

        return beat_times[best_phase::bpb]

    def synthesize_click(self, freq_hz: float, sr: int) -> np.ndarray:
        """Synthesizes a single sine burst click with exponential decay envelope."""
        duration_s = self.click_cfg.duration_ms / 1000.0
        n_samples = int(round(duration_s * sr))
        t = np.arange(n_samples) / float(sr)

        sine = np.sin(2.0 * np.pi * freq_hz * t)
        # Exponential decay envelope: drops to ~1% amplitude at end
        envelope = np.exp(-t / (duration_s / 4.6))
        return (sine * envelope * self.click_cfg.volume).astype(np.float32)

    def build_click_track(self, beat_times: np.ndarray, downbeat_times: np.ndarray, sr: int, total_samples: int) -> np.ndarray:
        """Renders complete multi-pitch click track across the full song duration."""
        track = np.zeros(total_samples, dtype=np.float32)

        normal_click = self.synthesize_click(self.click_cfg.beat_freq_hz, sr)
        down_click = self.synthesize_click(self.click_cfg.downbeat_freq_hz, sr)

        down_set = set(np.round(downbeat_times, 3))

        for t in beat_times:
            start = int(round(t * sr))
            if start >= total_samples:
                break
            is_down = round(float(t), 3) in down_set
            click = down_click if is_down else normal_click
            end = min(total_samples, start + len(click))
            chunk_len = end - start
            track[start:end] += click[:chunk_len]

        # Prevent digital clipping
        peak = np.max(np.abs(track))
        if peak > 1.0:
            track /= peak
        return track

    def render_plot(self, y_mono: np.ndarray, sr: int, beat_times: np.ndarray, downbeat_times: np.ndarray, out_path: Path, max_seconds: float = 60.0) -> None:
        """Renders an audio waveform verification plot with beat and downbeat markers."""
        duration = len(y_mono) / float(sr)
        view_seconds = min(duration, max_seconds) if max_seconds > 0 else duration
        n_view = int(round(view_seconds * sr))

        y_view = y_mono[:n_view]
        times = np.arange(len(y_view)) / float(sr)

        fig, ax = plt.subplots(figsize=(14, 4.5), facecolor="#0f172a")
        ax.set_facecolor("#1e293b")

        ax.plot(times, y_view, color="#38bdf8", linewidth=0.5, alpha=0.8, label="Input Waveform")

        beats_view = beat_times[beat_times <= view_seconds]
        downs_view = downbeat_times[downbeat_times <= view_seconds]

        ax.vlines(beats_view, ymin=-1.0, ymax=1.0, color="#f59e0b", linewidth=0.8, alpha=0.7, label=f"Beats ({len(beat_times)} total)")
        ax.vlines(downs_view, ymin=-1.0, ymax=1.0, color="#ef4444", linewidth=1.5, alpha=0.9, label=f"Downbeats ({len(downbeat_times)} total)")

        ax.set_xlim(0, view_seconds)
        ax.set_ylim(-1.05, 1.05)
        ax.set_xlabel("Time (seconds)", color="#94a3b8", fontsize=10)
        ax.set_ylabel("Amplitude", color="#94a3b8", fontsize=10)
        ax.tick_params(colors="#94a3b8")
        ax.grid(True, color="#334155", linestyle="--", alpha=0.5)

        title = "Alphtech - ClickTrackAdder Analysis: Waveform with Detected Beats"
        if duration > view_seconds:
            title += f" (First {view_seconds:.0f}s of {duration:.1f}s)"
        ax.set_title(title, color="#f8fafc", fontsize=12, fontweight="bold")

        legend = ax.legend(loc="upper right", facecolor="#0f172a", edgecolor="#334155")
        for text in legend.get_texts():
            text.set_color("#f8fafc")

        fig.tight_layout()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(str(out_path), dpi=140, facecolor=fig.get_facecolor(), edgecolor="none")
        plt.close(fig)

    def process(
        self,
        input_path: Path,
        output_click_path: Optional[Path] = None,
        output_mix_path: Optional[Path] = None,
        output_plot_path: Optional[Path] = None,
        output_txt_path: Optional[Path] = None,
        progress_cb: Optional[Callable[[float, str], None]] = None
    ) -> dict:
        """Executes full end-to-end processing pipeline."""
        if progress_cb:
            progress_cb(0.05, f"Loading audio file: {input_path.name}...")

        y_mono, y_full, sr, duration = self.load_audio(input_path)
        total_samples = len(y_mono)

        beat_times, downbeat_times = self.detect_beats(y_mono, sr, progress_cb)

        # Compute BPM statistics
        if len(beat_times) > 1:
            ibi = np.diff(beat_times)
            bpm_series = 60.0 / ibi
            min_bpm = float(np.min(bpm_series))
            max_bpm = float(np.max(bpm_series))
            median_bpm = float(np.median(bpm_series))
        else:
            min_bpm = max_bpm = median_bpm = 0.0

        if progress_cb:
            progress_cb(0.70, "Synthesizing metronome click track...")

        click_track = self.build_click_track(beat_times, downbeat_times, sr, total_samples)

        # 1. Isolated Click Track
        if output_click_path is None:
            output_click_path = input_path.with_name(f"{input_path.stem}_click.wav")
        output_click_path.parent.mkdir(parents=True, exist_ok=True)
        sf.write(str(output_click_path), click_track, sr, subtype="PCM_16")

        # 2. Reference Mixed Track
        if output_mix_path:
            if progress_cb:
                progress_cb(0.80, "Rendering reference mixed audio...")
            normalized_song = y_mono / (np.max(np.abs(y_mono)) + 1e-9) * 0.75
            mix = normalized_song + click_track
            peak = np.max(np.abs(mix))
            if peak > 1.0:
                mix /= peak
            output_mix_path.parent.mkdir(parents=True, exist_ok=True)
            sf.write(str(output_mix_path), mix, sr, subtype="PCM_16")

        # 3. Waveform Verification Plot
        if output_plot_path:
            if progress_cb:
                progress_cb(0.90, "Rendering waveform beat marker plot...")
            self.render_plot(y_mono, sr, beat_times, downbeat_times, output_plot_path)

        # 4. Beat Timestamps Text
        if output_txt_path:
            output_txt_path.parent.mkdir(parents=True, exist_ok=True)
            down_set = set(np.round(downbeat_times, 3))
            with open(output_txt_path, "w", encoding="utf-8") as f:
                f.write(f"# Alphtech - ClickTrackAdder Beat Export\n")
                f.write(f"# Source: {input_path.name}\n")
                f.write(f"# Sample Rate: {sr} Hz | Duration: {duration:.2f} s\n")
                f.write(f"# Median BPM: {median_bpm:.1f} (Min: {min_bpm:.1f}, Max: {max_bpm:.1f})\n")
                f.write("# time_seconds,is_downbeat\n")
                for t in beat_times:
                    is_down = round(float(t), 3) in down_set
                    f.write(f"{t:.4f},{int(is_down)}\n")

        if progress_cb:
            progress_cb(1.0, "Processing complete!")

        return {
            "sample_rate": sr,
            "duration": duration,
            "beat_count": len(beat_times),
            "downbeat_count": len(downbeat_times),
            "min_bpm": min_bpm,
            "max_bpm": max_bpm,
            "median_bpm": median_bpm,
            "click_file": str(output_click_path),
            "mix_file": str(output_mix_path) if output_mix_path else None,
            "plot_file": str(output_plot_path) if output_plot_path else None,
            "txt_file": str(output_txt_path) if output_txt_path else None,
        }
