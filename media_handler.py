"""
Media file analysis and subtitle handling
"""
import os
import json
import subprocess
from langdetect import detect, LangDetectException


class MediaHandler:
    """Handles media file analysis and subtitle detection."""
    
    def analyze_file(self, file_path):
        """
        Analyze a media file and return embedded and external subtitles.
        
        Returns:
            tuple: (embedded_subtitles, external_subtitles)
                Each is a list of dicts with 'language' and 'size' keys.
        """
        print(f"Analyzing file: {file_path}")
        
        embedded_subs = self._get_embedded_subtitles(file_path)
        external_subs = self._get_external_subtitles(file_path)
        
        print(f"Found {len(embedded_subs)} embedded subtitles, {len(external_subs)} external subtitles")
        
        return embedded_subs, external_subs
    
    def _get_embedded_subtitles(self, file_path):
        """Get embedded subtitles from video file using ffprobe."""
        subtitles = []
        
        try:
            # Use ffprobe to get subtitle stream information
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_streams',
                '-select_streams', 's',
                file_path
            ]
            
            print(f"Running: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            data = json.loads(result.stdout)
            
            for stream in data.get('streams', []):
                # Get language from stream tags
                tags = stream.get('tags', {})
                language = tags.get('language', 'und')
                
                # Normalize language code to 2 letters
                if len(language) > 2:
                    # Try to convert 3-letter codes to 2-letter
                    language = self._normalize_language_code(language)
                
                # Estimate size (not directly available from ffprobe)
                size = 'embedded'
                
                subtitles.append({
                    'language': language,
                    'size': size,
                    'index': stream.get('index', 0)
                })
                
                print(f"  Embedded subtitle: {language} (index {stream.get('index')})")
        
        except subprocess.CalledProcessError as e:
            print(f"Error running ffprobe: {e}")
        except json.JSONDecodeError as e:
            print(f"Error parsing ffprobe output: {e}")
        except Exception as e:
            print(f"Unexpected error getting embedded subtitles: {e}")
        
        return subtitles
    
    def _get_external_subtitles(self, file_path):
        """Get external .srt subtitle files in the same directory."""
        subtitles = []
        
        directory = os.path.dirname(file_path)
        basename = os.path.splitext(os.path.basename(file_path))[0]
        
        try:
            # Find all .srt files that match the base name
            for filename in os.listdir(directory):
                if not filename.endswith('.srt'):
                    continue
                
                # Check if it matches the pattern: basename.*.srt or basename.srt
                file_base = filename.replace('.srt', '')
                
                if file_base == basename or file_base.startswith(basename + '.'):
                    full_path = os.path.join(directory, filename)
                    
                    # Detect language from content
                    language = self._detect_subtitle_language(full_path)
                    
                    # Get file size
                    size = self._format_file_size(os.path.getsize(full_path))
                    
                    subtitles.append({
                        'language': language,
                        'size': size,
                        'filename': filename,
                        'path': full_path
                    })
                    
                    print(f"  External subtitle: {filename} - {language} ({size})")
        
        except Exception as e:
            print(f"Error scanning for external subtitles: {e}")
        
        return subtitles
    
    def _detect_subtitle_language(self, srt_path):
        """Detect language of an SRT file using langdetect."""
        try:
            with open(srt_path, 'r', encoding='utf-8', errors='ignore') as f:
                # Read a sample of the file (first 5000 chars should be enough)
                content = f.read(5000)
                
                # Remove subtitle timestamps and numbers
                lines = content.split('\n')
                text_lines = []
                for line in lines:
                    line = line.strip()
                    # Skip empty lines, numbers, and timestamp lines
                    if line and not line.isdigit() and '-->' not in line:
                        text_lines.append(line)
                
                text = ' '.join(text_lines)
                
                if text:
                    detected = detect(text)
                    print(f"    Detected language: {detected}")
                    return detected
                else:
                    print(f"    No text found in subtitle")
                    return 'und'
        
        except LangDetectException as e:
            print(f"    Language detection failed: {e}")
            return 'und'
        except Exception as e:
            print(f"    Error reading subtitle file: {e}")
            return 'und'
    
    def _normalize_language_code(self, code):
        """Normalize 3-letter language codes to 2-letter ISO codes."""
        # Common 3-letter to 2-letter mappings
        mapping = {
            'eng': 'en',
            'fra': 'fr',
            'fre': 'fr',
            'ger': 'de',
            'deu': 'de',
            'spa': 'es',
            'ita': 'it',
            'por': 'pt',
            'rus': 'ru',
            'jpn': 'ja',
            'chi': 'zh',
            'zho': 'zh',
            'ara': 'ar',
            'hin': 'hi',
            'und': 'und',
        }
        
        return mapping.get(code.lower(), code[:2])
    
    def _format_file_size(self, size_bytes):
        """Format file size in human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
