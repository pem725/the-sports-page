#!/usr/bin/env python3
"""Render narration text to a deep, measured MP3 using Piper + ffmpeg post
(pitch-down for gravitas, warmth EQ). Deliberate pauses: a beat after every
sentence, a longer one at paragraph breaks, an extra-long landing after short
punchy sentences (the dramatic one-liners) and headings.

Ported from the a_book_about_pain audiobook pipeline so The Sports Page audio
shares one house voice. Tunables (VOICE/DEEPEN) are exposed for per-project tone.

Usage: tts_render.py <in.txt> <out.mp3>
"""
import sys, re, os, wave, subprocess, tempfile
import numpy as np
from piper import PiperVoice, SynthesisConfig

MODEL = os.environ.get("PIPER_MODEL", "/tmp/piper_voices/en_US-ryan-high.onnx")
SR = 22050

# voice character: measured cadence + a touch more expressive prosody variation
CFG = SynthesisConfig(length_scale=1.05, noise_scale=0.667, noise_w_scale=0.85, volume=1.0)

# deepen + warm + level. asetrate drops pitch & slows; atempo claws tempo partway
# back (net slower, deeper). bass = chest warmth; presence bump = authority/clarity.
# Slightly less cavernous than the book (0.88 vs 0.86) — a dispatch, not a dirge.
DEEPEN = ("asetrate=22050*0.88,aresample=44100,atempo=1.06,"
          "bass=g=3:f=110,equalizer=f=2200:width_type=q:w=2:g=1.2,"
          "highpass=f=65,lowpass=f=9600,loudnorm=I=-19:TP=-1.5:LRA=11")

_voice = None
def voice():
    global _voice
    if _voice is None:
        _voice = PiperVoice.load(MODEL)
    return _voice

def synth(text):
    buf = bytearray()
    for chunk in voice().synthesize(text, CFG):
        buf += chunk.audio_int16_bytes
    return np.frombuffer(bytes(buf), dtype=np.int16)

def sil(sec):
    return np.zeros(int(SR * sec), dtype=np.int16)

def split_sentences(p):
    return [s.strip() for s in re.split(r'(?<=[.!?])\s+', p.strip()) if s.strip()]

def render_text(text):
    out = [sil(0.45)]
    paras = [p.strip() for p in re.split(r'\n\s*\n', text) if p.strip()]
    for para in paras:
        sents = split_sentences(para)
        # a one-line short paragraph reads as a heading / emphatic beat
        heading_like = len(sents) == 1 and len(para.split()) <= 9
        for s in sents:
            out.append(synth(s))
            n = len(s.split())
            pause = 0.30
            if s.endswith('?'):
                pause = 0.50
            if n <= 6:                 # dramatic one-liner -> let it land
                pause = 0.60
            out.append(sil(pause))
        out.append(sil(0.95 if heading_like else 0.55))   # paragraph / heading gap
    out.append(sil(0.6))
    return np.concatenate(out)

def render_to_mp3(text, dst, meta=None):
    """Render narration text to a deepened MP3 at dst. meta = dict of id3 tags."""
    audio = render_text(text)
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tf:
        wav_path = tf.name
    with wave.open(wav_path, 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(audio.tobytes())
    cmd = ['ffmpeg', '-y', '-i', wav_path, '-af', DEEPEN, '-b:a', '128k']
    for k, v in (meta or {}).items():
        cmd += ['-metadata', f'{k}={v}']
    cmd += [dst]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    os.remove(wav_path)
    return float(subprocess.run(['ffprobe','-v','error','-show_entries','format=duration',
                                 '-of','default=noprint_wrappers=1:nokey=1', dst],
                                capture_output=True, text=True).stdout.strip() or 0)

def main():
    src, dst = sys.argv[1], sys.argv[2]
    dur = render_to_mp3(open(src, encoding='utf-8').read(), dst)
    print(f"{os.path.basename(dst)}: {dur:.1f}s")

if __name__ == '__main__':
    main()
