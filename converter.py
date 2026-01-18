"""
MKV to MP4 conversion with subtitle extraction
"""
import os
import subprocess
import json
from media_handler import MediaHandler


def convert_mkv_to_mp4(mkv_path):
    """
    Convert MKV file to MP4 and extract embedded subtitles.
    
    Args:
        mkv_path: Path to the MKV file
    
    Returns:
        str: Path to the output MP4 file
    """
    print(f"Converting MKV to MP4: {mkv_path}")
    
    directory = os.path.dirname(mkv_path)
    basename = os.path.splitext(os.path.basename(mkv_path))[0]
    output_mp4 = os.path.join(directory, f"{basename}.mp4")
    
    # Extract subtitles first
    extract_subtitles(mkv_path)
    
    # Convert video to MP4
    print(f"Converting video to MP4: {output_mp4}")
    cmd = [
        'ffmpeg',
        '-i', mkv_path,
        '-map', '0:v',  # Map video streams
        '-map', '0:a',  # Map audio streams
        '-codec', 'copy',  # Copy without re-encoding
        '-y',  # Overwrite output file
        output_mp4
    ]
    
    print(f"Running: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        print("Video conversion complete")
        print(result.stderr[-500:] if len(result.stderr) > 500 else result.stderr)
    except subprocess.CalledProcessError as e:
        print(f"FFmpeg error: {e.stderr}")
        raise Exception(f"Video conversion failed: {e.stderr[-500:]}")
    
    return output_mp4


def extract_subtitles(mkv_path):
    """
    Extract all subtitle streams from MKV file.
    
    Args:
        mkv_path: Path to the MKV file
    """
    print(f"Extracting subtitles from: {mkv_path}")
    
    directory = os.path.dirname(mkv_path)
    basename = os.path.splitext(os.path.basename(mkv_path))[0]
    
    # Get subtitle stream information
    media_handler = MediaHandler()
    embedded_subs, _ = media_handler.analyze_file(mkv_path)
    
    if not embedded_subs:
        print("No embedded subtitles found")
        return
    
    # Extract each subtitle stream
    for i, sub in enumerate(embedded_subs):
        language = sub['language']
        stream_index = sub['index']
        
        # Generate output filename
        output_file = get_unique_subtitle_path(directory, basename, language)
        
        print(f"Extracting subtitle stream {stream_index} ({language}) to: {output_file}")
        
        cmd = [
            'ffmpeg',
            '-i', mkv_path,
            '-map', f"0:{stream_index}",
            '-c:s', 'srt',  # Convert to SRT format
            '-y',  # Overwrite
            output_file
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            print(f"  Extracted: {os.path.basename(output_file)}")
        except subprocess.CalledProcessError as e:
            print(f"  Error extracting subtitle: {e.stderr}")
            # Continue with other subtitles even if one fails


def get_unique_subtitle_path(directory, basename, language):
    """
    Get a unique subtitle file path, adding -1, -2, etc. if file exists.
    
    Args:
        directory: Directory path
        basename: Base filename without extension
        language: Language code
    
    Returns:
        str: Unique file path
    """
    # Try base name first
    output_file = os.path.join(directory, f"{basename}.{language}.srt")
    
    if not os.path.exists(output_file):
        return output_file
    
    # If exists, try with -1, -2, etc.
    counter = 1
    while True:
        output_file = os.path.join(directory, f"{basename}.{language}-{counter}.srt")
        if not os.path.exists(output_file):
            return output_file
        counter += 1
        
        # Safety limit
        if counter > 100:
            raise Exception(f"Too many subtitle files with language {language}")


def extract_single_subtitle(video_path, stream_index, language, output_dir):
    """
    Extract a single subtitle stream to a temporary directory.
    
    Args:
        video_path: Path to the video file
        stream_index: Stream index to extract
        language: Language code for naming
        output_dir: Directory to save the extracted subtitle
    
    Returns:
        str: Path to the extracted subtitle file
    """
    basename = os.path.splitext(os.path.basename(video_path))[0]
    output_file = os.path.join(output_dir, f"{basename}.{language}.srt")
    
    print(f"Extracting subtitle stream {stream_index} to: {output_file}")
    
    cmd = [
        'ffmpeg',
        '-i', video_path,
        '-map', f"0:{stream_index}",
        '-c:s', 'srt',
        '-y',
        output_file
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        print(f"Extracted subtitle: {output_file}")
        return output_file
    except subprocess.CalledProcessError as e:
        raise Exception(f"Failed to extract subtitle: {e.stderr}")
