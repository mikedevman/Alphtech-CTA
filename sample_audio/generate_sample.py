"""
Generates a short synthetic demo audio track with clear beat accents for testing.
"""

from pathlib import Path
import numpy as np
import soundfile as sf

def create_demo_audio(out_path: Path, duration_s: float = 8.0, bpm: float = 120.0, sr: int = 44100):
    total_samples = int(duration_s * sr)
    audio = np.zeros(total_samples, dtype=np.float32)

    beat_interval_s = 60.0 / bpm
    beats = np.arange(0, duration_s, beat_interval_s)

    for i, t in enumerate(beats):
        start_idx = int(t * sr)
        # Synthesize a bass/kick drum pulse
        freq = 60.0 if (i % 4 == 0) else 150.0
        decay = 0.25 if (i % 4 == 0) else 0.12
        dur_samples = int(decay * sr)
        t_pulse = np.arange(dur_samples) / float(sr)
        pulse = np.sin(2 * np.pi * freq * t_pulse) * np.exp(-t_pulse / (decay / 4.0))

        end_idx = min(total_samples, start_idx + len(pulse))
        audio[start_idx:end_idx] += pulse[:end_idx - start_idx] * 0.7

    # Add gentle ambient chord pad
    t_full = np.arange(total_samples) / float(sr)
    pad = 0.15 * (np.sin(2 * np.pi * 220.0 * t_full) + np.sin(2 * np.pi * 277.18 * t_full) + np.sin(2 * np.pi * 329.63 * t_full))
    audio += pad

    # Normalize
    peak = np.max(np.abs(audio))
    if peak > 0:
        audio = audio / peak * 0.85

    out_path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(out_path), audio, sr, subtype="PCM_16")
    print(f"Created demo audio track: {out_path} ({duration_s}s, {bpm} BPM)")

if __name__ == "__main__":
    demo_file = Path(__file__).parent / "demo_song.wav"
    create_demo_audio(demo_file)
