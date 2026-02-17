from typing import Dict, List, Any, Optional

# Chinese Language Lessons Data Structure
# Structured by HSK (Hanyu Shuiping Kaoshi) levels

LESSONS: Dict[str, List[Dict[str, Any]]] = {
    "HSK1": [
        {
            "id": 1,
            "title": "Greetings & Basics",
            "vocabulary": [
                {"char": "你", "pinyin": "nǐ", "english": "you"},
                {"char": "好", "pinyin": "hǎo", "english": "good / well"},
                {"char": "你好", "pinyin": "nǐ hǎo", "english": "hello"},
                {"char": "老师", "pinyin": "lǎoshī", "english": "teacher"},
                {"char": "吗", "pinyin": "ma", "english": "question particle"},
                {"char": "我", "pinyin": "wǒ", "english": "I / me"},
                {"char": "很", "pinyin": "hěn", "english": "very"},
                {"char": "谢谢", "pinyin": "xièxie", "english": "thanks"}
            ],
            "grammar": [
                "Subject + Verb + Object (Basic sentence structure)",
                "Adding 'ma' (吗) at the end of a statement turns it into a question."
            ],
            "exercises": [
                {
                    "type": "translation",
                    "question": "How do you say 'Hello' in Chinese?",
                    "answer": "你好",
                    "options": ["你好", "谢谢", "老师"]
                },
                {
                    "type": "multiple_choice",
                    "question": "What does '老师' mean?",
                    "options": ["Student", "Teacher", "Doctor", "Friend"],
                    "answer": "Teacher"
                }
            ]
        },
        {
            "id": 2,
            "title": "Numbers & Counting",
            "vocabulary": [
                {"char": "一", "pinyin": "yī", "english": "one"},
                {"char": "二", "pinyin": "èr", "english": "two"},
                {"char": "三", "pinyin": "sān", "english": "three"},
                {"char": "十", "pinyin": "shí", "english": "ten"},
                {"char": "百", "pinyin": "bǎi", "english": "hundred"},
                {"char": "钱", "pinyin": "qián", "english": "money"},
                {"char": "块", "pinyin": "kuài", "english": "measure word for currency"}
            ],
            "grammar": [
                "Numbers 1-10 are the foundation for all other numbers.",
                "Measure words (like 'kuài') are required between a number and a noun."
            ],
            "exercises": [
                {
                    "type": "translation",
                    "question": "Translate 'Three' to Chinese characters.",
                    "answer": "三",
                    "options": ["一", "二", "三"]
                }
            ]
        }
    ],
    "HSK2": [
        {
            "id": 1,
            "title": "Daily Routine & Time",
            "vocabulary": [
                {"char": "现在", "pinyin": "xiànzài", "english": "now"},
                {"char": "点", "pinyin": "diǎn", "english": "o'clock"},
                {"char": "起床", "pinyin": "qǐchuáng", "english": "to get up"},
                {"char": "吃饭", "pinyin": "chīfàn", "english": "to eat a meal"},
                {"char": "上班", "pinyin": "shàngbān", "english": "to go to work"}
            ],
            "grammar": [
                "Time words usually come after the subject or at the beginning of the sentence.",
                "Structure: Subject + Time + Verb + Object."
            ],
            "exercises": [
                {
                    "type": "multiple_choice",
                    "question": "Which word means 'to get up'?",
                    "options": ["吃饭", "起床", "上班", "睡觉"],
                    "answer": "起床"
                }
            ]
        }
    ],
    "HSK3": [
        {
            "id": 1,
            "title": "Expressing Experiences",
            "vocabulary": [
                {"char": "过", "pinyin": "guò", "english": "indicates past experience"},
                {"char": "去过", "pinyin": "qù guo", "english": "have been to"},
                {"char": "中国", "pinyin": "Zhōngguó", "english": "China"},
                {"char": "旅游", "pinyin": "lǚyóu", "english": "to travel"},
                {"char": "意思", "pinyin": "yìsi", "english": "meaning / interest"}
            ],
            "grammar": [
                "The particle 'guo' (过) is used after a verb to indicate that an action has been experienced in the past.",
                "Negative form: 'méiyǒu' (没有) + Verb + 'guo' (过)."
            ],
            "exercises": [
                {
                    "type": "translation",
                    "question": "I have been to China.",
                    "answer": "我去过中国",
                    "options": ["我去中国", "我去过中国", "我想去中国"]
                }
            ]
        }
    ]
}

def get_levels() -> List[str]:
    """Returns a list of available difficulty levels."""
    return list(LESSONS.keys())

def get_lessons_by_level(level: str) -> List[Dict[str, Any]]:
    """Returns all lessons for a specific level."""
    return LESSONS.get(level.upper(), [])

def get_lesson_content(level: str, lesson_id: int) -> Optional[Dict[str, Any]]:
    """Retrieves specific lesson content by level and ID."""
    lessons = get_lessons_by_level(level)
    for lesson in lessons:
        if lesson["id"] == lesson_id:
            return lesson
    return None

def get_vocabulary_list(level: str, lesson_id: int) -> List[Dict[str, str]]:
    """Returns the vocabulary list for a specific lesson."""
    lesson = get_lesson_content(level, lesson_id)
    return lesson["vocabulary"] if lesson else []

def get_exercises(level: str, lesson_id: int) -> List[Dict[str, Any]]:
    """Returns the exercises for a specific lesson."""
    lesson = get_lesson_content(level, lesson_id)
    return lesson["exercises"] if lesson else []

if __name__ == "__main__":
    # Example usage/testing
    print(f"Available Levels: {get_levels()}")
    hsk1_lessons = get_lessons_by_level("HSK1")
    print(f"HSK1 Lesson 1 Title: {hsk1_lessons[0]['title']}")
    
    vocab = get_vocabulary_list("HSK1", 1)
    print(f"First word in HSK1 L1: {vocab[0]['char']} ({vocab[0]['pinyin']})")