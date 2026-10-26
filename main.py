"""
Alphtech - ClickTrackAdder (Alphtech-CTA)
SWE40006 Software Deployment and Evolution - Task 4.4 High Distinction Tier
Author: Dang Duc Minh (Student ID: 105559691)

Main Application Launcher supporting:
1. Native Desktop GUI (Tkinter)
2. Interactive Terminal Console Menu (Docker-compatible headless mode)
3. Automated Batch Processing
"""

import argparse
import os
import platform
import socket
import sys
from pathlib import Path

from core.audio_engine import AudioEngine, ClickConfig, DetectionConfig

ASCII_BANNER = r"""
    ___    __       __     __            __       ______________  ___
   /   |  / /___   / /_   / /____  _____/ /_     / ____/_  __/   |/   |
  / /| | / / __ \ / __ \ / __/ _ \/ ___/ __ \   / /     / / / /| | /| |
 / ___ |/ / /_/ // / / // /_/  __/ /__/ / / /  / /___  / / / ___ |/ | |
/_/  |_/_/ .___//_/ /_/ \__/\___/\___/_/ /_/   \____/ /_/ /_/  |_/  |_|
        /_/       CLICK TRACK ADDER - TASK 4.4 HIGH DISTINCTION
"""


def run_cli_interactive():
    """Interactive console prompt mode for Docker or headless terminal execution."""
    click_cfg = ClickConfig()
    engine = AudioEngine(click_cfg=click_cfg)

    app_dir = Path(__file__).resolve().parent
    bundled_demo = app_dir / "sample_audio" / "demo_song.wav"

    while True:
        print("\n" + ASCII_BANNER)
        print("  Non-Web Application Mode (Docker Containerized)")
        print(f"  Container Host: {socket.gethostname()} | Python: {platform.python_version()}")
        print(f"  Student Author: Dang Duc Minh (105559691)")
        print("-" * 65)
        print("  [1] Run Beat Detection & Click Generator (Bundled Demo)")
        print("  [2] Process a Custom Audio File Path")
        print("  [3] View / Configure Click Parameters")
        print("  [4] Container & Engine Diagnostics")
        print("  [5] Exit Application")
        print("-" * 65)

        try:
            choice = input("Select an option [1-5]: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting application. Goodbye!")
            return 0

        if choice == "1":
            print(f"\nLoading bundled demo: {bundled_demo}")
            if not bundled_demo.exists():
                print(f"Demo file not found at {bundled_demo}, generating on the fly...")
                from sample_audio.generate_sample import create_demo_audio
                create_demo_audio(bundled_demo)

            run_pipeline_for_file(engine, bundled_demo)

        elif choice == "2":
            path_str = input("\nEnter path to audio file (e.g. /data/song.wav): ").strip()
            if not path_str:
                print("No path entered.")
                continue
            custom_path = Path(path_str)
            if not custom_path.exists():
                print(f"Error: File not found: {custom_path}")
                continue
            run_pipeline_for_file(engine, custom_path)

        elif choice == "3":
            print("\n--- Current Click Configuration ---")
            print(f"  Normal Beat Pitch:     {click_cfg.beat_freq_hz} Hz")
            print(f"  Downbeat Pitch:        {click_cfg.downbeat_freq_hz} Hz")
            print(f"  Click Pulse Duration:  {click_cfg.duration_ms} ms")
            print(f"  Gain Volume:           {click_cfg.volume}")
            print(f"  Beats per Bar (Meter): {click_cfg.beats_per_bar}")
            print("-" * 40)
            update = input("Change parameters? (y/n) [n]: ").strip().lower()
            if update == "y":
                try:
                    bpb = input(f"Beats per bar [{click_cfg.beats_per_bar}]: ").strip()
                    if bpb:
                        click_cfg.beats_per_bar = int(bpb)
                    vol = input(f"Volume 0.1-1.0 [{click_cfg.volume}]: ").strip()
                    if vol:
                        click_cfg.volume = float(vol)
                    print("Parameters updated!")
                except ValueError as e:
                    print(f"Invalid input: {e}")

        elif choice == "4":
            print("\n--- System & Container Diagnostics ---")
            print(f"  Hostname:       {socket.gethostname()}")
            print(f"  OS Platform:    {platform.platform()}")
            print(f"  Python Runtime: {sys.version}")
            print(f"  App Directory:  {app_dir}")
            print(f"  Bundled Audio:  {'Available' if bundled_demo.exists() else 'Not found'}")
            print(f"  Status:         Operational (High Distinction Tier)")
            print("-" * 40)
            input("Press Enter to return to main menu...")

        elif choice == "5":
            print("\nShutting down Alphtech - ClickTrackAdder. Goodbye!")
            return 0

        else:
            print("Invalid option. Please choose 1, 2, 3, 4, or 5.")


