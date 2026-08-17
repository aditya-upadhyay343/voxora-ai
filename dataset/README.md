# Dataset Folder

## What this folder contains

This folder contains a **sample/reference dataset**: `sample_transcriptions.csv`.
It is a small, illustrative table showing what a speech-to-text dataset
typically looks like - it is **not** a real audio dataset (there are no
actual `.wav` files included), and it is **not** used to train or
fine-tune the Whisper model in this project.

The CSV has these columns:

| Column          | Meaning                                             |
|-----------------|------------------------------------------------------|
| `id`            | A unique row identifier                              |
| `audio_file`    | The filename an audio clip would have (illustrative)  |
| `transcription` | The text a human transcriber would produce for it     |
| `language`      | The spoken language code (`en` = English, `hi` = Hindi) |

## How real speech datasets are structured

A real-world speech-to-text dataset normally has:

1. **A folder of audio clips** - short recordings (a few seconds to a
   few minutes each), usually in `.wav` or `.flac` format, sampled at
   16kHz mono, since that is what most speech models expect.
2. **A metadata file** (CSV, JSON, or TSV) that maps each audio file to
   its correct human-written transcription, and often also the
   speaker's language, accent, or speaker ID.
3. **A train/validation/test split**, so the model's performance can
   be measured on audio it has never seen before.

## Why this project does not train its own model

Training a speech-recognition model from scratch requires enormous
amounts of labelled audio (thousands of hours) and significant compute
power (multiple GPUs running for days or weeks). That is far beyond
the scope of a local beginner project.

Instead, this project uses **OpenAI's Whisper**, a model that has
*already been trained* by OpenAI on hundreds of thousands of hours of
multilingual audio. We simply load its pretrained weights and use them
to run inference (i.e. produce transcriptions) - we do not train or
fine-tune it here.

## Using a real dataset (e.g. LibriSpeech)

If you want to go further and actually experiment with training or
evaluating a speech model, a well-known public dataset is
[**LibriSpeech**](https://www.openslr.org/12) - about 1,000 hours of
read English speech, freely available for research use. To use it you
would typically:

1. Download one of the LibriSpeech subsets (e.g. `train-clean-100`).
2. Extract it, which gives you folders of `.flac` audio clips plus
   `.trans.txt` transcript files.
3. Build a CSV similar to `sample_transcriptions.csv` above, mapping
   each audio file to its transcription.
4. Use that CSV with a training/evaluation framework (e.g. Hugging
   Face `transformers` + `datasets`, or NVIDIA NeMo) if you want to
   fine-tune a model or benchmark Whisper's accuracy against it.

This project's Flask app does not perform steps 1-4 automatically -
they are described here purely for your own further learning.
