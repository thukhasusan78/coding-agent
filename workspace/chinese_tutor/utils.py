import base64
import io
from typing import List, Optional
from pypinyin import pinyin, Style
from gtts import gTTS

def get_pinyin(text: str, tone_marks: bool = True) -> str:
    """
    Convert Chinese characters to pinyin.
    
    Args:
        text: The Chinese string to convert.
        tone_marks: If True, uses marks (nǐ), if False, uses numbers (ni3).
    
    Returns:
        A string of pinyin separated by spaces.
    """
    style = Style.TONE if tone_marks else Style.TONE3
    result = pinyin(text, style=style)
    return " ".join([item[0] for item in result])

def get_stroke_order_url(char: str) -> str:
    """
    Returns a URL to a stroke order animation or diagram for a given character.
    Uses the Hanzi Writer data source as a reliable open-source reference.
    
    Args:
        char: A single Chinese character.
        
    Returns:
        URL string for the stroke order resource.
    """
    if not char or len(char) != 1:
        return ""
    
    # Using the Hanzi Writer CDN for stroke order data/animations
    # This is a common standard for web-based Chinese learning tools
    char_code = ord(char)
    return f"https://cdn.jsdelivr.net/npm/hanzi-writer-data@2.0/{char}.json"

def generate_audio_base64(text: str, lang: str = 'zh-cn') -> Optional[str]:
    """
    Generates an MP3 audio stream for the given text using Google Text-to-Speech
    and encodes it in base64 for easy embedding in web applications.
    
    Args:
        text: The Chinese text to pronounce.
        lang: Language code (default zh-cn).
        
    Returns:
        Base64 encoded string of the MP3 audio, or None if failed.
    """
    try:
        tts = gTTS(text=text, lang=lang)
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        audio_bytes = fp.read()
        base64_audio = base64.b64encode(audio_bytes).decode('utf-8')
        return f"data:audio/mp3;base64,{base64_audio}"
    except Exception as e:
        print(f"Error generating audio: {e}")
        return None

def get_character_details(text: str) -> List[dict]:
    """
    Helper function to get a comprehensive breakdown of a string of characters.
    """
    details = []
    for char in text:
        if '\u4e00' <= char <= '\u9fff':  # Check if character is CJK Unified Ideograph
            details.append({
                "char": char,
                "pinyin": get_pinyin(char),
                "stroke_order_data": get_stroke_order_url(char),
                "audio": generate_audio_base64(char)
            })
    return details

if __name__ == "__main__":
    # Example usage
    test_text = "你好"
    print(f"Pinyin: {get_pinyin(test_text)}")
    print(f"Stroke Order Data URL for '你': {get_stroke_order_url('你')}")
    # Audio base64 would be a long string, so we just check if it generates
    audio = generate_audio_base64(test_text)
    print(f"Audio generated: {audio[:50]}..." if audio else "Audio generation failed")