def run_pipeline_for_file(engine: AudioEngine, input_path: Path):
    """Executes the DSP pipeline and displays output metrics."""
    out_click = input_path.with_name(f"{input_path.stem}_click.wav")
    out_mix = input_path.with_name(f"{input_path.stem}_mixed.wav")
    out_plot = input_path.with_name(f"{input_path.stem}_click_plot.png")
    out_txt = input_path.with_name(f"{input_path.stem}.beats.txt")

    print("\nProcessing audio pipeline...")
    def console_cb(pct, msg):
        print(f"  [{int(pct * 100):3d}%] {msg}")

    try:
        results = engine.process(
            input_path,
            output_click_path=out_click,
            output_mix_path=out_mix,
            output_plot_path=out_plot,
            output_txt_path=out_txt,
            progress_cb=console_cb
        )

        print("\n" + "=" * 65)
        print("PIPELINE EXECUTION COMPLETED")
        print("=" * 65)
        print(f"  Input File:      {input_path.name}")
        print(f"  Sample Rate:     {results['sample_rate']} Hz")
        print(f"  Duration:        {results['duration']:.2f} seconds")
        print(f"  Detected Beats:  {results['beat_count']}")
        print(f"  Downbeats:       {results['downbeat_count']}")
        print(f"  Tempo Range:     {results['min_bpm']:.1f} - {results['max_bpm']:.1f} BPM (Median: {results['median_bpm']:.1f})")
        print(f"  Click Track:     {results['click_file']}")
        if results['mix_file']:
            print(f"  Mixed Reference: {results['mix_file']}")
        if results['plot_file']:
            print(f"  Waveform Plot:   {results['plot_file']}")
        if results['txt_file']:
            print(f"  Timestamps:      {results['txt_file']}")
        print("=" * 65)
    except Exception as e:
        print(f"Error during audio processing: {e}")

    input("\nPress Enter to return to main menu...")


def run_cli_batch(args):
    """Batch processing mode for automated CLI / Docker runs."""
    print(ASCII_BANNER)
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: Input audio file not found: {input_path}")
        return 1

    click_cfg = ClickConfig(
        beat_freq_hz=args.beat_freq,
        downbeat_freq_hz=args.downbeat_freq,
        duration_ms=args.duration,
        volume=args.volume,
        beats_per_bar=args.beats_per_bar
    )
    engine = AudioEngine(click_cfg=click_cfg)

    out_click = Path(args.output) if args.output else input_path.with_name(f"{input_path.stem}_click.wav")
    out_mix = input_path.with_name(f"{input_path.stem}_mixed.wav") if args.mix else None
    out_plot = input_path.with_name(f"{input_path.stem}_click_plot.png") if not args.no_plot else None
    out_txt = input_path.with_name(f"{input_path.stem}.beats.txt")

    print(f"Loading and analyzing: {input_path}")
    def progress_cb(pct, msg):
        print(f"[{int(pct * 100):3d}%] {msg}")

    results = engine.process(
        input_path,
        output_click_path=out_click,
        output_mix_path=out_mix,
        output_plot_path=out_plot,
        output_txt_path=out_txt,
        progress_cb=progress_cb
    )

    print("\nSummary:")
    print(f"  Beats Detected: {results['beat_count']} (Median BPM: {results['median_bpm']:.1f})")
    print(f"  Click Audio:    {results['click_file']}")
    if results['mix_file']:
        print(f"  Mixed Audio:    {results['mix_file']}")
    return 0


def main():
    parser = argparse.ArgumentParser(description="Alphtech - ClickTrackAdder")
    parser.add_argument("input", nargs="?", default=None, help="Input audio file path (WAV/MP3/FLAC/OGG)")
    parser.add_argument("-o", "--output", default=None, help="Output click track WAV path")
    parser.add_argument("--mix", action="store_true", help="Also export mixed song + click reference audio")
    parser.add_argument("--no-plot", action="store_true", help="Skip generating waveform plot PNG")
    parser.add_argument("--cli", action="store_true", help="Force command-line interface mode")
    parser.add_argument("--beat-freq", type=float, default=1000.0, help="Frequency of beat click in Hz")
    parser.add_argument("--downbeat-freq", type=float, default=1800.0, help="Frequency of downbeat click in Hz")
    parser.add_argument("--duration", type=float, default=35.0, help="Click pulse duration in ms")
    parser.add_argument("--volume", type=float, default=0.85, help="Click volume scale (0.0 - 1.0)")
    parser.add_argument("--beats-per-bar", type=int, default=4, help="Time signature numerator (beats per bar)")

    args = parser.parse_args()

    # 1. If explicit input file given -> run CLI batch
    if args.input:
        return run_cli_batch(args)

    # 2. If --cli flag given -> run interactive console
    if args.cli:
        return run_cli_interactive()

    # 3. Check for graphical display environment (Tkinter)
    is_headless = False
    if sys.platform.startswith("linux") and "DISPLAY" not in os.environ and "WAYLAND_DISPLAY" not in os.environ:
        is_headless = True

    if not is_headless:
        try:
            from gui import launch_gui
            launch_gui()
            return 0
        except Exception as e:
            print(f"Could not initialize graphical display ({e}). Falling back to interactive CLI...")
            return run_cli_interactive()
    else:
        # Inside Docker or headless container environment
        return run_cli_interactive()


if __name__ == "__main__":
    sys.exit(main())
