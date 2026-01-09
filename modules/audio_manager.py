import os
import pygame
import wave

ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")
NOISE_FILE = os.path.join(ASSETS_DIR, "brown_noise.wav")

class AudioManager:
    def __init__(self):
        self.enabled = True # Should read from config
        self.playing = False
        try:
            pygame.mixer.init()
            self.ensure_asset()
            self.sound = pygame.mixer.Sound(NOISE_FILE)
        except Exception as e:
            print(f"Audio init failed: {e}")
            self.enabled = False
            self.sound = None

    def ensure_asset(self):
        """Creates a dummy brown noise file if missing."""
        if not os.path.exists(NOISE_FILE):
            # Generate 1 sec of silence/noise
            try:
                with wave.open(NOISE_FILE, 'w') as f:
                    f.setnchannels(1)
                    f.setsampwidth(2)
                    f.setframerate(44100)
                    f.writeframes(b'\x00\x00' * 44100) # Silence
            except:
                pass

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
