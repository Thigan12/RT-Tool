"""
GameLoop Registry Tweaks Data & Utilities — RT Tool
Curated registry settings for Tencent GameLoop Android Emulator & Windows Gaming Engine.
"""

import os
import subprocess
import winreg
from typing import List, Dict, Any, Tuple

CATEGORIES = [
    "All Categories",
    "CPU/Core Management",
    "Memory/RAM Allocation",
    "GPU/Graphics Rendering",
    "FPS/Frame Rate Control",
    "Display Resolution & DPI",
    "Input Latency & Response",
    "Network/Connection Behavior",
    "Android/ADB & System Emulation",
    "Engine Core & Misc",
]

SAFETY_LEVELS = [
    "All Safety Levels",
    "Safe",
    "Cautious",
    "Advanced",
    "Danger",
]

SAFETY_COLORS = {
    "Safe":     "#00FF88",   # Neon green
    "Cautious": "#FFD700",   # Gold/Yellow
    "Advanced": "#FF6B00",   # Orange
    "Danger":   "#FF3366",   # Red
}

REGISTRY_TWEAKS: List[Dict[str, Any]] = [
    # ── 1. CPU/Core Management ──────────────────────────────────────────────
    {
        "id": "cpu_core_count",
        "category": "CPU/Core Management",
        "name": "Emulator CPU Core Count",
        "path": r"HKCU\Software\Tencent\MobileGamePC",
        "hive": "HKCU",
        "sub_key": r"Software\Tencent\MobileGamePC",
        "value_name": "VM_CPU_CORE",
        "value_type": "REG_DWORD",
        "recommended": 4,
        "default_val": 2,
        "safety": "Safe",
        "impact": "Sets the number of physical CPU cores assigned to the Android VM. 4 cores is the optimal PUBG Mobile sweet spot, preventing core contention and micro-stutters while maximizing multicore rendering."
    },
    {
        "id": "cpu_affinity_mask",
        "category": "CPU/Core Management",
        "name": "CPU Affinity Mask (8 Cores)",
        "path": r"HKCU\Software\Tencent\MobileGamePC",
        "hive": "HKCU",
        "sub_key": r"Software\Tencent\MobileGamePC",
        "value_name": "CpuAffinityMask",
        "value_type": "REG_DWORD",
        "recommended": 255,  # 0xFF = 8 cores
        "default_val": 0,
        "safety": "Cautious",
        "impact": "Binds GameLoop rendering threads exclusively to non-E-core or primary physical threads. Value 255 (0xFF) allows all 8 primary threads without thread migration penalties."
    },
    {
        "id": "cpu_multicore_opt",
        "category": "CPU/Core Management",
        "name": "Multi-Core Engine Optimization",
        "path": r"HKCU\Software\Tencent\MobileGamePC",
        "hive": "HKCU",
        "sub_key": r"Software\Tencent\MobileGamePC",
        "value_name": "MultiCoreOptimization",
        "value_type": "REG_DWORD",
        "recommended": 1,
        "default_val": 0,
        "safety": "Safe",
        "impact": "Enables multi-threaded task scheduling inside the Tencent virtualization layer, allowing simultaneous physics and rendering pipelines."
    },
    {
        "id": "cpu_thread_pool",
        "category": "CPU/Core Management",
        "name": "Worker Thread Pool Size",
        "path": r"HKCU\Software\Tencent\MobileGamePC",
        "hive": "HKCU",
        "sub_key": r"Software\Tencent\MobileGamePC",
        "value_name": "WorkerThreadPool",
        "value_type": "REG_DWORD",
        "recommended": 8,
        "default_val": 4,
        "safety": "Safe",
        "impact": "Increases background asset decompression and texture loading thread count from 4 to 8, cutting game loading times and eradicating mid-game hitching."
    },
    {
        "id": "cpu_android_process_prio",
        "category": "CPU/Core Management",
        "name": "AndroidProcess.exe CPU Priority",
        "path": r"HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Image File Execution Options\AndroidProcess.exe\PerfOptions",
        "hive": "HKLM",
        "sub_key": r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Image File Execution Options\AndroidProcess.exe\PerfOptions",
        "value_name": "CpuPriorityClass",
        "value_type": "REG_DWORD",
        "recommended": 3,  # High
        "default_val": 2,  # Normal
        "safety": "Safe",
        "impact": "Sets Windows scheduler priority for AndroidProcess.exe (the core PUBG VM container) to High (3), ensuring Windows gives CPU execution precedence over background tasks."
    },
    {
        "id": "cpu_appmarket_prio",
        "category": "CPU/Core Management",
        "name": "AppMarket.exe Background Priority",
        "path": r"HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Image File Execution Options\AppMarket.exe\PerfOptions",
        "hive": "HKLM",
        "sub_key": r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Image File Execution Options\AppMarket.exe\PerfOptions",
        "value_name": "CpuPriorityClass",
        "value_type": "REG_DWORD",
        "recommended": 5,  # Below Normal
        "default_val": 2,
        "safety": "Safe",
        "impact": "Deprioritizes Tencent launcher shell (AppMarket.exe) so it never steals CPU cycles from the actual game emulator during combat."
    },

    # ── 2. Memory/RAM Allocation ───────────────────────────────────────────
    {
        "id": "ram_vm_allocation",
        "category": "Memory/RAM Allocation",
        "name": "VM RAM Memory Allocation (MB)",
        "path": r"HKCU\Software\Tencent\MobileGamePC",
        "hive": "HKCU",
        "sub_key": r"Software\Tencent\MobileGamePC",
        "value_name": "VM_RAM_SIZE",
        "value_type": "REG_DWORD",
        "recommended": 4096,
        "default_val": 2048,
        "safety": "Safe",
        "impact": "Allocates 4096 MB (4 GB) RAM directly to the virtual guest OS. Prevents low-memory Android kills while avoiding virtual address space fragmentation."
    },
    {
        "id": "ram_max_pool",
        "category": "Memory/RAM Allocation",
        "name": "Max Emulator Memory Pool (MB)",
        "path": r"HKCU\Software\Tencent\MobileGamePC",
        "hive": "HKCU",
        "sub_key": r"Software\Tencent\MobileGamePC",
        "value_name": "MaxRamAllocation",
        "value_type": "REG_DWORD",
        "recommended": 8192,
        "default_val": 4096,
        "safety": "Cautious",
        "impact": "Expands the ceiling for total emulator allocation (including graphics heap and textures) to 8192 MB for PCs with 16 GB+ total RAM."
    },
    {
        "id": "ram_mem_trimming",
        "category": "Memory/RAM Allocation",
        "name": "Disable Background Memory Trimming",
        "path": r"HKCU\Software\Tencent\MobileGamePC",
        "hive": "HKCU",
        "sub_key": r"Software\Tencent\MobileGamePC",
        "value_name": "DisableMemoryTrimming",
        "value_type": "REG_DWORD",
        "recommended": 1,
        "default_val": 0,
        "safety": "Safe",
        "impact": "Prevents Windows and GameLoop from constantly releasing working set memory during gameplay, which causes sharp FPS drops and micro-freezes."
    },
    {
        "id": "ram_large_pages",
        "category": "Memory/RAM Allocation",
        "name": "Enable Large Page Memory Allocation",
        "path": r"HKCU\Software\Tencent\MobileGamePC",
        "hive": "HKCU",
        "sub_key": r"Software\Tencent\MobileGamePC",
        "value_name": "EnableLargePages",
        "value_type": "REG_DWORD",
        "recommended": 1,
        "default_val": 0,
        "safety": "Advanced",
        "impact": "Switches memory translation to 2 MB large pages, significantly reducing Translation Lookaside Buffer (TLB) misses inside the hypervisor."
    },
    {
        "id": "ram_android_lmk",
        "category": "Memory/RAM Allocation",
        "name": "Low Memory Killer Threshold (MB)",
        "path": r"HKCU\Software\Tencent\MobileGamePC",
        "hive": "HKCU",
        "sub_key": r"Software\Tencent\MobileGamePC",
        "value_name": "LMK_Threshold_MB",
        "value_type": "REG_DWORD",
        "recommended": 256,
        "default_val": 512,
        "safety": "Cautious",
        "impact": "Lowers Android's aggressive memory cleaner trigger so PUBG Mobile textures and shaders remain cached in memory without being purged mid-match."
    },

    # ── 3. GPU/Graphics Rendering ──────────────────────────────────────────
    {
        "id": "gpu_render_engine",
        "category": "GPU/Graphics Rendering",
        "name": "Render Engine Backend (DirectX+)",
        "path": r"HKCU\Software\Tencent\MobileGamePC",
        "hive": "HKCU",
        "sub_key": r"Software\Tencent\MobileGamePC",
        "value_name": "RenderEngine",
        "value_type": "REG_DWORD",
        "recommended": 1,  # 1 = DirectX+, 2 = OpenGL+, 3 = Smart Mode
        "default_val": 3,
        "safety": "Safe",
        "impact": "Forces DirectX+ (1) mode. Bypasses buggy Smart Mode switching and routes emulator draw calls through native Windows DirectX 11/12 with lowest driver overhead on NVIDIA and AMD GPUs."
    },
    {
        "id": "gpu_dedicated_card",
        "category": "GPU/Graphics Rendering",
        "name": "Prioritize Dedicated GPU",
        "path": r"HKCU\Software\Tencent\MobileGamePC",
        "hive": "HKCU",
        "sub_key": r"Software\Tencent\MobileGamePC",
        "value_name": "PrioritizeDedicatedGPU",
        "value_type": "REG_DWORD",
        "recommended": 1,
        "default_val": 1,
        "safety": "Safe",
        "impact": "Forces GameLoop rendering pipeline to lock onto discrete NVIDIA/AMD graphics, totally prohibiting Intel integrated graphics fallback on laptops and dual-GPU desktops."
    },
    {
        "id": "gpu_shader_cache",
        "category": "GPU/Graphics Rendering",
        "name": "Precompile & Cache Shaders",
        "path": r"HKCU\Software\Tencent\MobileGamePC",
        "hive": "HKCU",
        "sub_key": r"Software\Tencent\MobileGamePC",
        "value_name": "EnableShaderCache",
        "value_type": "REG_DWORD",
        "recommended": 1,
        "default_val": 0,
        "safety": "Safe",
        "impact": "Precompiles GLSL/HLSL shaders on startup and preserves them on disk, eliminating the notorious shader compilation stutter when scoping or encountering enemy players."
    },
    {
        "id": "gpu_texture_cache",
        "category": "GPU/Graphics Rendering",
        "name": "VRAM Texture Cache Size (MB)",
        "path": r"HKCU\Software\Tencent\MobileGamePC",
        "hive": "HKCU",
        "sub_key": r"Software\Tencent\MobileGamePC",
        "value_name": "VramCacheSizeMB",
        "value_type": "REG_DWORD",
        "recommended": 2048,
        "default_val": 1024,
        "safety": "Safe",
        "impact": "Increases emulator VRAM texture cache from 1024 MB to 2048 MB, preventing blurry texture pop-in during high-speed vehicle driving in Erangel and Miramar."
    },
    {
        "id": "gpu_rendering_cache",
        "category": "GPU/Graphics Rendering",
        "name": "Enable Rendering Cache Pipeline",
        "path": r"HKCU\Software\Tencent\MobileGamePC",
        "hive": "HKCU",
        "sub_key": r"Software\Tencent\MobileGamePC",
        "value_name": "RenderCache",
        "value_type": "REG_DWORD",
        "recommended": 1,
        "default_val": 1,
        "safety": "Safe",
        "impact": "Keeps rendered frame primitives cached in GPU memory between frame passes for higher continuous frame throughput."
    },
    {
        "id": "gpu_antialiasing",
        "category": "GPU/Graphics Rendering",
        "name": "Anti-Aliasing Mode (Disabled for Max FPS)",
        "path": r"HKCU\Software\Tencent\MobileGamePC",
        "hive": "HKCU",
        "sub_key": r"Software\Tencent\MobileGamePC",
        "value_name": "AntiAliasingMode",
        "value_type": "REG_DWORD",
        "recommended": 0,  # 0 = Off, 1 = Balanced, 2 = Ultra
        "default_val": 1,
        "safety": "Safe",
        "impact": "Turns off emulator-side multisample anti-aliasing (0 = Close). Yields 15-25% higher frame rates and razor-sharp crosshair pixel clarity."
    },
    {
        "id": "gpu_hardware_accel",
        "category": "GPU/Graphics Rendering",
        "name": "Hardware Accelerated Surface Composition",
        "path": r"HKCU\Software\Tencent\MobileGamePC",
        "hive": "HKCU",
        "sub_key": r"Software\Tencent\MobileGamePC",
        "value_name": "HardwareComposition",
        "value_type": "REG_DWORD",
        "recommended": 1,
        "default_val": 1,
        "safety": "Safe",
        "impact": "Composites Android UI overlays and game HUD via GPU flip queue rather than software rasterization."
    },

    # ── 4. FPS/Frame Rate Control ──────────────────────────────────────────
    {
        "id": "fps_unlock_extreme",
        "category": "FPS/Frame Rate Control",
        "name": "Unlock 90/120 FPS High Frame Mode",
        "path": r"HKCU\Software\Tencent\MobileGamePC",
        "hive": "HKCU",
        "sub_key": r"Software\Tencent\MobileGamePC",
        "value_name": "FPS_Extreme",
        "value_type": "REG_DWORD",
        "recommended": 1,
        "default_val": 0,
        "safety": "Safe",
        "impact": "Unlocks the 90 FPS and 120 FPS frame limits inside the GameLoop emulator engine, allowing high refresh monitor utilization."
    },
    {
        "id": "fps_target_rate",
        "category": "FPS/Frame Rate Control",
        "name": "Target Frame Rate Cap",
        "path": r"HKCU\Software\Tencent\MobileGamePC",
        "hive": "HKCU",
        "sub_key": r"Software\Tencent\MobileGamePC",
        "value_name": "TargetFPS",
        "value_type": "REG_DWORD",
        "recommended": 90,  # or 120
        "default_val": 60,
        "safety": "Safe",
        "impact": "Explicitly instructs the engine tick timer to aim for 90 FPS continuous synchronization."
    },
    {
        "id": "fps_vsync_disable",
        "category": "FPS/Frame Rate Control",
        "name": "Disable Engine VSync (Zero Input Delay)",
        "path": r"HKCU\Software\Tencent\MobileGamePC",
        "hive": "HKCU",
        "sub_key": r"Software\Tencent\MobileGamePC",
        "value_name": "VSyncEnabled",
        "value_type": "REG_DWORD",
        "recommended": 0,
        "default_val": 1,
        "safety": "Safe",
        "impact": "Disables vertical synchronization. Completely strips out frame buffer latency (reducing input lag by 16-33 ms) at the cost of potential minor screen tearing."
    },
    {
        "id": "fps_frame_pacing",
        "category": "FPS/Frame Rate Control",
        "name": "Disable Adaptive Frame Pacing",
        "path": r"HKCU\Software\Tencent\MobileGamePC",
        "hive": "HKCU",
        "sub_key": r"Software\Tencent\MobileGamePC",
        "value_name": "AdaptiveFramePacing",
        "value_type": "REG_DWORD",
        "recommended": 0,
        "default_val": 1,
        "safety": "Cautious",
        "impact": "Turns off GameLoop's internal frame limiter interpolation that artificially holds back frame presentation times, ensuring frames render as fast as hardware permits."
    },
    {
        "id": "fps_drop_skip",
        "category": "FPS/Frame Rate Control",
        "name": "Frame Drop Skip Protection",
        "path": r"HKCU\Software\Tencent\MobileGamePC",
        "hive": "HKCU",
        "sub_key": r"Software\Tencent\MobileGamePC",
        "value_name": "FrameDropProtection",
        "value_type": "REG_DWORD",
        "recommended": 1,
        "default_val": 0,
        "safety": "Safe",
        "impact": "Drops stale unpresented frames if a render stall occurs, instantly catching the display up to real-time game world state rather than showing delayed motion."
    },

    # ── 5. Display Resolution & DPI ────────────────────────────────────────
    {
        "id": "disp_res_width",
        "category": "Display Resolution & DPI",
        "name": "Display Resolution Width",
        "path": r"HKCU\Software\Tencent\MobileGamePC",
        "hive": "HKCU",
        "sub_key": r"Software\Tencent\MobileGamePC",
        "value_name": "ResolutionWidth",
        "value_type": "REG_DWORD",
        "recommended": 1920,
        "default_val": 1280,
        "safety": "Safe",
        "impact": "Horizontal pixel canvas resolution. 1920 (or 2560 for 1440p) gives crisp 1:1 pixel mapping with no blur or downsampling artifacts."
    },
    {
        "id": "disp_res_height",
        "category": "Display Resolution & DPI",
        "name": "Display Resolution Height",
        "path": r"HKCU\Software\Tencent\MobileGamePC",
        "hive": "HKCU",
        "sub_key": r"Software\Tencent\MobileGamePC",
        "value_name": "ResolutionHeight",
        "value_type": "REG_DWORD",
        "recommended": 1080,
        "default_val": 720,
        "safety": "Safe",
        "impact": "Vertical pixel canvas resolution. 1080 matches standard 16:9 1080p monitors."
    },
    {
        "id": "disp_screen_dpi",
        "category": "Display Resolution & DPI",
        "name": "Virtual Screen DPI Density",
        "path": r"HKCU\Software\Tencent\MobileGamePC",
        "hive": "HKCU",
        "sub_key": r"Software\Tencent\MobileGamePC",
        "value_name": "ScreenDPI",
        "value_type": "REG_DWORD",
        "recommended": 320,  # 240, 320, 400, 480
        "default_val": 240,
        "safety": "Safe",
        "impact": "Controls Android UI density scale. 320 or 400 DPI enlarges mini-map, health indicators, and inventory icons for effortless readability on desktop monitors."
    },
    {
        "id": "disp_custom_res_flag",
        "category": "Display Resolution & DPI",
        "name": "Custom Resolution Override",
        "path": r"HKCU\Software\Tencent\MobileGamePC",
        "hive": "HKCU",
        "sub_key": r"Software\Tencent\MobileGamePC",
        "value_name": "CustomResolutionEnabled",
        "value_type": "REG_DWORD",
        "recommended": 1,
        "default_val": 0,
        "safety": "Safe",
        "impact": "Forces the emulator window to honor custom resolutions without snapping back to default 720p presets."
    },
    {
        "id": "disp_stretch_mode",
        "category": "Display Resolution & DPI",
        "name": "Display Aspect Stretching Mode",
        "path": r"HKCU\Software\Tencent\MobileGamePC",
        "hive": "HKCU",
        "sub_key": r"Software\Tencent\MobileGamePC",
        "value_name": "StretchMode",
        "value_type": "REG_DWORD",
        "recommended": 0,  # 0 = Preserve Aspect, 1 = Stretch
        "default_val": 0,
        "safety": "Safe",
        "impact": "Preserves 16:9 true aspect ratio without distortion or horizontal character stretching."
    },

    # ── 6. Input Latency & Response ────────────────────────────────────────
    {
        "id": "input_raw_mouse",
        "category": "Input Latency & Response",
        "name": "Raw Mouse Input Capture",
        "path": r"HKCU\Software\Tencent\MobileGamePC",
        "hive": "HKCU",
        "sub_key": r"Software\Tencent\MobileGamePC",
        "value_name": "RawInputMouse",
        "value_type": "REG_DWORD",
        "recommended": 1,
        "default_val": 0,
        "safety": "Safe",
        "impact": "Directly queries the Windows Raw Input HID device rather than processing Windows cursor messages, eliminating mouse acceleration and cursor drift."
    },
    {
        "id": "input_polling_freq",
        "category": "Input Latency & Response",
        "name": "Input Polling Frequency (1000 Hz)",
        "path": r"HKCU\Software\Tencent\MobileGamePC",
        "hive": "HKCU",
        "sub_key": r"Software\Tencent\MobileGamePC",
        "value_name": "InputPollingFrequency",
        "value_type": "REG_DWORD",
        "recommended": 1000,
        "default_val": 250,
        "safety": "Safe",
        "impact": "Increases mouse coordinate sampling from 250 Hz (4 ms) to 1000 Hz (1 ms), matching modern 1000Hz gaming mice."
    },
    {
        "id": "input_smooth_aim",
        "category": "Input Latency & Response",
        "name": "Disable Aim Smoothing Filter",
        "path": r"HKCU\Software\Tencent\MobileGamePC",
        "hive": "HKCU",
        "sub_key": r"Software\Tencent\MobileGamePC",
        "value_name": "DisableSmoothAim",
        "value_type": "REG_DWORD",
        "recommended": 1,
        "default_val": 0,
        "safety": "Safe",
        "impact": "Turns off the artificial aim dampening and smoothing filter inside GameLoop keymapping, giving 1:1 true mechanical recoil control."
    },
    {
        "id": "input_key_scan_rate",
        "category": "Input Latency & Response",
        "name": "Key Scan Interval (ms)",
        "path": r"HKCU\Software\Tencent\MobileGamePC",
        "hive": "HKCU",
        "sub_key": r"Software\Tencent\MobileGamePC",
        "value_name": "KeyScanIntervalMs",
        "value_type": "REG_DWORD",
        "recommended": 1,
        "default_val": 8,
        "safety": "Safe",
        "impact": "Reduces key press detection latency from 8 ms to 1 ms for instant crouch, jump, and lean response."
    },
    {
        "id": "input_touch_inject_lag",
        "category": "Input Latency & Response",
        "name": "Touch Injection Delay (ms)",
        "path": r"HKCU\Software\Tencent\MobileGamePC",
        "hive": "HKCU",
        "sub_key": r"Software\Tencent\MobileGamePC",
        "value_name": "TouchInjectionDelayMs",
        "value_type": "REG_DWORD",
        "recommended": 0,
        "default_val": 4,
        "safety": "Safe",
        "impact": "Dispatches emulated touch events directly into the Android input pipeline without buffering."
    },

    # ── 7. Network/Connection Behavior ─────────────────────────────────────
    {
        "id": "net_tcp_nodelay",
        "category": "Network/Connection Behavior",
        "name": "TCP_NODELAY (Disable Nagle's Algorithm)",
        "path": r"HKCU\Software\Tencent\MobileGamePC",
        "hive": "HKCU",
        "sub_key": r"Software\Tencent\MobileGamePC",
        "value_name": "TcpNoDelay",
        "value_type": "REG_DWORD",
        "recommended": 1,
        "default_val": 0,
        "safety": "Safe",
        "impact": "Disables Nagle's packet-coalescing algorithm on the emulator virtual network adapter. Small game telemetry packets are sent immediately without 200 ms wait delays, drastically lowering PUBG in-game ping."
    },
    {
        "id": "net_socket_buffer",
        "category": "Network/Connection Behavior",
        "name": "Socket Buffer Size (KB)",
        "path": r"HKCU\Software\Tencent\MobileGamePC",
        "hive": "HKCU",
        "sub_key": r"Software\Tencent\MobileGamePC",
        "value_name": "SocketBufferSizeKB",
        "value_type": "REG_DWORD",
        "recommended": 128,
        "default_val": 32,
        "safety": "Safe",
        "impact": "Quadruples UDP and TCP network socket buffer sizes to absorb rapid player movement packets in crowded Hot Drops without packet drop."
    },
    {
        "id": "net_mtu_size",
        "category": "Network/Connection Behavior",
        "name": "Network Adapter MTU Size",
        "path": r"HKCU\Software\Tencent\MobileGamePC",
        "hive": "HKCU",
        "sub_key": r"Software\Tencent\MobileGamePC",
        "value_name": "NetworkMTU",
        "value_type": "REG_DWORD",
        "recommended": 1500,
        "default_val": 1400,
        "safety": "Safe",
        "impact": "Sets Maximum Transmission Unit to standard 1500 bytes to avoid packet fragmentation on broadband connections."
    },
    {
        "id": "net_dns_cache_ttl",
        "category": "Network/Connection Behavior",
        "name": "DNS Cache Expiry TTL (Seconds)",
        "path": r"HKCU\Software\Tencent\MobileGamePC",
        "hive": "HKCU",
        "sub_key": r"Software\Tencent\MobileGamePC",
        "value_name": "DnsCacheTTL",
        "value_type": "REG_DWORD",
        "recommended": 600,
        "default_val": 60,
        "safety": "Safe",
        "impact": "Extends DNS lookup caching to prevent repetitive domain resolution spikes during online matchmaking."
    },
    {
        "id": "net_tcp_ack_freq",
        "category": "Network/Connection Behavior",
        "name": "TCP Fast ACK Response (Gaming)",
        "path": r"HKLM\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters\Interfaces",
        "hive": "HKLM",
        "sub_key": r"SYSTEM\CurrentControlSet\Services\Tcpip\Parameters\Interfaces",
        "value_name": "TcpAckFrequency",
        "value_type": "REG_DWORD",
        "recommended": 1,
        "default_val": 2,
        "safety": "Cautious",
        "impact": "Sends TCP ACK responses immediately on packet arrival (frequency = 1) rather than waiting for double packets, shaving 10-20 ms off server ping."
    },

    # ── 8. Android/ADB & System Emulation ──────────────────────────────────
    {
        "id": "android_model_spoof",
        "category": "Android/ADB & System Emulation",
        "name": "Device Model (ASUS ROG Phone 6 Spoof)",
        "path": r"HKCU\Software\Tencent\MobileGamePC",
        "hive": "HKCU",
        "sub_key": r"Software\Tencent\MobileGamePC",
        "value_name": "DeviceModel",
        "value_type": "REG_SZ",
        "recommended": "ASUS ROG Phone 6",
        "default_val": "Default",
        "safety": "Safe",
        "impact": "Spoofs the guest Android system device model string to ASUS ROG Phone 6. PUBG Mobile checks this string to unlock the official 90 FPS and 120 FPS Extreme Graphics option."
    },
    {
        "id": "android_manufacturer",
        "category": "Android/ADB & System Emulation",
        "name": "Device Manufacturer String",
        "path": r"HKCU\Software\Tencent\MobileGamePC",
        "hive": "HKCU",
        "sub_key": r"Software\Tencent\MobileGamePC",
        "value_name": "DeviceManufacturer",
        "value_type": "REG_SZ",
        "recommended": "asus",
        "default_val": "tencent",
        "safety": "Safe",
        "impact": "Sets the hardware vendor identifier required for model spoof validation in the PUBG Mobile client."
    },
    {
        "id": "android_brand_string",
        "category": "Android/ADB & System Emulation",
        "name": "Device Brand Tag",
        "path": r"HKCU\Software\Tencent\MobileGamePC",
        "hive": "HKCU",
        "sub_key": r"Software\Tencent\MobileGamePC",
        "value_name": "DeviceBrand",
        "value_type": "REG_SZ",
        "recommended": "asus",
        "default_val": "tencent",
        "safety": "Safe",
        "impact": "Matches Android build.prop ro.product.brand for seamless anti-cheat hardware checks."
    },
    {
        "id": "android_adb_disable",
        "category": "Android/ADB & System Emulation",
        "name": "Disable ADB Debug Port (Anti-Ban)",
        "path": r"HKCU\Software\Tencent\MobileGamePC",
        "hive": "HKCU",
        "sub_key": r"Software\Tencent\MobileGamePC",
        "value_name": "AdbDebugEnabled",
        "value_type": "REG_DWORD",
        "recommended": 0,
        "default_val": 1,
        "safety": "Safe",
        "impact": "Closes the ADB TCP port (5555). Prevents Tencent anti-cheat (TP) from flagging the session as a potential third-party script injection or automated bot."
    },
    {
        "id": "android_root_disable",
        "category": "Android/ADB & System Emulation",
        "name": "Disable Guest Root Access (Anti-Ban)",
        "path": r"HKCU\Software\Tencent\MobileGamePC",
        "hive": "HKCU",
        "sub_key": r"Software\Tencent\MobileGamePC",
        "value_name": "RootAccessEnabled",
        "value_type": "REG_DWORD",
        "recommended": 0,
        "default_val": 0,
        "safety": "Safe",
        "impact": "Guarantees SU binary and root escalation tools are completely hidden, eliminating the risk of 10-minute or 10-year PUBG emulator bans."
    },

    # ── 9. Engine Core & Misc ──────────────────────────────────────────────
    {
        "id": "engine_telemetry_disable",
        "category": "Engine Core & Misc",
        "name": "Disable Tencent Telemetry & Analytics",
        "path": r"HKCU\Software\Tencent\MobileGamePC",
        "hive": "HKCU",
        "sub_key": r"Software\Tencent\MobileGamePC",
        "value_name": "DisableTelemetry",
        "value_type": "REG_DWORD",
        "recommended": 1,
        "default_val": 0,
        "safety": "Safe",
        "impact": "Blocks GameLoop background data mining and telemetry uploads to overseas Tencent analytics servers, saving bandwidth and background CPU."
    },
    {
        "id": "engine_crash_dump_disable",
        "category": "Engine Core & Misc",
        "name": "Disable Crash Minidump Uploads",
        "path": r"HKCU\Software\Tencent\MobileGamePC",
        "hive": "HKCU",
        "sub_key": r"Software\Tencent\MobileGamePC",
        "value_name": "DisableCrashReport",
        "value_type": "REG_DWORD",
        "recommended": 1,
        "default_val": 0,
        "safety": "Safe",
        "impact": "Disables automatic generation and upload of 500 MB+ memory dumps during background emulator errors."
    },
    {
        "id": "engine_log_verbosity",
        "category": "Engine Core & Misc",
        "name": "Disk Log Verbosity (Error Only)",
        "path": r"HKCU\Software\Tencent\MobileGamePC",
        "hive": "HKCU",
        "sub_key": r"Software\Tencent\MobileGamePC",
        "value_name": "LogVerbosityLevel",
        "value_type": "REG_DWORD",
        "recommended": 0,  # 0 = Error Only, 1 = Warn, 2 = Info, 3 = Debug
        "default_val": 2,
        "safety": "Safe",
        "impact": "Silences non-stop debug logging to disk (C:\\Users\\...\\AppData\\Local\\Tencent\\MobileGamePC\\Logs), eliminating SSD/HDD write contention stutter."
    },
    {
        "id": "engine_disk_write_cache",
        "category": "Engine Core & Misc",
        "name": "Virtual Disk I/O Write-Back Cache",
        "path": r"HKCU\Software\Tencent\MobileGamePC",
        "hive": "HKCU",
        "sub_key": r"Software\Tencent\MobileGamePC",
        "value_name": "DiskCacheWriteBack",
        "value_type": "REG_DWORD",
        "recommended": 1,
        "default_val": 0,
        "safety": "Cautious",
        "impact": "Batches disk writes into RAM buffers before committing to virtual disk VHD files, boosting map asset loading speed."
    },
    {
        "id": "engine_auto_update_block",
        "category": "Engine Core & Misc",
        "name": "Block In-Game Background Updater",
        "path": r"HKCU\Software\Tencent\MobileGamePC",
        "hive": "HKCU",
        "sub_key": r"Software\Tencent\MobileGamePC",
        "value_name": "AutoUpdateCheckDuringGame",
        "value_type": "REG_DWORD",
        "recommended": 0,
        "default_val": 1,
        "safety": "Safe",
        "impact": "Stops the GameLoop background updater from silently downloading launcher updates during an active PUBG match."
    },
    {
        "id": "engine_game_dvr_disable",
        "category": "Engine Core & Misc",
        "name": "Disable Windows GameDVR / Game Bar",
        "path": r"HKCU\System\GameConfigStore",
        "hive": "HKCU",
        "sub_key": r"System\GameConfigStore",
        "value_name": "GameDVR_Enabled",
        "value_type": "REG_DWORD",
        "recommended": 0,
        "default_val": 1,
        "safety": "Safe",
        "impact": "Disables Windows background Game Bar recording and overlay hooks that interfere with GameLoop fullscreen exclusive mode."
    },
    {
        "id": "engine_system_responsiveness",
        "category": "Engine Core & Misc",
        "name": "System Responsiveness Priority (Gaming)",
        "path": r"HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile",
        "hive": "HKLM",
        "sub_key": r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile",
        "value_name": "SystemResponsiveness",
        "value_type": "REG_DWORD",
        "recommended": 0,
        "default_val": 20,
        "safety": "Safe",
        "impact": "Allocates 100% of CPU processing bandwidth to foreground gaming tasks by setting Windows multimedia system responsiveness reservation to 0%."
    }
]


