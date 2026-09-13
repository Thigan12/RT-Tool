# RT Tool — PUBG Mobile GameLoop Pro Optimizer

<div align="center">

![Platform](https://img.shields.io/badge/Platform-Windows-0078D6?style=for-the-badge&logo=windows)
![Python](https://img.shields.io/badge/Python-3.11%20|%203.12%20|%203.13-3776AB?style=for-the-badge&logo=python)
![Framework](https://img.shields.io/badge/GUI-PyQt6-41CD52?style=for-the-badge&logo=qt)
![Target](https://img.shields.io/badge/Game-PUBG%20Mobile%20%C2%B7%20GameLoop-FF6B00?style=for-the-badge)

**A high-performance standalone Windows desktop application designed to eliminate input lag, unlock maximum frame rates, and bypass hardware throttling for PUBG Mobile on the Tencent GameLoop Android emulator.**

</div>

---

## ⚡ Key Features

### 🚀 1. Launch Hub
- **Auto-Detection**: Scans Windows Registry and filesystem for GameLoop installations (`AndroidProcess.exe`, `AppMarket.exe`, `TxGameAssistant`).
- **One-Click Launch**: Launches and embeds GameLoop with customized process priorities and affinity optimizations.
- **Hardware Telemetry**: Live circular ring gauges monitoring CPU, GPU, and RAM usage in real time.

### ⚡ 2. Performance & Hardware Engine
- **Dedicated GPU Prioritization**: Locks GameLoop onto discrete NVIDIA/AMD graphics, disabling integrated GPU fallback.
- **Windows Ultimate Performance Power Scheme**: Unparks all physical CPU cores and eliminates frequency scaling latency.
- **Dynamic RAM Working Set Trimming**: Flushes background cache to ensure maximum free memory during intense gunfights.
- **High-Precision Timer Resolution**: Adjusts Windows kernel timer to 0.5 ms for lowest system latency.

### 🌐 3. Network & Ping Optimizer
- **Low Ping Routing**: Real-time ICMP ping testing across global PUBG Mobile game servers (Asia, Europe, North America, Middle East).
- **Interactive Ping Graph**: Live pyqtgraph latency monitoring.
- **Gaming DNS Presets**: One-click configuration for Cloudflare (1.1.1.1), Google (8.8.8.8), and Quad9.
- **TCP ACK & Nagle Tuning**: Disables Nagle's algorithm (`TcpNoDelay=1`, `TcpAckFrequency=1`) for instantaneous packet transmission.

### 🖥️ 4. Display & Resolution Customizer
- **Native Resolution Override**: Custom resolution scaling (1080p, 1440p, 2K, 4K, stretched 4:3 resolutions).
- **High Refresh Rate Sync**: Unlocks 90 Hz / 120 Hz / 144 Hz display refresh rates.
- **Digital Vibrance & Clarity**: Enhances in-game color saturation for superior enemy spot visibility in shadows and foliage.

### 🖱️ 5. Input & Raw Polling
- **Direct Raw Mouse Input**: Bypasses Windows pointer acceleration curves (`EPP=0`) for 1:1 pixel precision.
- **1000 Hz Mouse Polling**: Reduces mouse reporting intervals to 1 ms.
- **Fast Keyboard Response**: Decreases keyboard scan repeat delays for instant lean, peek, and crouch actions.

### 🔊 6. Tactical Audio Enhancement
- **Footstep & Gunshot Frequency Equalizer**: Boosts critical 2 kHz - 8 kHz footstep frequencies.
- **Windows Spatial Sound**: Quick toggle for Dolby Atmos / Windows Sonic directional positioning.
- **Background Noise Suppression**: Dampens low-frequency engine rumbles.

### 🎮 7. In-Game HUD & Background Killer
- **Customizable Screen Crosshair**: Hardware-rendered non-intrusive crosshair overlay with customizable styles, sizing, and colors.
- **Background Process Terminator**: Real-time list of memory-heavy background processes (Chrome, Discord, OneDrive, etc.) with instant kill capability.
- **Weapon Recoil Visualizer**: Reference recoil compensation patterns for M416, Beryl M762, AKM, and DP-28.

### 👤 8. Profiles & Hardware Tiers
- **4 Built-in Hardware Profiles**: Budget, Mid-Range, High-End, and Enthusiast presets.
- **Custom Profile Manager**: Save, export, and import personalized tweak configurations.

### 🔧 9. GameLoop Registry Reference & Tweak Engine
- **50+ Curated Settings**: Full reference covering CPU allocation, VRAM cache, DirectX+ vs OpenGL+ backends, FPS unlocking, phone model spoofing (ASUS ROG Phone 6), and telemetry suppression.
- **Search & Filter**: Filter by category, safety level (Safe, Cautious, Advanced, Danger), and keywords.
- **Direct Registry Application**: Apply tweaks directly from the application with safety confirmation modals.
- **.reg File Exporter**: Export filtered tweaks or all recommended settings into ready-to-run Windows `.reg` files.

---

## 🛠️ Installation & Setup

### Requirements
- **OS**: Windows 10 / Windows 11 (64-bit)
- **Python**: 3.10+ (Tested on Python 3.13)
- **Administrator Privileges**: Recommended for applying registry tweaks and power schemes.

### Setup Instructions

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Thigan12/RT-Tool.git
   cd RT-Tool
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application:**
   ```bash
   python main.py
   ```

---

## 📦 Building Standalone Executable (.exe)

A portable single-file executable can be built using PyInstaller:

```cmd
build.bat
```
The output executable will be created in the `dist/` directory:
```
dist/RT_Tool_Optimizer.exe
```

---

## 📁 Repository Structure

```
RT Tool/
├── main.py                     # Application entry point & splash screen
├── build.bat                   # Portable executable builder
├── requirements.txt            # Python dependencies
├── .gitignore                  # Git ignore definitions
├── README.md                   # Documentation
├── ui/
│   ├── main_window.py          # App shell, sidebar navigation, top bar
│   ├── style.qss               # Dark gaming stylesheet
│   ├── icons.py                # Lucide/Feather vector icon engine
│   └── widgets/
│       ├── toggle_switch.py    # Glowing toggle switch
│       ├── ring_gauge.py       # Animated circular telemetry gauge
│       ├── stat_card.py        # Real-time hardware metric card
│       └── neon_button.py      # Styled gaming push buttons
├── pages/
│   ├── home_page.py            # Launch Hub & emulator scanner
│   ├── performance_page.py     # CPU/GPU/RAM optimization suite
│   ├── network_page.py         # Ping monitor & DNS switcher
│   ├── display_page.py         # Resolution & Hz customizer
│   ├── input_page.py           # Mouse & keyboard polling tuner
│   ├── audio_page.py           # Footstep EQ & spatial sound
│   ├── gaming_page.py          # Crosshair overlay & process killer
│   ├── profiles_page.py        # Hardware tier profiles & presets
│   └── registry_page.py        # Comprehensive GameLoop registry suite
└── core/
    ├── system_info.py          # CPU/GPU/RAM hardware sensors
    ├── scanner.py              # GameLoop installation locator
    ├── optimizer.py            # Windows powercfg & performance tweaks
    ├── network_tools.py        # ICMP ping & DNS manager
    ├── process_manager.py      # Process monitor & terminator
    ├── profile_manager.py      # Profile serialization & export
    └── registry_data.py        # GameLoop registry dataset & .reg generator
```

---

## ⚠️ Disclaimer

*RT Tool is an independent open-source utility designed to optimize Windows system settings and GameLoop emulator performance. It does not modify game memory, inject code into PUBG Mobile, or violate fair play policies.*
