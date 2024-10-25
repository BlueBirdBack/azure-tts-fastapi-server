"""FastAPI-based server for text-to-speech conversion using Azure Neural Speech."""

import logging
import os
import io
from typing import List, Optional
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel
import azure.cognitiveservices.speech as speechsdk
from azure.cognitiveservices.speech import SpeechSynthesisOutputFormat


app = FastAPI()

load_dotenv()

SPEECH_KEY = os.environ.get("AZURE_SPEECH_KEY")
SPEECH_REGION = os.environ.get("AZURE_SPEECH_REGION")


AUDIO_FORMATS = {
    "raw-8khz-8bit-mono-mulaw": SpeechSynthesisOutputFormat.Raw8Khz8BitMonoMULaw,
    "audio-16khz-32kbitrate-mono-mp3": SpeechSynthesisOutputFormat.Audio16Khz32KBitRateMonoMp3,
    "audio-16khz-128kbitrate-mono-mp3": SpeechSynthesisOutputFormat.Audio16Khz128KBitRateMonoMp3,
    "audio-16khz-64kbitrate-mono-mp3": SpeechSynthesisOutputFormat.Audio16Khz64KBitRateMonoMp3,
    "audio-24khz-48kbitrate-mono-mp3": SpeechSynthesisOutputFormat.Audio24Khz48KBitRateMonoMp3,
    "audio-24khz-96kbitrate-mono-mp3": SpeechSynthesisOutputFormat.Audio24Khz96KBitRateMonoMp3,
    "audio-24khz-160kbitrate-mono-mp3": SpeechSynthesisOutputFormat.Audio24Khz160KBitRateMonoMp3,
    "raw-16khz-16bit-mono-truesilk": SpeechSynthesisOutputFormat.Raw16Khz16BitMonoTrueSilk,
    "riff-16khz-16bit-mono-pcm": SpeechSynthesisOutputFormat.Riff16Khz16BitMonoPcm,
    "riff-8khz-16bit-mono-pcm": SpeechSynthesisOutputFormat.Riff8Khz16BitMonoPcm,
    "riff-24khz-16bit-mono-pcm": SpeechSynthesisOutputFormat.Riff24Khz16BitMonoPcm,
    "riff-8khz-8bit-mono-mulaw": SpeechSynthesisOutputFormat.Riff8Khz8BitMonoMULaw,
    "raw-16khz-16bit-mono-pcm": SpeechSynthesisOutputFormat.Raw16Khz16BitMonoPcm,
    "raw-24khz-16bit-mono-pcm": SpeechSynthesisOutputFormat.Raw24Khz16BitMonoPcm,
    "raw-8khz-16bit-mono-pcm": SpeechSynthesisOutputFormat.Raw8Khz16BitMonoPcm,
    "ogg-16khz-16bit-mono-opus": SpeechSynthesisOutputFormat.Ogg16Khz16BitMonoOpus,
    "ogg-24khz-16bit-mono-opus": SpeechSynthesisOutputFormat.Ogg24Khz16BitMonoOpus,
    "raw-48khz-16bit-mono-pcm": SpeechSynthesisOutputFormat.Raw48Khz16BitMonoPcm,
    "riff-48khz-16bit-mono-pcm": SpeechSynthesisOutputFormat.Riff48Khz16BitMonoPcm,
    "audio-48khz-96kbitrate-mono-mp3": SpeechSynthesisOutputFormat.Audio48Khz96KBitRateMonoMp3,
    "audio-48khz-192kbitrate-mono-mp3": SpeechSynthesisOutputFormat.Audio48Khz192KBitRateMonoMp3,
    "ogg-48khz-16bit-mono-opus": SpeechSynthesisOutputFormat.Ogg48Khz16BitMonoOpus,
    "webm-16khz-16bit-mono-opus": SpeechSynthesisOutputFormat.Webm16Khz16BitMonoOpus,
    "webm-24khz-16bit-mono-opus": SpeechSynthesisOutputFormat.Webm24Khz16BitMonoOpus,
    "raw-24khz-16bit-mono-truesilk": SpeechSynthesisOutputFormat.Raw24Khz16BitMonoTrueSilk,
    "raw-8khz-8bit-mono-alaw": SpeechSynthesisOutputFormat.Raw8Khz8BitMonoALaw,
    "riff-8khz-8bit-mono-alaw": SpeechSynthesisOutputFormat.Riff8Khz8BitMonoALaw,
    "webm-24khz-16bit-24kbps-mono-opus": SpeechSynthesisOutputFormat.Webm24Khz16Bit24KbpsMonoOpus,
}

