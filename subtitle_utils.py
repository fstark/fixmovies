"""
Subtitle processing and finalization for MP4 files
"""
import os
import shutil
import hashlib
from collections import defaultdict
from media_handler import MediaHandler


def process_mp4_subtitles(mp4_path):
    """
    Process subtitles for MP4 file:
    1. Rename subtitles intelligently (French as default, English if no French)
    2. Remove duplicate subtitles (same content)
    
    Args:
        mp4_path: Path to the MP4 file
    """
    print(f"Processing subtitles for: {mp4_path}")
    
    directory = os.path.dirname(mp4_path)
    basename = os.path.splitext(os.path.basename(mp4_path))[0]
    
    # Get external subtitles
    media_handler = MediaHandler()
    _, external_subs = media_handler.analyze_file(mp4_path)
    
    if not external_subs:
        print("No external subtitles found")
        return
    
    # Rename all subtitles intelligently
    renamed_subs = rename_subtitles_with_language(external_subs, basename, directory)
    
    # Remove duplicate subtitles
    remove_duplicate_subtitles(renamed_subs)
    
    print("Subtitle processing complete")


def rename_subtitles_with_language(external_subs, basename, directory):
    """
    Rename subtitles intelligently:
    - If only FR or only EN: first one -> basename.srt, others -> basename.lang-N.srt
    - If both FR and EN: FR -> basename.srt, EN -> basename.en.srt (or -N for multiples)
    - Other languages: always keep language code
    
    Args:
        external_subs: List of external subtitle dicts
        basename: Base filename without extension
        directory: Directory path
    
    Returns:
        list: List of renamed subtitle dicts with updated paths
    """
    print("Renaming subtitles...")
    
    # Group subtitles by language
    lang_groups = defaultdict(list)
    for sub in external_subs:
        lang_groups[sub['language']].append(sub)
    
    # Determine naming strategy
    has_french = 'fr' in lang_groups
    has_english = 'en' in lang_groups
    
    renamed_subs = []
    
    for language, subs in lang_groups.items():
        for i, sub in enumerate(subs):
            old_path = sub['path']
            old_filename = sub['filename']
            
            # Determine new filename
            if language == 'fr':
                if i == 0 and len(subs) == 1:
                    # First (or only) French subtitle becomes the default .srt
                    new_filename = f"{basename}.srt"
                elif i == 0:
                    # First of multiple French subtitles
                    new_filename = f"{basename}.fr-1.srt"
                else:
                    # Additional French subtitles
                    new_filename = f"{basename}.fr-{i+1}.srt"
            elif language == 'en':
                if i == 0 and len(subs) == 1 and not has_french:
                    # Only English subtitle and no French -> becomes default .srt
                    new_filename = f"{basename}.srt"
                elif i == 0 and len(subs) == 1:
                    # Single English subtitle but French exists -> keep language code
                    new_filename = f"{basename}.en.srt"
                elif i == 0:
                    # First of multiple English subtitles
                    new_filename = f"{basename}.en-1.srt"
                else:
                    # Additional English subtitles
                    new_filename = f"{basename}.en-{i+1}.srt"
            else:
                # Other languages: always keep language code
                if i == 0 and len(subs) == 1:
                    new_filename = f"{basename}.{language}.srt"
                else:
                    new_filename = f"{basename}.{language}-{i+1}.srt"
            
            new_path = os.path.join(directory, new_filename)
            
            # Skip if already correctly named
            if old_path == new_path:
                print(f"  Already correct: {new_filename}")
                renamed_subs.append({
                    'language': language,
                    'path': new_path,
                    'filename': new_filename
                })
                continue
            
            # Rename file
            try:
                print(f"  Renaming: {old_filename} -> {new_filename}")
                shutil.move(old_path, new_path)
                renamed_subs.append({
                    'language': language,
                    'path': new_path,
                    'filename': new_filename
                })
            except Exception as e:
                print(f"  Error renaming {old_filename}: {e}")
                # Keep original on error
                renamed_subs.append(sub)
    
    return renamed_subs


def remove_duplicate_subtitles(subtitle_list):
    """
    Remove duplicate subtitle files (same content).
    Keep the first occurrence, delete the rest.
    
    Args:
        subtitle_list: List of subtitle dicts with 'path' key
    """
    print("Checking for duplicate subtitles...")
    
    # Dictionary to store hash -> first file with that hash
    hash_to_file = {}
    files_to_delete = []
    
    for sub in subtitle_list:
        file_path = sub['path']
        
        if not os.path.exists(file_path):
            continue
        
        # Calculate file hash
        file_hash = calculate_file_hash(file_path)
        
        if file_hash in hash_to_file:
            # Duplicate found
            original = hash_to_file[file_hash]
            print(f"  Duplicate found: {sub['filename']} (same as {os.path.basename(original)})")
            files_to_delete.append(file_path)
        else:
            # First occurrence of this content
            hash_to_file[file_hash] = file_path
    
    # Delete duplicate files
    for file_path in files_to_delete:
        try:
            print(f"  Deleting duplicate: {os.path.basename(file_path)}")
            os.remove(file_path)
        except Exception as e:
            print(f"  Error deleting {os.path.basename(file_path)}: {e}")
    
    if not files_to_delete:
        print("  No duplicates found")
    else:
        print(f"  Removed {len(files_to_delete)} duplicate subtitle(s)")


def calculate_file_hash(file_path):
    """
    Calculate SHA256 hash of a file.
    
    Args:
        file_path: Path to the file
    
    Returns:
        str: Hexadecimal hash string
    """
    sha256_hash = hashlib.sha256()
    
    try:
        with open(file_path, 'rb') as f:
            # Read file in chunks to handle large files
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        print(f"Error calculating hash for {file_path}: {e}")
        # Return a unique value if hash fails
        return f"error_{file_path}"
