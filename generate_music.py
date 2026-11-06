import os
import subprocess
import numpy as np
import imageio_ffmpeg

SAMPLE_RATE = 44100

NOTE_FREQS = {
    'C2': 65.41, 'D2': 73.42, 'E2': 82.41, 'F2': 87.31, 'G2': 98.00, 'A2': 110.00, 'B2': 123.47,
    'C3': 130.81, 'D3': 146.83, 'E3': 164.81, 'F3': 174.61, 'G3': 196.00, 'A3': 220.00, 'B3': 246.94,
    'C4': 261.63, 'D4': 293.66, 'E4': 329.63, 'F4': 349.23, 'G4': 392.00, 'A4': 440.00, 'B4': 493.88,
    'C5': 523.25, 'D5': 587.33, 'E5': 659.25, 'F5': 698.46, 'G5': 783.99, 'A5': 880.00, 'B5': 987.77,
    'C6': 1046.50
}

def render_piano_note(freq: float, duration: float, velocity: float = 0.8) -> np.ndarray:
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), False)
    # Piano harmonic structure
    h1 = 1.00 * np.sin(2 * np.pi * freq * t)
    h2 = 0.55 * np.sin(2 * np.pi * 2 * freq * t + 0.1)
    h3 = 0.28 * np.sin(2 * np.pi * 3 * freq * t + 0.2)
    h4 = 0.14 * np.sin(2 * np.pi * 4 * freq * t + 0.3)
    h5 = 0.06 * np.sin(2 * np.pi * 5 * freq * t + 0.4)
    wave = h1 + h2 + h3 + h4 + h5
    
    # Attack and exponential decay envelope
    attack_samples = int(SAMPLE_RATE * 0.015)
    attack = np.linspace(0, 1, attack_samples)
    envelope = np.exp(-2.2 * t / duration)
    envelope[:attack_samples] *= attack
    return wave * envelope * velocity

