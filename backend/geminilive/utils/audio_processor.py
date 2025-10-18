"""
Audio processing utilities for Gemini Live API.
"""

import io
import wave
from pathlib import Path
from typing import Tuple, Optional
import soundfile as sf
import librosa


class AudioProcessor:
    """
    Utility class for audio file processing and conversion.
    """

    @staticmethod
    def load_audio_file(
        file_path: str,
        target_sample_rate: int = 16000
    ) -> bytes:
        """
        Load audio file and convert to PCM format suitable for Gemini Live API.

        Args:
            file_path: Path to the audio file
            target_sample_rate: Target sample rate (default: 16000 Hz)

        Returns:
            Audio data in PCM format as bytes
        """
        # Load audio with librosa (handles multiple formats)
        y, sr = librosa.load(file_path, sr=target_sample_rate)
        
        # Convert to PCM format
        buffer = io.BytesIO()
        sf.write(buffer, y, sr, format='RAW', subtype='PCM_16')
        buffer.seek(0)
        
        return buffer.read()

    @staticmethod
    def load_from_bytes(
        audio_bytes: bytes,
        target_sample_rate: int = 16000
    ) -> bytes:
        """
        Load audio from bytes and convert to correct format.

        Args:
            audio_bytes: Audio data as bytes
            target_sample_rate: Target sample rate (default: 16000 Hz)

        Returns:
            Audio data in PCM format as bytes
        """
        buffer_in = io.BytesIO(audio_bytes)
        y, sr = librosa.load(buffer_in, sr=target_sample_rate)
        
        buffer_out = io.BytesIO()
        sf.write(buffer_out, y, sr, format='RAW', subtype='PCM_16')
        buffer_out.seek(0)
        
        return buffer_out.read()

    @staticmethod
    def save_audio_to_wav(
        audio_data: bytes,
        output_path: str,
        sample_rate: int = 24000,
        channels: int = 1,
        sample_width: int = 2
    ) -> None:
        """
        Save audio data as WAV file.

        Args:
            audio_data: Raw audio data in bytes
            output_path: Path to save the WAV file
            sample_rate: Sample rate of the audio (default: 24000 Hz)
            channels: Number of audio channels (default: 1 for mono)
            sample_width: Sample width in bytes (default: 2 for 16-bit)
        """
        with wave.open(output_path, "wb") as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(sample_width)
            wf.setframerate(sample_rate)
            wf.writeframes(audio_data)

    @staticmethod
    def combine_audio_chunks(
        audio_chunks: list,
        output_path: Optional[str] = None,
        sample_rate: int = 24000
    ) -> bytes:
        """
        Combine multiple audio chunks into a single audio file.

        Args:
            audio_chunks: List of audio data chunks
            output_path: Optional path to save the combined audio
            sample_rate: Sample rate of the audio (default: 24000 Hz)

        Returns:
            Combined audio data as bytes
        """
        combined = b"".join(audio_chunks)
        
        if output_path:
            AudioProcessor.save_audio_to_wav(combined, output_path, sample_rate=sample_rate)
        
        return combined

    @staticmethod
    def convert_to_base64(audio_bytes: bytes) -> str:
        """
        Convert audio bytes to base64 string.

        Args:
            audio_bytes: Audio data in bytes

        Returns:
            Base64 encoded string
        """
        import base64
        return base64.b64encode(audio_bytes).decode('utf-8')

    @staticmethod
    def convert_from_base64(base64_string: str) -> bytes:
        """
        Convert base64 string to audio bytes.

        Args:
            base64_string: Base64 encoded audio string

        Returns:
            Audio data in bytes
        """
        import base64
        return base64.b64decode(base64_string)

    @staticmethod
    def get_audio_duration(
        audio_bytes: bytes,
        sample_rate: int = 16000,
        sample_width: int = 2
    ) -> float:
        """
        Calculate duration of audio in seconds.

        Args:
            audio_bytes: Audio data in bytes
            sample_rate: Sample rate of the audio
            sample_width: Sample width in bytes

        Returns:
            Duration in seconds
        """
        num_samples = len(audio_bytes) // sample_width
        duration = num_samples / sample_rate
        return duration

