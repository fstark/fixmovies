# Samsung TV Media File Converter

A Linux GUI application that converts MKV/MP4 files and manages subtitles for Samsung TV compatibility.

## Features

- **Drag & Drop Interface**: Simply drag a video file (MKV or MP4) onto the window
- **Embedded Subtitle Detection**: Displays all embedded subtitles from MKV files
- **External Subtitle Scanning**: Finds and analyzes .srt subtitle files
- **Language Detection**: Automatically detects English and French subtitles
- **MKV Conversion**: Converts MKV to MP4 and extracts embedded subtitles
- **Subtitle Normalization**: Renames subtitles to 2-letter ISO language codes
- **Smart Default Selection**: Automatically selects the best subtitle (French > English)
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

#### For MKV files:
1. Drag and drop an MKV file onto the window
2. Review embedded and external subtitles
3. Click "Convert to MP4"
4. The app will:
   - Extract all embedded subtitles as separate .srt files
   - Convert the video to MP4 (no re-encoding, fast)
   - Reload the interface with the MP4 file

#### For MP4 files:
1. Drag and drop an MP4 file onto the window
2. Review external subtitles
3. Click "Go (Finalize)"
4. The app will:
   - Rename all subtitles to `.lang.srt` format (e.g., `movie.fr.srt`, `movie.en.srt`)
   - Copy the best subtitle as `movie.srt` (French preferred, English fallback)
   - Handle multiple subtitles of the same language with numbering (e.g., `movie.fr-1.srt`, `movie.fr-2.srt`)

### Result

After processing, you'll have:
- `movie.mp4` - The video file (Samsung TV compatible)
- `movie.srt` - The default subtitle (French or English)
- `movie.fr.srt`, `movie.en.srt`, etc. - All subtitles with language codes

## How It Works

### MKV Conversion
- Uses `ffmpeg` with `-codec copy` for fast, lossless conversion
- Extracts subtitles and converts them to SRT format
- Automatically handles naming conflicts

### Language Detection
- Uses the `langdetect` library for accurate language identification
- Supports English and French
- Falls back to `und` (undefined) for unrecognized languages

### Subtitle Normalization
- Converts 3-letter language codes to 2-letter ISO codes
- Ensures Samsung TV compatibility
- Maintains all subtitle variants with proper numbering

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
