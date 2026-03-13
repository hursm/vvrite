"""Qwen3 ASR transcription using mlx-audio."""

import os

from huggingface_hub import model_info, snapshot_download
from mlx_audio.stt.utils import load_model

from vvrite.preferences import Preferences
from vvrite import audio_utils


_model = None


def is_model_loaded() -> bool:
    """Return True if the ASR model is loaded in memory."""
    return _model is not None


def is_model_cached(model_id: str) -> bool:
    """Return True if the model is already downloaded locally."""
    try:
        snapshot_download(repo_id=model_id, local_files_only=True)
        return True
    except Exception:
        return False


def get_model_size(model_id: str) -> int:
    """Return total model size in bytes. Returns 0 on error."""
    try:
        info = model_info(model_id, files_metadata=True)
        return sum(s.size for s in info.siblings if s.size)
    except Exception:
        return 0


def download_model(model_id: str) -> str:
    """Download model files and return local path."""
    return snapshot_download(repo_id=model_id)


def load_from_local(local_path: str):
    """Load model from a local directory into memory."""
    global _model
    _model = load_model(local_path)


def load(prefs: Preferences = None):
    """Download + load in one step. Used by existing non-onboarding flow."""
    global _model
    if prefs is None:
        prefs = Preferences()
    model_id = prefs.model_id
    print(f"Loading model: {model_id} ...")
    _model = load_model(model_id)
    print("Model loaded.")


def transcribe(raw_wav_path: str, prefs: Preferences = None) -> str:
    """
    Normalize audio via ffmpeg, then transcribe with Qwen3-ASR.
    Cleans up temp files after processing.
    """
    if prefs is None:
        prefs = Preferences()

    normalized_path = audio_utils.normalize(raw_wav_path)
    try:
        kwargs = {"max_tokens": prefs.max_tokens}
        custom_words = prefs.custom_words.strip()
        if custom_words:
            kwargs["system_prompt"] = f"Use the following spellings: {custom_words}"
        result = _model.generate(
            normalized_path,
            **kwargs,
        )
        return result.text.strip()
    finally:
        for path in (raw_wav_path, normalized_path):
            try:
                os.unlink(path)
            except OSError:
                pass
