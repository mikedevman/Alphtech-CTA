# Alphtech - ClickTrackAdder (`Alphtech-CTA`)

**SWE40006 Software Deployment and Evolution - Task 4.4 High Distinction Tier**  
**Author:** Dang Duc Minh (Student ID: 105559691)

---

## 1. Overview
**Alphtech - ClickTrackAdder** is a non-web desktop audio engineering and beat detection utility. It analyzes audio recordings (with support for variable tempo songs), detects beat and downbeat locations, synthesizes high-precision metronome click tracks, renders waveform analysis verification plots, and exports audio stems.

---

## 2. Running the Desktop GUI (Host Machine)
To launch the modern dark-themed desktop application:

```powershell
cd C:\Users\Admin\Documents\Alphtech-CTA
python main.py
```

### Features in Desktop GUI:
1. **Audio Input**: Select any `.wav`, `.mp3`, `.flac`, or `.ogg` file.
2. **Click Configuration**: Customize normal beat frequency (default 1000 Hz), downbeat frequency (default 1800 Hz), duration (35 ms), volume gain, and beats per bar (meter).
3. **Multi-Track Export**: Output isolated clicks (`_click.wav`), reference mix (`_mixed.wav`), waveform marker plot (`.png`), and beat timestamps (`.beats.txt`).
4. **Asynchronous Execution**: UI runs on a separate worker thread so the interface remains smooth and responsive.

---

## 3. Running inside Docker (Task 4.4 HD)

### Build the Docker Image:
```bash
cd C:\Users\Admin\Documents\Alphtech-CTA
docker build -t alphtech-cta .
```

### Run Interactively inside Container:
```bash
docker run -it --rm -v "C:\Users\Admin\Documents\Alphtech-CTA\sample_audio:/data" alphtech-cta
```
*Prompts interactively for the file (`/data/demo_song.wav`) and parameters, and executes the complete pipeline inside the Docker container.*

### Run Automated Batch Processing in Container:
```bash
docker run --rm -v "C:\Users\Admin\Documents\Alphtech-CTA\sample_audio:/data" alphtech-cta /data/demo_song.wav --mix
```
