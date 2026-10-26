"""
Alphtech - ClickTrackAdder: Desktop GUI Interface
SWE40006 Software Deployment and Evolution - Task 4.4 High Distinction
Author: Dang Duc Minh (105559691)
"""

import os
import sys
import threading
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText

from core.audio_engine import AudioEngine, ClickConfig, DetectionConfig


class AlphtechCTAGUI(tk.Tk):
    """Modern dark-themed desktop application window for Alphtech ClickTrackAdder."""

    def __init__(self):
        super().__init__()

        self.title("Alphtech - ClickTrackAdder")
        self.geometry("820x760")
        self.minsize(760, 680)
        self.configure(bg="#0f172a")

        self.engine = AudioEngine()
        self.current_file = None
        self.is_processing = False

        self.setup_styles()
        self.build_ui()

    def setup_styles(self):
        """Configure modern dark TTK styles."""
        self.style = ttk.Style(self)
        self.style.theme_use("clam")

        # Palette
        self.colors = {
            "bg": "#0f172a",
            "card_bg": "#1e293b",
            "border": "#334155",
            "primary": "#2563eb",
            "primary_hover": "#1d4ed8",
            "text": "#f8fafc",
            "text_muted": "#94a3b8",
            "accent": "#38bdf8",
            "success": "#10b981",
        }

        self.style.configure(".", background=self.colors["bg"], foreground=self.colors["text"])
        self.style.configure("TFrame", background=self.colors["bg"])
        self.style.configure("Card.TFrame", background=self.colors["card_bg"], relief="flat")
        self.style.configure("TLabel", background=self.colors["bg"], foreground=self.colors["text"], font=("Segoe UI", 10))
        self.style.configure("Card.TLabel", background=self.colors["card_bg"], foreground=self.colors["text"], font=("Segoe UI", 10))
        self.style.configure("Header.TLabel", background=self.colors["bg"], foreground=self.colors["accent"], font=("Segoe UI", 18, "bold"))
        self.style.configure("SubHeader.TLabel", background=self.colors["bg"], foreground=self.colors["text_muted"], font=("Segoe UI", 9))
        self.style.configure("CardTitle.TLabel", background=self.colors["card_bg"], foreground=self.colors["accent"], font=("Segoe UI", 11, "bold"))

        # Buttons
        self.style.configure(
            "Primary.TButton",
            background=self.colors["primary"],
            foreground="#ffffff",
            font=("Segoe UI", 11, "bold"),
            padding=(16, 8),
            borderwidth=0
        )
        self.style.map("Primary.TButton", background=[("active", self.colors["primary_hover"])])

        self.style.configure(
            "Secondary.TButton",
            background="#334155",
            foreground="#ffffff",
            font=("Segoe UI", 9, "bold"),
            padding=(10, 5),
            borderwidth=0
        )
        self.style.map("Secondary.TButton", background=[("active", "#475569")])

        # Checkbuttons
        self.style.configure(
            "Card.TCheckbutton",
            background=self.colors["card_bg"],
            foreground=self.colors["text"],
            font=("Segoe UI", 9)
        )

        # Progressbar
        self.style.configure("Horizontal.TProgressbar", background=self.colors["accent"], troughcolor="#0f172a")

    def build_ui(self):
        """Construct the UI layout."""
        # Top Header Banner
        header_frame = ttk.Frame(self, padding=(24, 16, 24, 8))
        header_frame.pack(fill="x")

        ttk.Label(header_frame, text="Alphtech - ClickTrackAdder", style="Header.TLabel").pack(anchor="w")
        ttk.Label(
            header_frame,
            text="High-Precision Beat Detection & Synchronized Metronome Generator",
            style="SubHeader.TLabel"
        ).pack(anchor="w", pady=(2, 0))

        # Main Scrollable / Padded Container
        container = ttk.Frame(self, padding=(24, 8, 24, 16))
        container.pack(fill="both", expand=True)

        # 1. File Selection Card
        self.build_file_card(container)

        # 2. Click Settings & Output Options Grid
        middle_grid = ttk.Frame(container)
        middle_grid.pack(fill="x", pady=10)
        middle_grid.columnconfigure(0, weight=1)
        middle_grid.columnconfigure(1, weight=1)

        self.build_settings_card(middle_grid)
        self.build_options_card(middle_grid)

        # 3. Actions & Progress Bar Card
        self.build_action_card(container)

        # 4. Console Log Card
        self.build_log_card(container)

    def build_file_card(self, parent):
        card = ttk.Frame(parent, style="Card.TFrame", padding=14)
        card.pack(fill="x", pady=6)

        ttk.Label(card, text="Audio Source Input", style="CardTitle.TLabel").pack(anchor="w", pady=(0, 6))

        row = ttk.Frame(card, style="Card.TFrame")
        row.pack(fill="x")

        self.file_entry_var = tk.StringVar()
        self.file_entry = tk.Entry(
            row,
            textvariable=self.file_entry_var,
            bg="#0f172a",
            fg="#f8fafc",
            insertbackground="#f8fafc",
            relief="solid",
            bd=1,
            font=("Segoe UI", 10)
        )
        self.file_entry.pack(side="left", fill="x", expand=True, ipady=4, padx=(0, 10))

        browse_btn = ttk.Button(row, text="Browse Audio...", style="Secondary.TButton", command=self.browse_file)
        browse_btn.pack(side="right")

        self.file_info_var = tk.StringVar(value="Ready. Select any WAV, MP3, FLAC, or OGG audio file.")
        info_label = ttk.Label(card, textvariable=self.file_info_var, style="Card.TLabel", font=("Segoe UI", 9))
        info_label.configure(foreground=self.colors["text_muted"])
        info_label.pack(anchor="w", pady=(6, 0))

    def build_settings_card(self, parent):
        card = ttk.Frame(parent, style="Card.TFrame", padding=14)
        card.grid(row=0, column=0, sticky="nsew", padx=(0, 6))

        ttk.Label(card, text="Click Synthesis Configuration", style="CardTitle.TLabel").pack(anchor="w", pady=(0, 8))

        form = ttk.Frame(card, style="Card.TFrame")
        form.pack(fill="x")

        # Beat Pitch
        ttk.Label(form, text="Normal Beat Pitch (Hz):", style="Card.TLabel").grid(row=0, column=0, sticky="w", pady=4)
        self.beat_pitch_var = tk.StringVar(value="1000")
        tk.Entry(form, textvariable=self.beat_pitch_var, width=8, bg="#0f172a", fg="#ffffff", insertbackground="#fff", relief="solid", bd=1).grid(row=0, column=1, sticky="e", pady=4)

        # Downbeat Pitch
        ttk.Label(form, text="Downbeat Pitch (Hz):", style="Card.TLabel").grid(row=1, column=0, sticky="w", pady=4)
        self.downbeat_pitch_var = tk.StringVar(value="1800")
        tk.Entry(form, textvariable=self.downbeat_pitch_var, width=8, bg="#0f172a", fg="#ffffff", insertbackground="#fff", relief="solid", bd=1).grid(row=1, column=1, sticky="e", pady=4)

        # Click Duration
        ttk.Label(form, text="Click Duration (ms):", style="Card.TLabel").grid(row=2, column=0, sticky="w", pady=4)
        self.duration_var = tk.StringVar(value="35")
        tk.Entry(form, textvariable=self.duration_var, width=8, bg="#0f172a", fg="#ffffff", insertbackground="#fff", relief="solid", bd=1).grid(row=2, column=1, sticky="e", pady=4)

        # Beats per bar
        ttk.Label(form, text="Beats per Bar (Numerator):", style="Card.TLabel").grid(row=3, column=0, sticky="w", pady=4)
        self.bpb_var = tk.StringVar(value="4")
        tk.Spinbox(form, from_=1, to=16, textvariable=self.bpb_var, width=6, bg="#0f172a", fg="#ffffff", buttonbackground="#334155").grid(row=3, column=1, sticky="e", pady=4)

        # Volume slider
        ttk.Label(form, text="Click Volume Gain:", style="Card.TLabel").grid(row=4, column=0, sticky="w", pady=(6, 2))
        self.volume_var = tk.DoubleVar(value=0.85)
        scale = tk.Scale(form, variable=self.volume_var, from_=0.1, to=1.0, resolution=0.05, orient="horizontal", bg="#1e293b", fg="#94a3b8", troughcolor="#0f172a", highlightthickness=0, bd=0)
        scale.grid(row=4, column=1, sticky="e", pady=(6, 2))

    def build_options_card(self, parent):
        card = ttk.Frame(parent, style="Card.TFrame", padding=14)
        card.grid(row=0, column=1, sticky="nsew", padx=(6, 0))

        ttk.Label(card, text="Output Generation Options", style="CardTitle.TLabel").pack(anchor="w", pady=(0, 8))

        self.opt_click_track = tk.BooleanVar(value=True)
        self.opt_mixed_track = tk.BooleanVar(value=True)
        self.opt_plot_waveform = tk.BooleanVar(value=True)
        self.opt_export_txt = tk.BooleanVar(value=True)

        ttk.Checkbutton(card, text="Export Isolated Click (*_click.wav)", variable=self.opt_click_track, style="Card.TCheckbutton").pack(anchor="w", pady=4)
        ttk.Checkbutton(card, text="Export Song + Click Mix (*_mixed.wav)", variable=self.opt_mixed_track, style="Card.TCheckbutton").pack(anchor="w", pady=4)
        ttk.Checkbutton(card, text="Export Waveform Beat Plot (*.png)", variable=self.opt_plot_waveform, style="Card.TCheckbutton").pack(anchor="w", pady=4)
        ttk.Checkbutton(card, text="Export Beat Timestamps (*.beats.txt)", variable=self.opt_export_txt, style="Card.TCheckbutton").pack(anchor="w", pady=4)

    def build_action_card(self, parent):
        card = ttk.Frame(parent, style="Card.TFrame", padding=14)
        card.pack(fill="x", pady=6)

        btn_row = ttk.Frame(card, style="Card.TFrame")
        btn_row.pack(fill="x", pady=(0, 10))

        self.generate_btn = ttk.Button(btn_row, text="GENERATE CLICK TRACK", style="Primary.TButton", command=self.start_processing)
        self.generate_btn.pack(side="left", fill="x", expand=True, padx=(0, 8))

        reset_btn = ttk.Button(btn_row, text="Reset Defaults", style="Secondary.TButton", command=self.reset_defaults)
        reset_btn.pack(side="right")

        self.progress_var = tk.DoubleVar(value=0.0)
        self.progress_bar = ttk.Progressbar(card, variable=self.progress_var, maximum=1.0, style="Horizontal.TProgressbar")
        self.progress_bar.pack(fill="x", pady=(0, 4))

        self.status_label_var = tk.StringVar(value="Status: Idle")
        status_label = ttk.Label(card, textvariable=self.status_label_var, style="Card.TLabel")
        status_label.configure(foreground=self.colors["accent"], font=("Segoe UI", 9, "bold"))
        status_label.pack(anchor="w")

    def build_log_card(self, parent):
        card = ttk.Frame(parent, style="Card.TFrame", padding=14)
        card.pack(fill="both", expand=True, pady=6)

        ttk.Label(card, text="Execution Diagnostic Log", style="CardTitle.TLabel").pack(anchor="w", pady=(0, 4))

        self.log_text = ScrolledText(
            card,
            height=7,
            bg="#0f172a",
            fg="#94a3b8",
            insertbackground="#ffffff",
            relief="solid",
            bd=1,
            font=("Consolas", 9)
        )
        self.log_text.pack(fill="both", expand=True)

        self.log("Alphtech - ClickTrackAdder GUI initialized.")
        self.log("Engine loaded: segmented beat tracking & downbeat acoustic synthesis.")

    def log(self, message: str):
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)

    def browse_file(self):
        filetypes = [
            ("Audio Files", "*.wav *.mp3 *.flac *.ogg *.m4a"),
            ("WAV Files", "*.wav"),
            ("All Files", "*.*")
        ]
        chosen = filedialog.askopenfilename(title="Select Song Audio File", filetypes=filetypes)
        if chosen:
            self.file_entry_var.set(chosen)
            self.inspect_file(Path(chosen))

    def inspect_file(self, path: Path):
        try:
            self.current_file = path
            _, _, sr, duration = AudioEngine.load_audio(path)
            mins = int(duration // 60)
            secs = int(duration % 60)
            info_str = f"Loaded: {path.name} | Sample Rate: {sr} Hz | Duration: {mins}m {secs:02d}s"
            self.file_info_var.set(info_str)
            self.log(f"Selected audio: {path.resolve()}")
            self.log(f"  {info_str}")
        except Exception as e:
            self.file_info_var.set(f"Error inspecting audio: {e}")
            self.log(f"Error loading {path}: {e}")

    def reset_defaults(self):
        self.beat_pitch_var.set("1000")
        self.downbeat_pitch_var.set("1800")
        self.duration_var.set("35")
        self.bpb_var.set("4")
        self.volume_var.set(0.85)
        self.opt_click_track.set(True)
        self.opt_mixed_track.set(True)
        self.opt_plot_waveform.set(True)
        self.opt_export_txt.set(True)
        self.log("Configuration parameters reset to defaults.")

    def start_processing(self):
        if self.is_processing:
            return

        file_str = self.file_entry_var.get().strip()
        if not file_str:
            messagebox.showwarning("No File", "Please select an audio file first!")
            return

        path = Path(file_str)
        if not path.exists():
            messagebox.showerror("File Not Found", f"Audio file does not exist: {path}")
            return

        try:
            click_cfg = ClickConfig(
                beat_freq_hz=float(self.beat_pitch_var.get()),
                downbeat_freq_hz=float(self.downbeat_pitch_var.get()),
                duration_ms=float(self.duration_var.get()),
                volume=float(self.volume_var.get()),
                beats_per_bar=int(self.bpb_var.get())
            )
        except ValueError as e:
            messagebox.showerror("Invalid Input", f"Configuration parsing error: {e}")
            return

        self.engine.click_cfg = click_cfg
        self.is_processing = True
        self.generate_btn.configure(state="disabled")

        thread = threading.Thread(target=self._run_pipeline_worker, args=(path,), daemon=True)
        thread.start()

    def _run_pipeline_worker(self, path: Path):
        def progress_cb(pct: float, message: str):
            self.after(0, lambda: self._update_progress(pct, message))

        try:
            self.log(f"=== Beginning Click Track Generation: {path.name} ===")

            out_click = path.with_name(f"{path.stem}_click.wav") if self.opt_click_track.get() else None
            out_mix = path.with_name(f"{path.stem}_mixed.wav") if self.opt_mixed_track.get() else None
            out_plot = path.with_name(f"{path.stem}_click_plot.png") if self.opt_plot_waveform.get() else None
            out_txt = path.with_name(f"{path.stem}.beats.txt") if self.opt_export_txt.get() else None

            results = self.engine.process(
                path,
                output_click_path=out_click,
                output_mix_path=out_mix,
                output_plot_path=out_plot,
                output_txt_path=out_txt,
                progress_cb=progress_cb
            )

            self.after(0, lambda: self._on_success(results))
        except Exception as e:
            self.after(0, lambda: self._on_error(str(e)))

    def _update_progress(self, pct: float, message: str):
        self.progress_var.set(pct)
        self.status_label_var.set(f"Status: {message}")
        self.log(f"[{int(pct * 100)}%] {message}")

    def _on_success(self, results: dict):
        self.is_processing = False
        self.generate_btn.configure(state="normal")
        self.progress_var.set(1.0)
        self.status_label_var.set("Status: Completed successfully!")

        self.log("--- Generation Summary ---")
        self.log(f"  Sample Rate: {results['sample_rate']} Hz | Duration: {results['duration']:.2f} s")
        self.log(f"  Detected Beats: {results['beat_count']} | Downbeats: {results['downbeat_count']}")
        self.log(f"  Tempo Range: {results['min_bpm']:.1f} - {results['max_bpm']:.1f} BPM (Median: {results['median_bpm']:.1f})")
        if results['click_file']:
            self.log(f"  Click Track: {results['click_file']}")
        if results['mix_file']:
            self.log(f"  Mixed Track: {results['mix_file']}")
        if results['plot_file']:
            self.log(f"  Plot Image:  {results['plot_file']}")
        if results['txt_file']:
            self.log(f"  Timestamps:  {results['txt_file']}")
        self.log("==================================================")

        messagebox.showinfo(
            "Generation Complete",
            f"Click track successfully generated!\n\n"
            f"Beats: {results['beat_count']} | Median BPM: {results['median_bpm']:.1f}\n"
            f"Saved to: {Path(results['click_file']).name}"
        )

    def _on_error(self, err_msg: str):
        self.is_processing = False
        self.generate_btn.configure(state="normal")
        self.status_label_var.set("Status: Error encountered.")
        self.log(f"ERROR: {err_msg}")
        messagebox.showerror("Processing Failed", f"An error occurred during audio processing:\n{err_msg}")


def launch_gui():
    app = AlphtechCTAGUI()
    app.mainloop()


if __name__ == "__main__":
    launch_gui()
