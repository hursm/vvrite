"""PyInstaller spec for vvrite macOS app."""
import os
import sys
from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

site_packages = os.path.join(
    os.path.dirname(os.__file__), "site-packages"
)

# PyObjC bridge modules need all submodules collected
pyobjc_hiddenimports = (
    collect_submodules("objc")
    + collect_submodules("AppKit")
    + collect_submodules("Foundation")
    + collect_submodules("Quartz")
    + collect_submodules("ApplicationServices")
    + collect_submodules("AVFoundation")
)

a = Analysis(
    ["vvrite/main.py"],
    pathex=[],
    binaries=[
        ("/opt/homebrew/bin/ffmpeg", "."),
    ],
    datas=[
        # soundfile needs libsndfile
        (os.path.join(site_packages, "_soundfile_data"), "_soundfile_data"),
        # MLX Metal shaders and native libs
        (os.path.join(site_packages, "mlx", "lib"), os.path.join("mlx", "lib")),
    ],
    hiddenimports=pyobjc_hiddenimports + [
        # MLX (namespace package — must be explicit)
        "mlx",
        "mlx._reprlib_fix",
        "mlx.core",
        "mlx.nn",
        "mlx.optimizers",
        "mlx.utils",
        # MLX ecosystem
        "mlx_lm",
        "mlx_audio",
        "mlx_audio.stt",
        "mlx_audio.stt.models",
        "mlx_audio.stt.models.qwen3_asr",
        # Transformers
        "transformers",
        "tokenizers",
        # Audio
        "sounddevice",
        "soundfile",
        # Other
        "huggingface_hub",
        "safetensors",
        "numpy",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "tkinter",
        "pytest",
        # Heavy packages not needed (we use mlx, not torch)
        "torch",
        "torchaudio",
        "torchvision",
        "pyarrow",
        "cv2",
        "opencv-python",
        "onnxruntime",
        "PIL",
        "matplotlib",
        "pandas",
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="vvrite",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    target_arch="arm64",
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="vvrite",
)

app = BUNDLE(
    coll,
    name="vvrite.app",
    icon="assets/vvrite.icns",
    bundle_identifier="com.vvrite.app",
    info_plist={
        "CFBundleName": "vvrite",
        "CFBundleShortVersionString": "1.0.0",  # keep in sync with vvrite/__init__.__version__
        "CFBundleVersion": "1",
        "LSUIElement": True,
        "NSMicrophoneUsageDescription": (
            "vvrite needs microphone access to record and transcribe your speech."
        ),
        "NSHighResolutionCapable": True,
        "NSSupportsAutomaticTermination": False,
        "NSSupportsSuddenTermination": False,
    },
)