# ── Query & Filter Functions ───────────────────────────────────────────────────

def get_all_tweaks() -> List[Dict[str, Any]]:
    return REGISTRY_TWEAKS


def get_categories() -> List[str]:
    return CATEGORIES


def get_safety_levels() -> List[str]:
    return SAFETY_LEVELS


def filter_tweaks(category: str = "All Categories",
                   safety: str = "All Safety Levels",
                   search: str = "") -> List[Dict[str, Any]]:
    """Filter tweaks by category, safety level, and search keyword."""
    res = []
    search = search.strip().lower()

    for t in REGISTRY_TWEAKS:
        if category != "All Categories" and t["category"] != category:
            continue
        if safety != "All Safety Levels" and t["safety"] != safety:
            continue
        if search:
            in_name = search in t["name"].lower()
            in_val = search in t["value_name"].lower()
            in_path = search in t["path"].lower()
            in_impact = search in t["impact"].lower()
            if not (in_name or in_val or in_path or in_impact):
                continue
        res.append(t)
    return res


# ── Code Generation Helpers ───────────────────────────────────────────────────

def generate_reg_command(tweak: Dict[str, Any]) -> str:
    """Generate standard Windows reg.exe command."""
    path = tweak["path"]
    name = tweak["value_name"]
    vtype = tweak["value_type"]
    val = tweak["recommended"]

    if vtype == "REG_DWORD":
        return f'reg add "{path}" /v "{name}" /t REG_DWORD /d {val} /f'
    elif vtype == "REG_SZ":
        return f'reg add "{path}" /v "{name}" /t REG_SZ /d "{val}" /f'
    else:
        return f'reg add "{path}" /v "{name}" /d "{val}" /f'