# Mapping of output formats to MIME types
MIME_TYPES = {
    "raw-8khz-8bit-mono-mulaw": "audio/basic",
    "audio-16khz-32kbitrate-mono-mp3": "audio/mpeg",
    "audio-16khz-128kbitrate-mono-mp3": "audio/mpeg",
    "audio-16khz-64kbitrate-mono-mp3": "audio/mpeg",
    "audio-24khz-48kbitrate-mono-mp3": "audio/mpeg",
    "audio-24khz-96kbitrate-mono-mp3": "audio/mpeg",
    "audio-24khz-160kbitrate-mono-mp3": "audio/mpeg",
    "raw-16khz-16bit-mono-truesilk": "audio/SILK",
    "riff-16khz-16bit-mono-pcm": "audio/wav",
    "riff-8khz-16bit-mono-pcm": "audio/wav",
    "riff-24khz-16bit-mono-pcm": "audio/wav",
    "riff-8khz-8bit-mono-mulaw": "audio/wav",
    "raw-16khz-16bit-mono-pcm": "audio/l16",
    "raw-24khz-16bit-mono-pcm": "audio/l16",
    "raw-8khz-16bit-mono-pcm": "audio/l16",
    "ogg-16khz-16bit-mono-opus": "audio/ogg",
    "ogg-24khz-16bit-mono-opus": "audio/ogg",
    "raw-48khz-16bit-mono-pcm": "audio/l16",
    "riff-48khz-16bit-mono-pcm": "audio/wav",
    "audio-48khz-96kbitrate-mono-mp3": "audio/mpeg",
    "audio-48khz-192kbitrate-mono-mp3": "audio/mpeg",
    "ogg-48khz-16bit-mono-opus": "audio/ogg",
    "webm-16khz-16bit-mono-opus": "audio/webm",
    "webm-24khz-16bit-mono-opus": "audio/webm",
    "raw-24khz-16bit-mono-truesilk": "audio/SILK",
    "raw-8khz-8bit-mono-alaw": "audio/x-alaw-basic",
    "riff-8khz-8bit-mono-alaw": "audio/wav",
    "webm-24khz-16bit-24kbps-mono-opus": "audio/webm",
}

CHUNK_SIZE = 1024


class Voice(BaseModel):
    """Represents a voice option for text-to-speech conversion."""

    gender: str
    short_name: str
    locale: str
    name: str
    local_name: Optional[str]
    style_list: List[str]
    voice_type: str


def get_available_voices(speech_key: str, service_region: str) -> List[Voice]:
    """Get available voices from Azure Cognitive Services Speech SDK."""
    speech_config = speechsdk.SpeechConfig(
        subscription=speech_key, region=service_region
    )
    speech_synthesizer = speechsdk.SpeechSynthesizer(
        speech_config=speech_config, audio_config=None
    )

    result = speech_synthesizer.get_voices_async().get()

    if result.reason == speechsdk.ResultReason.VoicesListRetrieved:
        voices = []
        for voice in result.voices:
            voices.append(
                Voice(
                    gender=voice.gender.name,
                    short_name=voice.short_name,
                    locale=voice.locale,
                    name=voice.name,
                    local_name=voice.local_name,
                    style_list=voice.style_list,
                    voice_type=voice.voice_type.name,
                )
            )
        return voices
    else:
        print(f"Error retrieving voices: {result.error_details}")
        return []


@app.get("/")
async def read_root():
    """Serve the index.html file."""
    return FileResponse("index.html")


@app.get("/voices")
async def get_voices():
    """Retrieve and return the list of available voices from Azure Neural Speech."""
    speech_key = os.getenv("AZURE_SPEECH_KEY")
    service_region = os.getenv("AZURE_SPEECH_REGION")

    if not speech_key or not service_region:
        raise HTTPException(
            status_code=500,
            detail="AZURE_SPEECH_KEY or AZURE_SPEECH_REGION environment variables are not set.",
        )

    voices = get_available_voices(speech_key, service_region)
    return voices


@app.get("/read")
async def read_text(
    text: str = Query(..., min_length=1, max_length=3000),
    voice_id: str = Query(...),
    output_format: str = Query(...),
    speed: str = Query("0%", regex=r"^[+-]?(\d{1,3}%)$"),
):
    """
    Convert text to speech using Azure Neural Speech and stream the audio.

    Args:
        text (str): The text to convert to speech.
        voice_id (str): The ID of the voice to use.
        output_format (str): The desired audio output format.
        speed (str): The speed of the speech as a percentage (e.g., "-50%", "0%", "+75%", "+100%").

    Returns:
        StreamingResponse: A streaming response containing the audio data.

    Raises:
        HTTPException: If there's an error in the text-to-speech conversion process.
    """
    logging.info(
        "Received request: text=%s, voice_id=%s, output_format=%s, speed=%s",
        text,
        voice_id,
        output_format,
        speed,
    )

    try:
        speech_config = speechsdk.SpeechConfig(
            subscription=SPEECH_KEY, region=SPEECH_REGION
        )
        speech_config.speech_synthesis_voice_name = voice_id

        # Set the output format
        speech_config.set_speech_synthesis_output_format(AUDIO_FORMATS[output_format])

        # Create a speech synthesizer
        speech_synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=speech_config, audio_config=None
        )

        # Prepare SSML with the percentage-based rate
        ssml = f"""
        <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">
            <voice name="{voice_id}">
                <prosody rate="{speed}" volume="+100%">
                    {text}
                </prosody>
            </voice>
        </speak>
        """

        logging.info("SSML: %s", ssml)

        # Synthesize speech
        result = speech_synthesizer.speak_ssml_async(ssml).get()

        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            audio_data = result.audio_data
            return StreamingResponse(
                io.BytesIO(audio_data), media_type=MIME_TYPES[output_format]
            )
        else:
            logging.error("Speech synthesis failed: %s", result.reason)
            raise HTTPException(
                status_code=500, detail="Speech synthesis failed"
            ) from result

    except Exception as e:
        logging.error("An error occurred: %s", str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="localhost", port=8000)