def save_to_mp3(audio: np.ndarray, output_path: str):
    # Normalize to avoid clipping
    max_val = np.max(np.abs(audio))
    if max_val > 0:
        audio = audio / max_val * 0.88
    audio_int16 = (audio * 32767).astype(np.int16)

    # Convert raw audio via ffmpeg
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    cmd = [
        ffmpeg_exe, "-y",
        "-f", "s16le",
        "-ar", str(SAMPLE_RATE),
        "-ac", "1",
        "-i", "-",
        "-c:a", "libmp3lame",
        "-b:a", "192k",
        output_path
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    proc.stdin.write(audio_int16.tobytes())
    proc.stdin.close()
    proc.wait()

def generate_romantic_tracks(output_dir: str):
    os.makedirs(output_dir, exist_ok=True)

    # --- Track 1: Mayin Pianino (Am -> F -> C -> G) ---
    track_1_path = os.path.join(output_dir, "romantic_piano.mp3")
    if not os.path.exists(track_1_path):
        print("Generating Track 1: Romantic Piano...")
        # 4 chords x 4 beats = 16 beats loop x 2 = 32 beats (~30 seconds)
        bpm = 64
        beat_len = 60.0 / bpm
        chord_len = beat_len * 4
        chords = [
            # Bass, Mid chord notes, Arpeggio sequence
            ('A2', ['C4', 'E4', 'A4'], ['A3', 'C4', 'E4', 'A4', 'E4', 'C4', 'E4', 'A4']),
            ('F2', ['C4', 'F4', 'A4'], ['F3', 'A3', 'C4', 'F4', 'C4', 'A3', 'C4', 'F4']),
            ('C3', ['C4', 'E4', 'G4'], ['C3', 'G3', 'C4', 'E4', 'G4', 'E4', 'C4', 'G3']),
            ('G2', ['B3', 'D4', 'G4'], ['G3', 'B3', 'D4', 'G4', 'D4', 'B3', 'D4', 'G4'])
        ]
        
        full_audio = np.zeros(int(SAMPLE_RATE * chord_len * len(chords) * 2))
        curr_offset = 0

        for loop in range(2):
            for bass, chord_tones, arp in chords:
                # Add bass note
                b_wave = render_piano_note(NOTE_FREQS[bass], chord_len * 0.95, velocity=0.7)
                end_idx = min(len(full_audio), curr_offset + len(b_wave))
                full_audio[curr_offset:end_idx] += b_wave[:end_idx - curr_offset]

                # Add arpeggio notes
                note_dur = chord_len / len(arp)
                for i, note in enumerate(arp):
                    n_wave = render_piano_note(NOTE_FREQS[note], note_dur * 1.8, velocity=0.55)
                    n_start = curr_offset + int(i * note_dur * SAMPLE_RATE)
                    n_end = min(len(full_audio), n_start + len(n_wave))
                    full_audio[n_start:n_end] += n_wave[:n_end - n_start]

                curr_offset += int(chord_len * SAMPLE_RATE)

        save_to_mp3(full_audio, track_1_path)

    # --- Track 2: Sevgi Izhori (C -> G -> Am -> F) ---
    track_2_path = os.path.join(output_dir, "acoustic_love.mp3")
    if not os.path.exists(track_2_path):
        print("Generating Track 2: Acoustic Love...")
        bpm = 72
        beat_len = 60.0 / bpm
        chord_len = beat_len * 4
        chords_2 = [
            ('C3', ['E4', 'G4', 'C5'], ['C4', 'E4', 'G4', 'C5', 'G4', 'E4']),
            ('G2', ['D4', 'G4', 'B4'], ['B3', 'D4', 'G4', 'B4', 'G4', 'D4']),
            ('A2', ['C4', 'E4', 'A4'], ['A3', 'C4', 'E4', 'A4', 'E4', 'C4']),
            ('F2', ['C4', 'F4', 'A4'], ['F3', 'A3', 'C4', 'F4', 'C4', 'A3'])
        ]
        full_audio_2 = np.zeros(int(SAMPLE_RATE * chord_len * len(chords_2) * 2))
        curr_offset = 0

        for loop in range(2):
            for bass, _, arp in chords_2:
                b_wave = render_piano_note(NOTE_FREQS[bass], chord_len * 0.9, velocity=0.65)
                end_idx = min(len(full_audio_2), curr_offset + len(b_wave))
                full_audio_2[curr_offset:end_idx] += b_wave[:end_idx - curr_offset]

                note_dur = chord_len / len(arp)
                for i, note in enumerate(arp):
                    n_wave = render_piano_note(NOTE_FREQS[note], note_dur * 1.6, velocity=0.6)
                    n_start = curr_offset + int(i * note_dur * SAMPLE_RATE)
                    n_end = min(len(full_audio_2), n_start + len(n_wave))
                    full_audio_2[n_start:n_end] += n_wave[:n_end - n_start]

                curr_offset += int(chord_len * SAMPLE_RATE)

        save_to_mp3(full_audio_2, track_2_path)

    # --- Track 3: Sokin Romance (F -> G -> Em -> Am) ---
    track_3_path = os.path.join(output_dir, "soft_romance.mp3")
    if not os.path.exists(track_3_path):
        print("Generating Track 3: Soft Romance...")
        bpm = 58
        beat_len = 60.0 / bpm
        chord_len = beat_len * 4
        chords_3 = [
            ('F2', ['A3', 'C4', 'F4'], ['F3', 'C4', 'F4', 'A4', 'F4', 'C4']),
            ('G2', ['B3', 'D4', 'G4'], ['G3', 'D4', 'G4', 'B4', 'G4', 'D4']),
            ('E2', ['G3', 'B3', 'E4'], ['E3', 'B3', 'E4', 'G4', 'E4', 'B3']),
            ('A2', ['C4', 'E4', 'A4'], ['A3', 'E4', 'A4', 'C5', 'A4', 'E4'])
        ]
        full_audio_3 = np.zeros(int(SAMPLE_RATE * chord_len * len(chords_3) * 2))
        curr_offset = 0

        for loop in range(2):
            for bass, _, arp in chords_3:
                b_wave = render_piano_note(NOTE_FREQS[bass], chord_len * 0.95, velocity=0.7)
                end_idx = min(len(full_audio_3), curr_offset + len(b_wave))
                full_audio_3[curr_offset:end_idx] += b_wave[:end_idx - curr_offset]

                note_dur = chord_len / len(arp)
                for i, note in enumerate(arp):
                    n_wave = render_piano_note(NOTE_FREQS[note], note_dur * 2.0, velocity=0.5)
                    n_start = curr_offset + int(i * note_dur * SAMPLE_RATE)
                    n_end = min(len(full_audio_3), n_start + len(n_wave))
                    full_audio_3[n_start:n_end] += n_wave[:n_end - n_start]

                curr_offset += int(chord_len * SAMPLE_RATE)

        save_to_mp3(full_audio_3, track_3_path)

    print("All romantic tracks generated successfully!")

if __name__ == "__main__":
    generate_romantic_tracks("assets/music")
