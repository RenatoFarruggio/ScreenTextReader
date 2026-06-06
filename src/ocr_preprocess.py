from __future__ import annotations

import logging

import numpy as np
from PIL import Image


def _otsu_threshold(values: np.ndarray) -> int:
    histogram = np.bincount(values.ravel(), minlength=256).astype(np.float64)
    total = values.size
    sum_total = float(np.dot(np.arange(256), histogram))

    sum_background = 0.0
    weight_background = 0.0
    max_variance = -1.0
    threshold = 128

    for level in range(256):
        weight_background += histogram[level]
        if weight_background == 0:
            continue

        weight_foreground = total - weight_background
        if weight_foreground == 0:
            break

        sum_background += level * histogram[level]
        mean_background = sum_background / weight_background
        mean_foreground = (sum_total - sum_background) / weight_foreground
        variance = weight_background * weight_foreground * (mean_background - mean_foreground) ** 2

        if variance > max_variance:
            max_variance = variance
            threshold = level

    return threshold


def to_black_and_white(
    image: Image.Image,
    threshold: int | None = 70,
    scale: int | None = None,
) -> Image.Image:
    grayscale = image.convert("L")
    values = np.asarray(grayscale)
    threshold_value = _otsu_threshold(values) if threshold is None else threshold

    bright_foreground = values > threshold_value
    bright_ratio = float(np.count_nonzero(bright_foreground)) / float(values.size)

    if bright_ratio < 0.5:
        result = np.where(bright_foreground, 0, 255).astype(np.uint8)
    else:
        result = np.where(bright_foreground, 255, 0).astype(np.uint8)

    processed = Image.fromarray(result, mode="L")
    scale_value = scale if scale is not None else (2 if image.height < 60 else 1)
    if scale_value > 1:
        processed = processed.resize(
            (processed.width * scale_value, processed.height * scale_value),
            Image.Resampling.NEAREST,
        )
    logging.info(
        "Converted image to black/white with threshold %d and scale %d",
        threshold_value,
        scale_value,
    )
    return processed
