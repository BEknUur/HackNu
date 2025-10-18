"""
Gemini Live API client for real-time audio interactions.
"""

import asyncio
from typing import Optional, AsyncGenerator, Dict, Any
from google import genai
from google.genai import types


class GeminiLiveClient:
    """
    Client for interacting with Gemini Live API.
    Supports real-time audio streaming and responses.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gemini-2.5-flash-native-audio-preview-09-2025",
        system_instruction: str = "You are a helpful assistant and answer in a friendly tone."
    ):
        """
        Initialize the Gemini Live API client.

        Args:
            api_key: Google AI API key (optional if set in environment)
            model: Model to use for Live API
            system_instruction: System instruction for the model
        """
        self.client = genai.Client(api_key=api_key) if api_key else genai.Client()
        self.model = model
        self.system_instruction = system_instruction

    async def process_audio_stream(
        self,
        audio_bytes: bytes,
        mime_type: str = "audio/pcm;rate=16000",
        response_modalities: list = None,
        additional_config: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[bytes, None]:
        """
        Process audio stream and yield audio responses.

        Args:
            audio_bytes: Audio data in bytes
            mime_type: MIME type of the audio
            response_modalities: List of response modalities (default: ["AUDIO"])
            additional_config: Additional configuration options

        Yields:
            Audio response data in bytes
        """
        if response_modalities is None:
            response_modalities = ["AUDIO"]

        config = {
            "response_modalities": response_modalities,
            "system_instruction": self.system_instruction,
        }

        if additional_config:
            config.update(additional_config)

        async with self.client.aio.live.connect(model=self.model, config=config) as session:
            # Send audio input
            await session.send_realtime_input(
                audio=types.Blob(data=audio_bytes, mime_type=mime_type)
            )

            # Receive and yield responses
            async for response in session.receive():
                if response.data is not None:
                    yield response.data

    async def process_audio_to_text(
        self,
        audio_bytes: bytes,
        mime_type: str = "audio/pcm;rate=16000"
    ) -> str:
        """
        Process audio and return text response.

        Args:
            audio_bytes: Audio data in bytes
            mime_type: MIME type of the audio

        Returns:
            Text response from the model
        """
        config = {
            "response_modalities": ["TEXT"],
            "system_instruction": self.system_instruction,
        }

        text_response = ""

        async with self.client.aio.live.connect(model=self.model, config=config) as session:
            await session.send_realtime_input(
                audio=types.Blob(data=audio_bytes, mime_type=mime_type)
            )

            async for response in session.receive():
                if hasattr(response, 'server_content') and response.server_content:
                    if hasattr(response.server_content, 'model_turn') and response.server_content.model_turn:
                        for part in response.server_content.model_turn.parts:
                            if hasattr(part, 'text') and part.text:
                                text_response += part.text

        return text_response

    async def process_text_to_audio(
        self,
        text: str
    ) -> AsyncGenerator[bytes, None]:
        """
        Process text input and yield audio responses.

        Args:
            text: Input text

        Yields:
            Audio response data in bytes
        """
        config = {
            "response_modalities": ["AUDIO"],
            "system_instruction": self.system_instruction,
        }

        async with self.client.aio.live.connect(model=self.model, config=config) as session:
            await session.send_realtime_input(text=text)

            async for response in session.receive():
                if response.data is not None:
                    yield response.data

    async def interactive_session(
        self,
        input_generator: AsyncGenerator[Dict[str, Any], None],
        response_modalities: list = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Create an interactive session with continuous input/output.

        Args:
            input_generator: Async generator yielding input data
            response_modalities: List of response modalities

        Yields:
            Response data dictionaries
        """
        if response_modalities is None:
            response_modalities = ["AUDIO"]

        config = {
            "response_modalities": response_modalities,
            "system_instruction": self.system_instruction,
        }

        async with self.client.aio.live.connect(model=self.model, config=config) as session:
            async def send_inputs():
                async for input_data in input_generator:
                    if "audio" in input_data:
                        await session.send_realtime_input(
                            audio=types.Blob(
                                data=input_data["audio"],
                                mime_type=input_data.get("mime_type", "audio/pcm;rate=16000")
                            )
                        )
                    elif "text" in input_data:
                        await session.send_realtime_input(text=input_data["text"])

            send_task = asyncio.create_task(send_inputs())

            try:
                async for response in session.receive():
                    response_data = {}
                    if response.data is not None:
                        response_data["audio_data"] = response.data
                    if hasattr(response, 'server_content') and response.server_content:
                        response_data["server_content"] = response.server_content
                    
                    if response_data:
                        yield response_data
            finally:
                await send_task

