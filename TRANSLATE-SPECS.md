Here's the minimal set of instructions to reproduce the final program:

---

**Create a Python command-line tool srt_translate.py that translates SRT subtitle files:**

**Requirements:**
- Usage: `srt_translate.py <target_lang> <subfile>`
  - `target_lang`: target language (e.g., "french")
  - `subfile`: path to the SRT file
- Use OpenAI API with API key from `OPENAI_API_KEY` environment variable
- Use `gpt-4o-mini` model with temperature 0.3
- Strip all HTML tags from input subtitles before translation
- Process all subtitle entries (no line limit)
- Translate in batches of 10 entries at a time
- Output filename: `<original_name>.<target_lang>.srt`
- Preserve SRT structure: sequence numbers, timestamps, and blank lines between entries

**Implementation details:**
- Parse SRT format: blocks separated by blank lines, each with index, timestamp, and text
- Remove all HTML-like tags (matching `<[^>]+>`) from subtitle text
- Send numbered list to OpenAI for batch translation
- Parse numbered responses back to maintain order
- System prompt: "You are a professional subtitle translator. Translate to {target_lang} while preserving subtitle timing and formatting."
- User prompt: Ask to translate with preserved numbering and line breaks

---

That's it - these instructions would recreate the exact program we have now.