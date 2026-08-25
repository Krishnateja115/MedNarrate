import wave
import struct
import math
import os

os.makedirs('assets/sounds', exist_ok=True)

def generate_tone(filename, frequencies, duration, sample_rate=44100, volume=32767.0/2):
    num_samples = int(duration * sample_rate)
    with wave.open(f'assets/sounds/{filename}', 'w') as wav_file:
        wav_file.setnchannels(1) # mono
        wav_file.setsampwidth(2) # 2 bytes per sample
        wav_file.setframerate(sample_rate)
        
        for i in range(num_samples):
            # Sum up sine waves for the given frequencies
            sample = 0
            for freq in frequencies:
                sample += math.sin(2 * math.pi * freq * (i / sample_rate))
            
            # Apply an envelope (fade in and fade out)
            env = 1.0
            if i < 0.1 * sample_rate:
                env = i / (0.1 * sample_rate)
            elif i > num_samples - 0.2 * sample_rate:
                env = (num_samples - i) / (0.2 * sample_rate)
            
            sample = int(sample * (volume / len(frequencies)) * env)
            wav_file.writeframes(struct.pack('h', sample))

# 1. Gentle Chime: E5, G5, C6 (chord)
generate_tone('gentle_chime.wav', [659.25, 783.99, 1046.50], 1.5)

# 2. Soft Pulse: single frequency pulsing (we can just do a warm tone)
generate_tone('soft_pulse.wav', [440.0], 1.0) # A4

# 3. Alert: slightly dissonant/urgent
generate_tone('alert.wav', [880.0, 932.33], 0.8) # A5, Bb5

print("Generated sounds in assets/sounds/")
