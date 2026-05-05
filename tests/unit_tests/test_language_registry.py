import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from api.language_registry import normalize_language


def test_normalize_language_accepts_codes() -> None:
    assert normalize_language("en") == "en"
    assert normalize_language("hi") == "hi"
    assert normalize_language("zh-CN") == "zh-CN"


def test_normalize_language_accepts_names_and_aliases() -> None:
    assert normalize_language("Hindi") == "hi"
    assert normalize_language("french") == "fr"
    assert normalize_language("Chinese Traditional") == "zh-TW"


def test_normalize_language_falls_back_to_english() -> None:
    assert normalize_language("") == "en"
    assert normalize_language("unknown-language") == "en"
