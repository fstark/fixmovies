Original plan from Claude 4.5


Plan: Samsung TV Media File Converter
A Linux GUI application using Python with PyGObject (GTK) that converts MKV/MP4 files and manages subtitles for Samsung TV compatibility. Uses ffmpeg with -codec copy for fast conversion, converts all subtitle formats to SRT, overwrites existing files, uses movie.fr-1.srt numbering format with .und.srt for unknown languages, and accepts any langdetect result.

Steps
Create project structure and dependencies with requirements.txt including PyGObject and langdetect, organize code into: main.py, media_handler.py, converter.py, subtitle_utils.py, ui_components.py

Implement startup and main window in main.py and ui_components.py to check ffmpeg/VLC with shutil.which() and show error dialog if missing, create GTK window with drag-and-drop zone accepting .mkv/.mp4 files, display clickable media filename launching VLC via subprocess.Popen(['vlc', filepath]), show two subtitle lists with language and size columns, add conditional "Convert" or "Go" button that disables during processing with status label

Build media analysis module in media_handler.py to probe embedded subtitles with ffprobe -show_streams -select_streams s -of json, extract language codes from stream metadata, scan directory for .srt files matching basename, detect language using langdetect accepting any result or fallback to und on exception, calculate file sizes with os.path.getsize(), log operations to console

Implement MKV conversion workflow in converter.py to extract each subtitle stream with ffmpeg -i input.mkv -map 0:s:N -c:s srt output.lang.srt, detect language and use movie.lang.srt or movie.lang-1.srt for collisions, convert video with ffmpeg -i input.mkv -codec copy -map 0:v -map 0:a output.mp4 -y for overwrite, disable button during processing, show error dialog on failure, log operations, reload UI with MP4

Build MP4 finalization workflow in subtitle_utils.py to detect language of external .srt files using langdetect, rename to basename.lang.srt format with numbering basename.lang-1.srt for duplicates, copy French subtitle as basename.srt or fallback to English if no French exists, disable button during processing, overwrite files, log operations, show completion status

Add error handling and UI feedback across all modules to wrap ffmpeg/subprocess calls in try-except blocks, display GTK MessageDialog for errors, log details to console, disable Convert/Go buttons during operations with set_sensitive(False), show status label ("Processing...", "Complete", "Error"), re-enable buttons after completion or error

Further Considerations
None - the plan is ready for implementation with all requirements clarified.

