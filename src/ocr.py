from __future__ import annotations

import asyncio
import io
import logging

from PIL import Image
from winsdk.windows.globalization import Language
from winsdk.windows.graphics.imaging import BitmapDecoder, BitmapPixelFormat, SoftwareBitmap
from winsdk.windows.media.ocr import OcrEngine
from winsdk.windows.storage.streams import DataWriter, InMemoryRandomAccessStream


def _image_to_png_bytes(image: Image.Image) -> bytes:
    output = io.BytesIO()
    image.convert("RGB").save(output, format="PNG")
    return output.getvalue()


async def _software_bitmap_from_image(image: Image.Image) -> SoftwareBitmap:
    stream = InMemoryRandomAccessStream()
    writer = DataWriter(stream)
    writer.write_bytes(_image_to_png_bytes(image))
    await writer.store_async()
    await writer.flush_async()
    writer.detach_stream()
    stream.seek(0)

    decoder = await BitmapDecoder.create_async(stream)
    bitmap = await decoder.get_software_bitmap_async()
    return SoftwareBitmap.convert(bitmap, BitmapPixelFormat.GRAY8)


async def recognize_text_async(image: Image.Image, language_tag: str = "de-DE") -> str:
    language = Language(language_tag)
    engine = OcrEngine.try_create_from_language(language)
    if engine is None:
        raise RuntimeError(f"Windows OCR language is not available: {language_tag}")

    bitmap = await _software_bitmap_from_image(image)
    result = await engine.recognize_async(bitmap)
    text = " ".join(line.text for line in result.lines).strip()
    logging.info("OCR completed with %d character(s)", len(text))
    return text


def recognize_text(image: Image.Image, language_tag: str = "de-DE") -> str:
    return asyncio.run(recognize_text_async(image, language_tag))
