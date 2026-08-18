"""
services/speech_to_text.py
----------------------------
This module contains all the AI logic for converting speech to text.

It uses OpenAI's Whisper model running 100% locally on your own
computer - there is NO paid API key required and no audio is ever
sent to the internet.

How it works (high level):
1. The Whisper model is loaded once into memory the first time it
   is needed (this can take a few seconds).
2. When a request comes in, the audio file on disk is handed to the
   model.
3. Whisper internally uses FFmpeg to decode the audio, converts it
   into a numerical representation (a "log-Mel spectrogram"), and
   feeds that through a neural network trained on hundreds of
   thousands of hours of multilingual speech.
4. The model outputs the most likely text transcription, along with
   the language it detected (if you didn't force one).
"""

import whisper

# Module-level cache so we only load the (potentially large) model
# into memory ONCE per application run, not on every single request.
_model_cache = {}


class TranscriptionError(Exception):
    """Raised when audio cannot be transcribed for any reason."""
    pass


def _get_model(model_size):
    """
    Load (or fetch from cache) the Whisper model of the requested size.

    The very first time a given model size is requested, Whisper will
    download the pretrained weights automatically (this requires an
    internet connection once). After that, it is cached locally on
    your computer and no further downloads are needed.
    """
    if model_size not in _model_cache:
        try:
            _model_cache[model_size] = whisper.load_model(model_size)
        except Exception as exc:  # noqa: BLE001 - we re-wrap intentionally
            raise TranscriptionError(
                f"Could not load the Whisper '{model_size}' model. "
                f"Make sure you have an internet connection the first "
                f"time you run this app so the model can download. "
                f"Original error: {exc}"
            ) from exc
    return _model_cache[model_size]


def transcribe_audio(file_path, model_size="tiny", language="auto"):
    """
    Transcribe the audio file at `file_path` into text.

    Parameters
    ----------
    file_path : str
        Path to the audio file on disk (wav, mp3, m4a, flac, ogg, webm).
    model_size : str
        Which Whisper model to use (tiny, base, small, medium, large).
    language : str
        "auto" to let Whisper detect the language automatically, or an
        explicit language code such as "en" or "hi".

    Returns
    -------
    dict with keys:
        "text"              - the transcribed text
        "detected_language" - the language code Whisper detected/used

    Raises
    ------
    TranscriptionError
        If the audio cannot be decoded or no speech could be detected.
    """
    model = _get_model(model_size)

    # Whisper expects `language=None` (not the string "auto") when we
    # want it to auto-detect the spoken language.
    whisper_language = None if language == "auto" else language

    try:
        result = model.transcribe(
            file_path,
            language=whisper_language,
            fp16=False,  # fp16 requires a compatible GPU; False = safe on CPU
        )
    except Exception as exc:  # noqa: BLE001 - convert to a friendly error
        raise TranscriptionError(
            "The audio file could not be processed. It may be corrupted, "
            "silent, in an unsupported format, or FFmpeg may not be "
            f"installed correctly. Original error: {exc}"
        ) from exc

    text = (result.get("text") or "").strip()
    detected_language = result.get("language", language)

    if not text:
        raise TranscriptionError(
            "No speech could be detected in this audio file. Please try "
            "a clearer recording or a different file."
        )

    return {
        "text": text,
        "detected_language": detected_language,
    }
