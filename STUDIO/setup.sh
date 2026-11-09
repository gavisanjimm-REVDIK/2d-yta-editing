#!/usr/bin/env bash
# setup.sh - install everything the studio needs (free / open-source, CPU only). Idempotent.
#   bash STUDIO/setup.sh          core: python deps, Blender 4.2 LTS, Mesa for CPU EEVEE, fonts
#   bash STUDIO/setup.sh --tts    also Chatterbox TTS + faster-whisper (large download: torch CPU)
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"

echo "== python deps"
pip install -q -r "$HERE/requirements.txt"

echo "== system libs (ffmpeg, Mesa EGL so EEVEE renders on CPU)"
if command -v apt-get >/dev/null; then
  apt-get update -qq
  apt-get install -y -qq ffmpeg libegl1 libgl1 libegl-mesa0 libgl1-mesa-dri libxi6 libxxf86vm1 \
    libxfixes3 libxrender1 libxkbcommon0 libsm6 >/dev/null
fi

echo "== blender"
if ! command -v blender >/dev/null; then
  V=4.2.3
  curl -sSfL -o /tmp/blender.tar.xz "https://download.blender.org/release/Blender4.2/blender-$V-linux-x64.tar.xz"
  tar -xf /tmp/blender.tar.xz -C /opt && rm /tmp/blender.tar.xz
  ln -sf "/opt/blender-$V-linux-x64/blender" /usr/local/bin/blender
fi
blender -b --version | head -1

echo "== fonts (OFL)"
F="$HERE/ASSETS/fonts"; mkdir -p "$F"
[ -f "$F/Anton-Regular.ttf" ] || curl -sSfL -o "$F/Anton-Regular.ttf" https://raw.githubusercontent.com/google/fonts/main/ofl/anton/Anton-Regular.ttf
[ -f "$F/Oswald-VF.ttf" ] || curl -sSfL -o "$F/Oswald-VF.ttf" "https://raw.githubusercontent.com/google/fonts/main/ofl/oswald/Oswald%5Bwght%5D.ttf"

if [[ "${1:-}" == "--tts" ]]; then
  echo "== TTS: Kokoro-82M (Apache-2.0, ONNX, CPU) + faster-whisper for word timing / voice QC"
  pip install -q kokoro-onnx faster-whisper
  K=/opt/models/kokoro; mkdir -p "$K"
  [ -f "$K/kokoro-v1.0.onnx" ] || curl -sSfL -o "$K/kokoro-v1.0.onnx" https://huggingface.co/fastrtc/kokoro-onnx/resolve/main/kokoro-v1.0.onnx
  [ -f "$K/voices-v1.0.bin" ] || curl -sSfL -o "$K/voices-v1.0.bin" https://huggingface.co/fastrtc/kokoro-onnx/resolve/main/voices-v1.0.bin
fi
[ -f "$F/Cinzel-VF.ttf" ] || curl -sSfL -o "$F/Cinzel-VF.ttf" "https://raw.githubusercontent.com/google/fonts/main/ofl/cinzel/Cinzel%5Bwght%5D.ttf"

echo "== sfx library"
python3 "$HERE/PIPELINE/audio/sfx_lib.py" >/dev/null && echo "ok"
