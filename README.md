# Samsung TV Media File Converter

A Linux GUI application that converts MKV/MP4 files and manages subtitles for Samsung TV compatibility.

## Features

- **Drag & Drop Interface**: Simply drag a video file (MKV or MP4) anywhere in the window
- **Embedded Subtitle Detection**: Displays all embedded subtitles from MKV files
- **External Subtitle Scanning**: Finds and analyzes .srt subtitle files
- **Language Detection**: Automatically detects English and French subtitles using langdetect
- **MKV Conversion**: Converts MKV to MP4 and extracts embedded subtitles
- **Auto-Delete MKV**: Moves original MKV to .Trash or prompts for deletion
- **Subtitle Normalization**: Renames all subtitles to 2-letter ISO language codes (.lang.srt)
- **Duplicate Detection**: Automatically removes duplicate subtitle files
- **Auto-Convert Mode**: Optional checkbox to process files automatically on drop
- **Auto-Reload**: Detects new subtitle files when window gains focus
- **VLC Integration**: Click the filename to open the video in VLC

## Requirements

- Linux operating system
- Python 3.8+
- GTK 3
- FFmpeg
- VLC media player

## Installation

1. Install system dependencies:
```bash
sudo apt-get update
sudo apt-get install python3 python3-venv python3-gi python3-gi-cairo gir1.2-gtk-3.0 ffmpeg vlc
```

2. Clone or download this repository

3. Create a virtual environment and install Python dependencies:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

Run the application:
```bash
./run.sh
```

Or manually:
```bash
source .venv/bin/activate
python3 main.py
```

### Workflow

#### Basic Usage:
1. Drag and drop a video file (MKV or MP4) anywhere in the window
2. Review embedded and external subtitles
3. Click "Cleanup" to process

#### Auto-Convert Mode:
- Check the "Auto-convert" checkbox
- Drop a file - it will be processed automatically

#### What Happens During Cleanup:

**For MKV files:**
1. Extracts all embedded subtitles as separate .srt files
2. Converts video to MP4 (no re-encoding, fast)
3. Deletes the original MKV file:
   - Moves to `.Trash` folder if available
   - Otherwise prompts for confirmation before deletion
4. Continues with subtitle cleanup (see below)

**For all files (MKV and MP4):**
1. Renames all subtitles to `.lang.srt` format (e.g., `movie.fr.srt`, `movie.en.srt`)
2. Handles multiple subtitles of the same language with numbering (e.g., `movie.fr-1.srt`, `movie.fr-2.srt`)
3. Removes duplicate subtitle files (same content)

### Result

After processing, you'll have:
- `movie.mp4` - The video file (Samsung TV compatible)
- `movie.fr.srt`, `movie.en.srt`, etc. - All unique subtitles with 2-letter language codes

## How It Works

### MKV Conversion
- Uses `ffmpeg` with `-codec copy` for fast, lossless conversion
- Extracts subtitles and converts them to SRT format
- Automatically handles naming conflicts
- Deletes original MKV after successful conversion

### Language Detection
- Uses the `langdetect` library for accurate language identification
- Supports English and French
- Falls back to `und` (undefined) for unrecognized languages

### Subtitle Normalization
- Converts 3-letter language codes to 2-letter ISO codes
- Ensures Samsung TV compatibility
- Maintains all subtitle variants with proper numbering

### Duplicate Detection
- Calculates SHA256 hash of each subtitle file
- Removes files with identical content
- Keeps the first occurrence, deletes the rest

### Auto-Reload on Focus
- When the window gains focus, checks for new subtitle files
- Automatically reloads the file if subtitles have changed
- Useful when adding subtitles from other sources

## Troubleshooting

### Missing Dependencies Error
If you see an error about missing `ffmpeg` or `vlc`, install them:
```bash
sudo apt-get install ffmpeg vlc
```

### Import Errors
If you get Python import errors, ensure you're using the virtual environment:
```bash
source .venv/bin/activate
python3 main.py
```

### GTK Warnings
GTK warnings are usually harmless and can be ignored. The application should work normally.

## File Structure

- `main.py` - Application entry point and dependency checks
- `ui_components.py` - GTK window and user interface
- `media_handler.py` - Media file analysis and subtitle detection
- `converter.py` - MKV to MP4 conversion
- `subtitle_utils.py` - Subtitle processing and finalization
- `requirements.txt` - Python dependencies
- `run.sh` - Convenience script to run the application

## License

This project is open source and available for personal use.
