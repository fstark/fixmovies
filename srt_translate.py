#!/usr/bin/env python3
"""
SRT Subtitle Translator using OpenAI API
Usage: srt_translate.py <target_lang> <subfile> [-o output_file]
"""
import os
import sys
import re
import argparse
from openai import OpenAI


def parse_srt(srt_content):
    """
    Parse SRT file into structured entries.
    Returns list of dicts with: index, timestamp, text
    """
    entries = []
    blocks = srt_content.strip().split('\n\n')
    
    for block in blocks:
        lines = block.strip().split('\n')
        if len(lines) < 3:
            continue
        
        # First line: sequence number
        try:
            index = int(lines[0].strip())
        except ValueError:
            continue
        
        # Second line: timestamp
        timestamp = lines[1].strip()
        if '-->' not in timestamp:
            continue
        
        # Remaining lines: subtitle text
        text = '\n'.join(lines[2:])
        
        entries.append({
            'index': index,
            'timestamp': timestamp,
            'text': text
        })
    
    return entries


def strip_tags(text):
    """
    Strip all HTML-like tags from text.
    Returns clean text for translation.
    """
    # Remove all HTML-like tags (e.g., <font>, <i>, <b>, etc.)
    tag_pattern = r'<[^>]+>'
    clean_text = re.sub(tag_pattern, '', text)
    return clean_text


def translate_batch(texts, target_lang, client):
    """
    Translate a batch of texts using OpenAI API.
    """
    if not texts:
        return []
    
    # Prepare texts with indices to maintain order
    numbered_texts = [f"{i+1}. {text}" for i, text in enumerate(texts)]
    batch_text = '\n'.join(numbered_texts)
    
    prompt = f"""Translate the following subtitle lines to {target_lang}. 
Preserve the numbering format. Maintain the meaning and natural flow for subtitles.
Keep line breaks as they are. Do not translate HTML tags.

{batch_text}"""
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": f"You are a professional subtitle translator. Translate to {target_lang} while preserving subtitle timing and formatting."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        
        translated = response.choices[0].message.content.strip()
        
        # Parse numbered responses
        lines = translated.split('\n')
        results = []
        current_text = []
        
        for line in lines:
            # Check if line starts with a number
            match = re.match(r'^(\d+)\.\s+(.*)$', line)
            if match:
                if current_text:
                    results.append('\n'.join(current_text))
                    current_text = []
                current_text.append(match.group(2))
            else:
                if current_text:
                    current_text.append(line)
        
        if current_text:
            results.append('\n'.join(current_text))
        
        return results
    
    except Exception as e:
        print(f"Error during translation: {e}")
        return texts  # Return original on error


def translate_srt(srt_file, target_lang, limit=None, output_file=None):
    """
    Translate an SRT file to target language.
    
    Args:
        srt_file: Path to input SRT file
        target_lang: Target language (e.g., 'french', 'spanish')
        limit: Optional limit on number of entries to translate (for testing)
        output_file: Optional output file path (default: input_file.target_lang.srt)
    """
    # Check API key
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable not set")
        sys.exit(1)
    
    client = OpenAI(api_key=api_key)
    
    # Read SRT file
    try:
        with open(srt_file, 'r', encoding='utf-8') as f:
            srt_content = f.read()
    except FileNotFoundError:
        print(f"Error: File '{srt_file}' not found")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading file: {e}")
        sys.exit(1)
    
    # Parse SRT
    entries = parse_srt(srt_content)
    print(f"Found {len(entries)} subtitle entries")
    
    # Limit for testing
    if limit:
        entries = entries[:limit]
        print(f"Processing first {len(entries)} entries (test mode)")
    
    # Translate in batches
    batch_size = 10
    translated_entries = []
    
    for i in range(0, len(entries), batch_size):
        batch = entries[i:i+batch_size]
        print(f"Translating entries {i+1}-{min(i+batch_size, len(entries))}...")
        
        # Extract clean texts (strip tags)
        texts = []
        for entry in batch:
            clean_text = strip_tags(entry['text'])
            texts.append(clean_text)
        
        # Translate batch
        translated_texts = translate_batch(texts, target_lang, client)
        
        # Create new entries with translated text (no tags)
        for j, entry in enumerate(batch):
            if j < len(translated_texts):
                translated_entries.append({
                    'index': entry['index'],
                    'timestamp': entry['timestamp'],
                    'text': translated_texts[j]
                })
    
    # Generate output filename
    if output_file is None:
        base_name = os.path.splitext(srt_file)[0]
        output_file = f"{base_name}.{target_lang}.srt"
    
    # Write translated SRT
    with open(output_file, 'w', encoding='utf-8') as f:
        for entry in translated_entries:
            f.write(f"{entry['index']}\n")
            f.write(f"{entry['timestamp']}\n")
            f.write(f"{entry['text']}\n")
            f.write('\n')
    
    print(f"Translation complete! Output: {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description='Translate SRT subtitle files using OpenAI API',
        usage='%(prog)s <target_lang> <subfile> [-o OUTPUT]'
    )
    parser.add_argument('target_lang', help='Target language (e.g., french, spanish)')
    parser.add_argument('subfile', help='Input SRT file')
    parser.add_argument('-o', '--output', dest='output_file', 
                        help='Output file (default: input.target_lang.srt)')
    
    args = parser.parse_args()
    
    translate_srt(args.subfile, args.target_lang, output_file=args.output_file)


if __name__ == '__main__':
    main()