def generate_ps_command(tweak: Dict[str, Any]) -> str:
    """Generate PowerShell Set-ItemProperty command."""
    hive = tweak["hive"]
    sub_key = tweak["sub_key"]
    name = tweak["value_name"]
    vtype = tweak["value_type"]
    val = tweak["recommended"]

    ps_root = "HKCU:" if hive == "HKCU" else "HKLM:"
    ps_path = f"{ps_root}\\{sub_key}"

    if vtype == "REG_DWORD":
        return f'Set-ItemProperty -Path "{ps_path}" -Name "{name}" -Value {val} -Type DWord -Force'
    else:
        return f'Set-ItemProperty -Path "{ps_path}" -Name "{name}" -Value "{val}" -Type String -Force'


def generate_reg_file_content(tweaks: List[Dict[str, Any]], title: str = "GameLoop Registry Tweaks") -> str:
    """Generate a valid Windows .reg file format content."""
    lines = [
        "Windows Registry Editor Version 5.00",
        f"; {title} — Generated by RT Tool (PUBG Mobile GameLoop Optimizer)",
        "; Restart GameLoop after applying for changes to take effect.",
        ""
    ]

    # Group by full path
    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for t in tweaks:
        p = t["path"]
        if p not in grouped:
            grouped[p] = []
        grouped[p].append(t)

    for path, items in grouped.items():
        lines.append(f"[{path}]")
        for t in items:
            vname = t["value_name"]
            vtype = t["value_type"]
            val = t["recommended"]
            comment = t["name"]

            lines.append(f"; {comment} ({t['safety']})")
            if vtype == "REG_DWORD":
                hex_val = f"{int(val):08x}"
                lines.append(f'"{vname}"=dword:{hex_val}')
            elif vtype == "REG_SZ":
                esc_val = str(val).replace("\\", "\\\\").replace('"', '\\"')
                lines.append(f'"{vname}"="{esc_val}"')
            else:
                lines.append(f'"{vname}"="{val}"')
        lines.append("")

    return "\n".join(lines)


