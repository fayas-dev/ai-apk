"""
Jarvis PC Client - Speech Listener
Always-on local wake-phrase detection. Waits for a complete utterance
(silence after speech) before sending a command. English + Malayalam STT.
Does NOT stream raw microphone audio to the VPS.
"""

import collections
import logging
import math
import time
from typing import Callable, List, Optional

import speech_recognition as sr

from wake_phrase import parse_wake_phrase

logger = logging.getLogger("JarvisSpeech")

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
        self.recognizer.dynamic_energy_threshold = False
        self.recognizer.pause_threshold = 1.35
        self.recognizer.non_speaking_duration = 0.55
        self.recognizer.energy_threshold = 45
        self._running = False
        self._paused = False
        self._cancel_active_capture = False

        self._use_sounddevice = False
        self._sample_rate = 16000
        self._microphone: Optional[sr.Microphone] = None
        self._energy_threshold = 40.0

    def _notify_status(self, status: str):
        if self.on_status_change:
            try:
                self.on_status_change(status)
            except Exception:
                pass

    def cancel_capture(self):
        self._cancel_active_capture = True

    def pause(self):
        self._paused = True
        self._cancel_active_capture = True

    def resume(self):
        self._cancel_active_capture = False
        self._paused = False

    def initialize_microphone(self) -> bool:
        self._notify_status("Initializing microphone...")

        try:
            self._microphone = sr.Microphone()
            with self._microphone as source:
                logger.info("Calibrating microphone with PyAudio...")
                self.recognizer.adjust_for_ambient_noise(source, duration=0.6)
            self.recognizer.dynamic_energy_threshold = False
            self.recognizer.energy_threshold = max(25, min(self.recognizer.energy_threshold * 0.55, 280))
            self._use_sounddevice = False
            self._notify_status("Microphone initialized")
            logger.info("Microphone ready (PyAudio). Energy threshold: %.1f", self.recognizer.energy_threshold)
            return True
        except Exception as e:
            logger.warning("PyAudio not available (%s), attempting SoundDevice fallback...", e)

        if HAS_SOUNDDEVICE:
            try:
                devices = sd.query_devices(kind="input")
                device_name = devices.get("name", "Default Input")
                sample_data = sd.rec(
                    int(0.6 * self._sample_rate),
                    samplerate=self._sample_rate,
                    channels=1,
                    dtype="int16",
                )
                sd.wait()
                ambient_rms = math.sqrt(np.mean(sample_data.astype(float) ** 2))
                self._energy_threshold = max(ambient_rms * 1.6, 22.0)
                self._use_sounddevice = True
                self._notify_status("Microphone initialized")
                logger.info("Microphone ready via SoundDevice (%s). Energy: %.1f", device_name, self._energy_threshold)
                return True
            except Exception as sde:
                logger.error("SoundDevice initialization failed: %s", sde)

        self._notify_status("Microphone error (retry scheduled)")
        return False

    def listen_loop(self):
        self._running = True

        while self._running:
            if self._paused:
                time.sleep(0.12)
                continue

            if not self._microphone and not self._use_sounddevice:
                success = self.initialize_microphone()
                if not success:
                    time.sleep(2.5)
                    continue

            try:
                self._notify_status("Waiting for Hey Jarvis")
                # The initial window is long enough for “Hey Jarvis, <command>”
                # in one natural sentence, so there is no premature reply.
                audio = self._listen_utterance(timeout=None, phrase_time_limit=15.0, end_silence=1.35)
                if self._paused or not audio:
                    continue

                self._notify_status("Processing...")
                candidates = self._recognize_candidates(audio)
                if not candidates:
                    continue

                logger.info("Recognized candidates: %s", candidates[:4])
                wake_found = False
                inline_command = None
                for candidate in candidates:
                    found, remainder = parse_wake_phrase(candidate)
                    if found:
                        wake_found = True
                        inline_command = remainder
                        break

                if not wake_found:
                    continue

                logger.info("Wake phrase detected. Inline command: %s", inline_command)
                self._fire_wake()

                if inline_command:
                    self._notify_status("Command recognized")
                    self._emit_command(inline_command)
                    continue

                self._notify_status("Listening for command...")
                command = self._capture_followup_command(timeout=10.0)
                if command:
                    found, remainder = parse_wake_phrase(command)
                    if found:
                        command = remainder or ""
                    if command.strip():
                        self._notify_status("Command recognized")
                        self._emit_command(command.strip())
                    else:
                        logger.info("Wake only, no follow-up command.")
                        if self.on_command_failed:
                            self.on_command_failed()
                else:
                    logger.info("No command after wake phrase.")
                    if self.on_command_failed:
                        self.on_command_failed()

            except Exception as e:
                logger.error("Audio error in listen loop: %s", e)
                self._notify_status("Microphone error, retrying...")
                time.sleep(1.5)

    def _fire_wake(self):
        if self.on_wake_detected:
            try:
                self.on_wake_detected()
            except Exception as ex:
                logger.warning("Wake acknowledgment error: %s", ex)

    def _emit_command(self, command: str):
        if self.on_command_captured:
            self.on_command_captured(command)

    def capture_single_command(self, timeout: float = 10.0) -> Optional[str]:
        self._paused = True
        self._cancel_active_capture = False
        try:
            return self._capture_followup_command(timeout=timeout)
        finally:
            self._paused = False

    def _listen_utterance(
        self,
        timeout: Optional[float],
        phrase_time_limit: float,
        end_silence: float,
    ) -> Optional[sr.AudioData]:
        if self._use_sounddevice:
            return self._listen_sounddevice(
                timeout=timeout,
                phrase_time_limit=phrase_time_limit,
                end_silence=end_silence,
            )
        if not self._microphone:
            return None
        try:
            with self._microphone as source:
                return self.recognizer.listen(
                    source,
                    timeout=timeout,
                    phrase_time_limit=phrase_time_limit,
                )
        except sr.WaitTimeoutError:
            return None

    def _recognize_candidates(self, audio: sr.AudioData) -> List[str]:
        """English (IN/US) + Malayalam, including alternative transcripts."""
        seen = set()
        ordered: List[str] = []

        def add(text: Optional[str]):
            if not text:
                return
            key = text.strip().lower()
            if key and key not in seen:
                seen.add(key)
                ordered.append(text.strip())

        for lang in ("en-IN", "ml-IN", "en-US"):
            try:
                result = self.recognizer.recognize_google(audio, language=lang, show_all=True)
            except (sr.UnknownValueError, sr.RequestError):
                continue
            except Exception:
                continue

            if isinstance(result, str):
                add(result)
            elif isinstance(result, dict):
                alts = result.get("alternative") or []
                for alt in alts:
                    add(alt.get("transcript"))

        malayalam = [t for t in ordered if any("\u0D00" <= ch <= "\u0D7F" for ch in t)]
        if malayalam:
            rest = [t for t in ordered if t not in malayalam]
            return malayalam + rest
        return ordered

    def _recognize_audio(self, audio: sr.AudioData) -> Optional[str]:
        candidates = self._recognize_candidates(audio)
        return candidates[0] if candidates else None

    def _listen_sounddevice(
        self,
        timeout: Optional[float] = None,
        phrase_time_limit: float = 12.0,
        end_silence: float = 1.25,
    ) -> Optional[sr.AudioData]:
        chunk_duration = 0.08
        chunk_samples = int(self._sample_rate * chunk_duration)
        ring_buffer = collections.deque(maxlen=8)

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
                        if time.time() - start_wait_time > phrase_time_limit:
                            break
                        if rms < self._energy_threshold:
                            if silence_start_time is None:
                                silence_start_time = time.time()
                            elif time.time() - silence_start_time > end_silence:
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

    def _capture_followup_command(self, timeout: float = 10.0) -> Optional[str]:
        """Waits until the user finishes the full command (longer end-silence)."""
        self._cancel_active_capture = False
        try:
            audio = self._listen_utterance(timeout=timeout, phrase_time_limit=14.0, end_silence=1.35)
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
