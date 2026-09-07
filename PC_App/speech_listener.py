"""
Jarvis PC Client - Speech Listener
Continuous local wake-phrase detection using SpeechRecognition.
Supports both native SoundDevice and PyAudio backends for 100% Windows compatibility.
Does NOT stream raw microphone audio to the VPS. Only recognized text is emitted.
"""

import collections
import logging
import math
import time
from typing import Callable, Optional

import speech_recognition as sr

from config import WAKE_PHRASES

logger = logging.getLogger("JarvisSpeech")

# Try importing sounddevice as a robust PortAudio-bundled backend
try:
    import sounddevice as sd
    import numpy as np
    HAS_SOUNDDEVICE = True
except ImportError:
    HAS_SOUNDDEVICE = False


class SpeechListener:
    def __init__(
        self,
        on_wake_detected: Optional[Callable[[], None]] = None,
        on_command_captured: Optional[Callable[[str], None]] = None,
        on_command_failed: Optional[Callable[[], None]] = None,
        on_status_change: Optional[Callable[[str], None]] = None,
    ):
        self.on_wake_detected = on_wake_detected
        self.on_command_captured = on_command_captured
        self.on_command_failed = on_command_failed
        self.on_status_change = on_status_change

        self.recognizer = sr.Recognizer()
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.8
        self._running = False
        self._paused = False
        self._cancel_active_capture = False

        self._use_sounddevice = False
        self._sample_rate = 16000
        self._microphone: Optional[sr.Microphone] = None
        self._energy_threshold = 60.0

    def _notify_status(self, status: str):
        if self.on_status_change:
            try:
                self.on_status_change(status)
            except Exception:
                pass

    def cancel_capture(self):
        """Immediately aborts any active audio recording."""
        self._cancel_active_capture = True

    def pause(self):
        """Thread-safe pause: stops active audio recording and prevents new captures."""
        self._paused = True
        self._cancel_active_capture = True

    def resume(self):
        """Thread-safe resume: allows the listen loop to resume."""
        self._cancel_active_capture = False
        self._paused = False

    def initialize_microphone(self) -> bool:
        """Initializes the default microphone and adjusts for ambient noise."""
        self._notify_status("Initializing microphone...")

        # First attempt: Try standard SpeechRecognition Microphone (requires PyAudio)
        try:
            self._microphone = sr.Microphone()
            with self._microphone as source:
                logger.info("Calibrating microphone with PyAudio...")
                self.recognizer.adjust_for_ambient_noise(source, duration=0.8)
            self._use_sounddevice = False
            self._notify_status("Microphone initialized")
            logger.info(
                "Microphone initialized successfully with PyAudio. Energy threshold: %.1f",
                self.recognizer.energy_threshold,
            )
            return True
        except Exception as e:
            logger.warning("PyAudio not available (%s), attempting SoundDevice fallback...", e)

        # Second attempt: Use SoundDevice (has prebuilt PortAudio DLL bundled)
        if HAS_SOUNDDEVICE:
            try:
                devices = sd.query_devices(kind="input")
                device_name = devices.get("name", "Default Input")
                logger.info("Using SoundDevice with device: %s", device_name)

                # Calibrate ambient noise
                logger.info("Calibrating ambient noise with SoundDevice...")
                sample_data = sd.rec(
                    int(0.8 * self._sample_rate),
                    samplerate=self._sample_rate,
                    channels=1,
                    dtype="int16",
                )
                sd.wait()
                ambient_rms = math.sqrt(np.mean(sample_data.astype(float) ** 2))
                self._energy_threshold = max(ambient_rms * 2.0, 35.0)
                self._use_sounddevice = True
                self._notify_status("Microphone initialized")
                logger.info(
                    "Microphone initialized via SoundDevice (%s). Energy threshold: %.1f",
                    device_name,
                    self._energy_threshold,
                )
                return True
            except Exception as sde:
                logger.error("SoundDevice initialization failed: %s", sde)

        self._notify_status("Microphone error (retry scheduled)")
        return False

    def is_wake_phrase(self, text: str) -> tuple[bool, Optional[str]]:
        """
        Checks if text contains the wake phrase.
        Returns (is_detected, remaining_command_text).
        """
        lower = text.lower().strip()
        for phrase in WAKE_PHRASES:
            if phrase in lower:
                idx = lower.find(phrase)
                after = lower[idx + len(phrase):].strip()
                after = after.lstrip(",.!?;: ")
                return True, after if after else None
        return False, None

    def capture_single_command(self, timeout: float = 7.0) -> Optional[str]:
        """Manually captures a single user command without background listening collision."""
        self._paused = True
        self._cancel_active_capture = False
        try:
            return self._capture_followup_command(timeout=timeout)
        finally:
            self._paused = False

    def listen_loop(self):
        """Continuous listening loop with automatic retry on audio hardware failure."""
        self._running = True

        while self._running:
            if self._paused:
                time.sleep(0.15)
                continue

            if not self._microphone and not self._use_sounddevice:
                success = self.initialize_microphone()
                if not success:
                    time.sleep(3.0)
                    continue

            try:
                self._notify_status("Waiting for 'Hey Jarvis'")
                logger.info("Listening for speech...")

                if self._use_sounddevice:
                    audio = self._listen_sounddevice(timeout=10.0)
                else:
                    with self._microphone as source:
                        audio = self.recognizer.listen(source, timeout=None, phrase_time_limit=10.0)

                if self._paused or not audio:
                    continue

                self._notify_status("Processing...")
                logger.info("Speech detected, recognizing...")

                recognized_text = self._recognize_audio(audio)
                if not recognized_text:
                    continue

                logger.info("Recognized text: '%s'", recognized_text)
                wake_found, inline_command = self.is_wake_phrase(recognized_text)

                if wake_found:
                    logger.info("Wake phrase detected!")

                    if inline_command:
                        self._notify_status("Command recognized")
                        logger.info("Captured inline command: '%s'", inline_command)
                        if self.on_command_captured:
                            self.on_command_captured(inline_command)
                    else:
                        self._notify_status("Acknowledging...")
                        if self.on_wake_detected:
                            try:
                                self.on_wake_detected()
                            except Exception as ex:
                                logger.warning("Wake acknowledgment error: %s", ex)

                        time.sleep(0.35)
                        self._notify_status("Listening for command...")
                        logger.info("Listening for follow-up command...")
                        command = self._capture_followup_command(timeout=8.0)
                        if command:
                            self._notify_status("Command recognized")
                            logger.info("Captured follow-up command: '%s'", command)
                            if self.on_command_captured:
                                self.on_command_captured(command)
                        else:
                            logger.info("No command captured after wake phrase. Resetting to standby.")
                            if self.on_command_failed:
                                self.on_command_failed()
                else:
                    # Spoken without wake word in passive mode - do nothing
                    pass

            except Exception as e:
                logger.error("Audio error in listen loop: %s", e)
                self._notify_status("Microphone error, retrying...")
                time.sleep(2.0)

    def _recognize_audio(self, audio: sr.AudioData) -> Optional[str]:
        """Recognizes speech trying Indian English, US English, and Malayalam."""
        # Try Indian English first (most accurate for Indian users speaking English)
        for lang in ["en-IN", "en-US", "ml-IN"]:
            try:
                text = self.recognizer.recognize_google(audio, language=lang)
                if text and text.strip():
                    return text.strip()
            except (sr.UnknownValueError, sr.RequestError):
                continue
        return None

    def _listen_sounddevice(self, timeout: Optional[float] = None, phrase_time_limit: float = 8.0) -> Optional[sr.AudioData]:
        """Captures voice audio using sounddevice with voice activity detection (VAD)."""
        chunk_duration = 0.1  # 100ms
        chunk_samples = int(self._sample_rate * chunk_duration)
        ring_buffer = collections.deque(maxlen=6)  # ~600ms pre-roll buffer

        started_speaking = False
        speech_frames = []
        silence_start_time = None
        start_wait_time = time.time()
        self._cancel_active_capture = False

        try:
            with sd.InputStream(samplerate=self._sample_rate, channels=1, dtype="int16") as stream:
                while self._running and not self._cancel_active_capture:
                    if self._paused and not started_speaking:
                        return None

                    chunk, overflowed = stream.read(chunk_samples)
                    rms = math.sqrt(np.mean(chunk.astype(float) ** 2))

                    if not started_speaking:
                        ring_buffer.append(chunk)
                        if timeout and (time.time() - start_wait_time > timeout):
                            return None
                        if rms > self._energy_threshold:
                            started_speaking = True
                            speech_frames.extend(list(ring_buffer))
                            silence_start_time = None
                            start_wait_time = time.time()
                    else:
                        speech_frames.append(chunk)
                        # Check speech timeout
                        if time.time() - start_wait_time > phrase_time_limit:
                            break

                        # Check silence
                        if rms < self._energy_threshold:
                            if silence_start_time is None:
                                silence_start_time = time.time()
                            elif time.time() - silence_start_time > 0.85:  # 850ms silence ends utterance
                                break
                        else:
                            silence_start_time = None
        except Exception as e:
            logger.warning("SoundDevice input stream error: %s", e)
            return None

        if self._cancel_active_capture or not speech_frames:
            return None

        audio_bytes = np.concatenate(speech_frames).tobytes()
        return sr.AudioData(audio_bytes, self._sample_rate, 2)

    def _capture_followup_command(self, timeout: float = 6.0) -> Optional[str]:
        """Captures immediate command following wake phrase or tap to speak."""
        self._cancel_active_capture = False
        try:
            if self._use_sounddevice:
                audio = self._listen_sounddevice(timeout=timeout, phrase_time_limit=10.0)
            elif self._microphone:
                with self._microphone as source:
                    audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=10.0)
            else:
                return None

            if not audio or self._cancel_active_capture:
                return None

            return self._recognize_audio(audio)
        except (sr.WaitTimeoutError, sr.UnknownValueError):
            return None
        except Exception as e:
            logger.warning("Error capturing follow-up command: %s", e)
            return None

    def stop(self):
        self._running = False
        self._cancel_active_capture = True
