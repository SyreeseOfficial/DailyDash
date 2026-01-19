import os
import pygame
import wave
import random
import struct

ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")
NOISE_FILE = os.path.join(ASSETS_DIR, "brown_noise.wav")
CHIME_FILE = os.path.join(ASSETS_DIR, "chime.wav")

class AudioManager:
    def __init__(self):
        self.enabled = True # Should read from config
        self.playing = False
        try:
            pygame.mixer.init()
            self.ensure_asset()
            self.ensure_chime()
            self.sound = pygame.mixer.Sound(NOISE_FILE)
            self.chime_sound = pygame.mixer.Sound(CHIME_FILE)
        except Exception as e:
            print(f"Audio init failed: {e}")
            self.enabled = False
            self.sound = None
            self.chime_sound = None

    def ensure_asset(self):
        """Creates a brown noise file if missing."""
        if not os.path.exists(NOISE_FILE):
            # Generate 5 seconds of brown noise
            # Brown noise = integration of white noise
            duration = 5 
            sample_rate = 44100
            n_samples = duration * sample_rate
            
            samples = []
            val = 0.0
            
            # Simple random walk
            for _ in range(n_samples):
                white = random.uniform(-1, 1)
                val += white
                # Leaky integrator to prevent drift
                val -= val * 0.02 
                samples.append(val)
            
            # Normalize
            max_val = max(abs(min(samples)), abs(max(samples)))
            if max_val > 0:
                samples = [s / max_val for s in samples]
            
            # Convert to 16-bit PCM
            wave_data = bytearray()
            for s in samples:
                # Scale to int16
                i = int(s * 32767)
                wave_data.extend(struct.pack('<h', i))
                
            try:
                with wave.open(NOISE_FILE, 'w') as f:
                    f.setnchannels(1)
                    f.setsampwidth(2)
                    f.setframerate(sample_rate)
                    f.writeframes(wave_data)
            except Exception as e:
                print(f"Failed to generate noise: {e}")


    def ensure_chime(self):
        """Creates a simple chime/ding file if missing."""
        if not os.path.exists(CHIME_FILE):
            import math
            duration = 1.0
            sample_rate = 44100
            n_samples = int(duration * sample_rate)
            
            wave_data = bytearray()
            
            # Sine wave with exponential decay (simple ding)
            frequency = 880.0 # A5
            
            for i in range(n_samples):
                t = float(i) / sample_rate
                # Sine wave
                val = math.sin(2.0 * math.pi * frequency * t)
                # Decay
                val *= math.exp(-3.0 * t)
                
                # Scale to int16
                sample = int(val * 32767)
                wave_data.extend(struct.pack('<h', sample))
                
            try:
                with wave.open(CHIME_FILE, 'w') as f:
                    f.setnchannels(1)
                    f.setsampwidth(2)
                    f.setframerate(sample_rate)
                    f.writeframes(wave_data)
            except Exception as e:
                print(f"Failed to generate chime: {e}")

    def toggle_brown_noise(self):
        if not self.enabled or not self.sound:
            return False
        
        if self.playing:
            self.sound.stop()
            self.playing = False
        else:
            self.sound.play(loops=-1)
            self.playing = True
        return self.playing

    def play_chime(self):
        if self.enabled and self.chime_sound:
            self.chime_sound.play()