# ── Execution Actions ─────────────────────────────────────────────────────────

def apply_tweak(tweak: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Apply a single registry tweak using winreg or reg.exe fallback.
    Returns (success: bool, message: str).
    """
    hive_name = tweak["hive"]
    sub_key = tweak["sub_key"]
    name = tweak["value_name"]
    vtype = tweak["value_type"]
    val = tweak["recommended"]

    hkey = winreg.HKEY_CURRENT_USER if hive_name == "HKCU" else winreg.HKEY_LOCAL_MACHINE

    try:
        # Try winreg first
        with winreg.CreateKeyEx(hkey, sub_key, 0, winreg.KEY_SET_VALUE | winreg.KEY_WOW64_64KEY) as key:
            if vtype == "REG_DWORD":
                winreg.SetValueEx(key, name, 0, winreg.REG_DWORD, int(val))
            elif vtype == "REG_SZ":
                winreg.SetValueEx(key, name, 0, winreg.REG_SZ, str(val))
            else:
                winreg.SetValueEx(key, name, 0, winreg.REG_SZ, str(val))
        return True, f"Successfully applied {name} = {val}"
    except PermissionError:
        # Fallback to reg.exe which can run with UAC prompt or admin rights
        cmd = generate_reg_command(tweak)
        try:
            res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if res.returncode == 0:
                return True, f"Applied via reg.exe: {name} = {val}"
            else:
                return False, f"Access Denied. Administrator rights required to modify {tweak['path']}"
        except Exception as e:
            return False, f"Error: {e}"
    except Exception as e:
        return False, f"Error setting {name}: {e}"


def open_regedit(path: str = ""):
    """Launch regedit.exe in the background."""
    try:
        # Optionally set LastKey so regedit navigates to target key
        if path:
            try:
                with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER,
                                        r"Software\Microsoft\Windows\CurrentVersion\Applets\Regedit",
                                        0, winreg.KEY_SET_VALUE) as key:
                    winreg.SetValueEx(key, "LastKey", 0, winreg.REG_SZ, f"Computer\\{path}")
            except Exception:
                pass
        subprocess.Popen(["regedit.exe"], shell=True)
    except Exception as e:
        pass
