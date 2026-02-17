markdown
# Chinese Tutor AI

An interactive, AI-powered language learning application designed to help users master Mandarin Chinese through structured lessons, real-time conversation practice, and persistent progress tracking.

## Features

- **Structured Lessons**: Comprehensive curriculum covering vocabulary, grammar, and cultural context via `lessons.py`.
- **AI Tutoring**: Interactive chat interface powered by Large Language Models (LLMs) to practice conversation.
- **Memory Persistence**: Utilizes ChromaDB (`memory_db/`) to remember user progress, past mistakes, and learning preferences.
- **State Management**: Robust session handling using SQLite checkpoints to ensure learning continuity.
- **Configurable Experience**: Easily adjustable settings for difficulty levels and API integrations via `config.yml`.

## Project Structure