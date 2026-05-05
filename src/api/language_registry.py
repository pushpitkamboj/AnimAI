from __future__ import annotations
import re

LANGUAGE_CODE_TO_NAME: dict[str, str] = {
    "af": "Afrikaans",
    "ar": "Arabic",
    "bg": "Bulgarian",
    "bn": "Bengali",
    "bs": "Bosnian",
    "ca": "Catalan",
    "cs": "Czech",
    "cy": "Welsh",
    "da": "Danish",
    "de": "German",
    "el": "Greek",
    "en": "English",
    "eo": "Esperanto",
    "es": "Spanish",
    "et": "Estonian",
    "fi": "Finnish",
    "fr": "French",
    "gu": "Gujarati",
    "hi": "Hindi",
    "hr": "Croatian",
    "hu": "Hungarian",
    "hy": "Armenian",
    "id": "Indonesian",
    "is": "Icelandic",
    "it": "Italian",
    "ja": "Japanese",
    "jw": "Javanese",
    "km": "Khmer",
    "kn": "Kannada",
    "ko": "Korean",
    "la": "Latin",
    "lv": "Latvian",
    "mk": "Macedonian",
    "ml": "Malayalam",
    "mr": "Marathi",
    "ms": "Malay",
    "my": "Myanmar",
    "ne": "Nepali",
    "nl": "Dutch",
    "no": "Norwegian",
    "pl": "Polish",
    "pt": "Portuguese",
    "ro": "Romanian",
    "ru": "Russian",
    "si": "Sinhala",
    "sk": "Slovak",
    "sq": "Albanian",
    "sr": "Serbian",
    "su": "Sundanese",
    "sv": "Swedish",
    "sw": "Swahili",
    "ta": "Tamil",
    "te": "Telugu",
    "th": "Thai",
    "tl": "Filipino",
    "tr": "Turkish",
    "uk": "Ukrainian",
    "ur": "Urdu",
    "vi": "Vietnamese",
    "zh-CN": "Chinese (Simplified)",
    "zh-TW": "Chinese (Traditional)",
}

LANGUAGE_ALIASES: dict[str, str] = {
    "afrikaans": "af",
    "arabic": "ar",
    "bengali": "bn",
    "bangla": "bn",
    "bosnian": "bs",
    "bulgarian": "bg",
    "catalan": "ca",
    "chinese": "zh-CN",
    "chinese simplified": "zh-CN",
    "chinese traditional": "zh-TW",
    "croatian": "hr",
    "czech": "cs",
    "danish": "da",
    "dutch": "nl",
    "english": "en",
    "english uk": "en",
    "english us": "en",
    "esperanto": "eo",
    "estonian": "et",
    "filipino": "tl",
    "finnish": "fi",
    "french": "fr",
    "german": "de",
    "greek": "el",
    "gujarati": "gu",
    "hindi": "hi",
    "hungarian": "hu",
    "icelandic": "is",
    "indonesian": "id",
    "italian": "it",
    "japanese": "ja",
    "javanese": "jw",
    "kannada": "kn",
    "khmer": "km",
    "korean": "ko",
    "latin": "la",
    "latvian": "lv",
    "macedonian": "mk",
    "malay": "ms",
    "malayalam": "ml",
    "marathi": "mr",
    "myanmar": "my",
    "burmese": "my",
    "nepali": "ne",
    "norwegian": "no",
    "polish": "pl",
    "portuguese": "pt",
    "portuguese brazil": "pt",
    "romanian": "ro",
    "russian": "ru",
    "serbian": "sr",
    "sinhala": "si",
    "slovak": "sk",
    "spanish": "es",
    "spanish latin america": "es",
    "sundanese": "su",
    "swahili": "sw",
    "swedish": "sv",
    "tamil": "ta",
    "telugu": "te",
    "thai": "th",
    "turkish": "tr",
    "ukrainian": "uk",
    "urdu": "ur",
    "vietnamese": "vi",
    "welsh": "cy",
}


def _normalize_key(value: str) -> str:
    return re.sub(r"[\s_]+", " ", value.strip()).lower()


def normalize_language(value: str | None) -> str:
    if not value:
        return "en"

    raw_value = value.strip()
    if not raw_value:
        return "en"

    if raw_value in LANGUAGE_CODE_TO_NAME:
        return raw_value

    lowered = raw_value.lower()
    for code in LANGUAGE_CODE_TO_NAME:
        if lowered == code.lower():
            return code

    normalized = _normalize_key(raw_value.replace("-", " "))
    if normalized in LANGUAGE_ALIASES:
        return LANGUAGE_ALIASES[normalized]

    return "en"


def get_language_name(code: str) -> str:
    normalized_code = normalize_language(code)
    return LANGUAGE_CODE_TO_NAME.get(normalized_code, "English")
