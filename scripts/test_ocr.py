from __future__ import annotations

import logging
import re
import sys
from argparse import ArgumentParser
from pathlib import Path

from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.ocr import recognize_text  # noqa: E402
from src.ocr_preprocess import to_black_and_white  # noqa: E402


EXPECTED_TEXTS = {
    "sample_text_pipistrello.png": "Pippit: I should go check on auntie in her office, just in case.",
    "sample_text_easy.png": "You can take screenshots on Windows easily",
}


def normalize(text: str) -> str:
    text = re.sub(r"\s+", " ", text.casefold()).strip()
    return text


def levenshtein_distance(left: str, right: str) -> int:
    if left == right:
        return 0
    if not left:
        return len(right)
    if not right:
        return len(left)

    previous = list(range(len(right) + 1))
    for left_index, left_char in enumerate(left, start=1):
        current = [left_index]
        for right_index, right_char in enumerate(right, start=1):
            insertion = current[right_index - 1] + 1
            deletion = previous[right_index] + 1
            substitution = previous[right_index - 1] + (left_char != right_char)
            current.append(min(insertion, deletion, substitution))
        previous = current
    return previous[-1]


def similarity(left: str, right: str) -> float:
    left_normalized = normalize(left)
    right_normalized = normalize(right)
    max_length = max(len(left_normalized), len(right_normalized), 1)
    distance = levenshtein_distance(left_normalized, right_normalized)
    return 1.0 - (distance / max_length)


def main() -> int:
    parser = ArgumentParser()
    parser.add_argument("--language", default="de-DE", help="Windows OCR language tag")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    failures: list[str] = []

    for image_name, expected in EXPECTED_TEXTS.items():
        image_path = PROJECT_ROOT / image_name
        if not image_path.exists():
            failures.append(f"{image_name}: missing file")
            continue

        image = Image.open(image_path)
        processed = to_black_and_white(image)
        recognized = recognize_text(processed, language_tag=args.language)
        score = similarity(recognized, expected)

        print(f"\n{image_name}")
        print(f"Expected:   {expected}")
        print(f"Recognized: {recognized}")
        print(f"Similarity: {score:.1%}")

        if score < 0.9:
            failures.append(f"{image_name}: similarity {score:.1%}")

    if failures:
        print("\nOCR acceptance test failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("\nOCR acceptance test passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
