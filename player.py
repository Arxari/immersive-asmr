import os
import sys
import time
import pygame
import requests
from dotenv import load_dotenv
import logging
import select
import shutil
import termios
import tty

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class MediaPlayer:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()
        self.load_env()

    def load_env(self):
        env_file = os.path.join(os.path.dirname(__file__), '.env')
        if os.path.exists(env_file):
            load_dotenv(env_file)
            self.api_key = os.getenv('SHOCK_API_KEY')
            self.shock_id = os.getenv('SHOCK_ID')
            logging.info(f"Loaded API Key: {'*' * len(self.api_key) if self.api_key else 'Not Found'}")
            logging.info(f"Loaded Shock ID: {self.shock_id if self.shock_id else 'Not Found'}")
        else:
            self.api_key = None
            self.shock_id = None
            logging.warning("API key or Shock ID not found. OpenShock features will be disabled.")

    def trigger_shock(self, intensity, duration, shock_type='Shock'):
        if not self.api_key or not self.shock_id:
            logging.warning("OpenShock API key or Shock ID not set. Skipping shock/vibration.")
            return

        logging.info(f"Attempting to send {shock_type.lower()} with intensity: {intensity} and duration: {duration} milliseconds")

        url = 'https://api.shocklink.net/2/shockers/control'
        headers = {
            'accept': 'application/json',
            'OpenShockToken': self.api_key,
            'Content-Type': 'application/json'
        }

        payload = {
            'shocks': [{
                'id': self.shock_id,
                'type': shock_type,
                'intensity': intensity,
                'duration': duration
            }],
            'customName': 'ImmersiveASMR'
        }

        try:
            response = requests.post(url=url, headers=headers, json=payload)
            logging.debug(f"API Response: {response.status_code} - {response.text}")

            if response.status_code == 200:
                logging.info(f'{shock_type} sent successfully.')
            else:
                logging.error(f"Failed to send {shock_type.lower()}. Status code: {response.status_code}")
        except requests.exceptions.RequestException as e:
            logging.error(f"Error sending request to OpenShock API: {e}")

    def parse_timestamp(self, time_str):
        try:
            minutes, seconds = map(int, time_str.split(':'))
            return minutes * 60 + seconds
        except ValueError:
            logging.error(f"Invalid timestamp format: {time_str}")
            return 0

    def load_timestamps(self, timestamp_file):
        timestamps = []
        if os.path.exists(timestamp_file):
            logging.info(f"Loading timestamps from {timestamp_file}")
            with open(timestamp_file, 'r') as file:
                for line in file:
                    parts = line.strip().split(',')
                    if len(parts) == 4:
                        time_str, shock_type, intensity, duration = parts
                        timestamps.append({
                            'time': self.parse_timestamp(time_str),
                            'type': shock_type,
                            'intensity': int(intensity),
                            'duration': int(duration)
                        })
                    else:
                        logging.warning(f"Invalid timestamp entry: {line.strip()}")
        else:
            logging.warning(f"Timestamp file not found: {timestamp_file}")
        logging.info(f"Loaded {len(timestamps)} timestamps")
        return sorted(timestamps, key=lambda x: x['time'])

    def play(self, file_path):
        if not os.path.exists(file_path):
            logging.error(f"File not found: {file_path}")
            return

        timestamp_file = os.path.splitext(file_path)[0] + '.txt'
        timestamps = self.load_timestamps(timestamp_file)

        fd = None
        old_settings = None

        try:
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.play()

            logging.info(f"Now playing: {os.path.basename(file_path)}")

            start_time = time.time()
            current_timestamp_index = 0
            paused = False
            pause_start = 0

            print("Enter 'p' to pause/unpause, 's' to stop.")

            terminal_width = shutil.get_terminal_size().columns

            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            tty.setcbreak(fd)

            while True:
                if not paused and not pygame.mixer.music.get_busy():
                    logging.info("Playback finished")
                    break

                elapsed_time = time.time() - start_time if not paused else pause_start - start_time
                minutes, seconds = divmod(int(elapsed_time), 60)
                time_str = f"{minutes:02d}:{seconds:02d}"

                status = f"Time: {time_str} | {'Paused' if paused else 'Playing'}"
                status = status.ljust(terminal_width)

                print(f"\r{status}", end="", flush=True)

                if not paused:
                    while (current_timestamp_index < len(timestamps) and
                           timestamps[current_timestamp_index]['time'] <= elapsed_time):
                        shock = timestamps[current_timestamp_index]
                        logging.info(f"Triggering shock at {elapsed_time:.2f} seconds")
                        self.trigger_shock(shock['intensity'], shock['duration'], shock['type'])
                        current_timestamp_index += 1

                if select.select([sys.stdin], [], [], 0.1)[0]:
                    user_input = sys.stdin.read(1).lower()
                    if user_input == 'p':
                        if not paused:
                            pygame.mixer.music.pause()
                            pause_start = time.time()
                            paused = True
                            logging.info("Playback paused")
                        else:
                            pygame.mixer.music.unpause()
                            start_time += time.time() - pause_start
                            paused = False
                            logging.info("Playback resumed")
                    elif user_input == 's':
                        pygame.mixer.music.stop()
                        logging.info("Playback stopped")
                        break

                time.sleep(0.1)

        except Exception as e:
            logging.error(f"Error playing file: {e}")
        finally:
            if fd and old_settings:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

    def __del__(self):
        pygame.quit()

def main():
    if len(sys.argv) < 2:
        logging.error("Usage: python script.py <path_to_audio_file>")
        return

    player = MediaPlayer()
    file_path = sys.argv[1]
    player.play(file_path)

if __name__ == "__main__":
    main()
