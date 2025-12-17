# bilingual_book_maker

AI translation tool for creating multi-language epub/txt files and books. Uses various AI models (ChatGPT, Claude, Gemini, etc.) to translate content.

## Commands

- **Run translation**: `python3 make_book.py --book_name "test_books/animal_farm.epub" --language "zh-hans"`
- **Help**: `python3 make_book.py --help`
- **Install dependencies**: `pip install -r requirements.txt` or `pdm install`
- **Format**: `make fmt` (uses black)
- **Test**: `make tests` (runs integration tests)

## Codebase

- `make_book.py`: Entry point script.
- `book_maker/`: Core package.
  - `cli.py`: Command line interface parsing and orchestration.
  - `loader/`: Book loaders for different formats (epub, txt, srt, etc).
  - `translator/`: Translation model implementations and API clients.
- `tests/`: Integration tests.
