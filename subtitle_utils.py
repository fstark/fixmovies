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
    1. Rename all external subtitles to .lang.srt format
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
    
    # Rename all subtitles to .lang.srt format
    renamed_subs = rename_subtitles_with_language(external_subs, basename, directory)
    
    # Remove duplicate subtitles
    remove_duplicate_subtitles(renamed_subs)
    
    print("Subtitle processing complete")


def rename_subtitles_with_language(external_subs, basename, directory):
    """
    Rename all external subtitles to follow .lang.srt or .lang-N.srt format.
    
    Args:
        external_subs: List of external subtitle dicts
        basename: Base filename without extension
        directory: Directory path
    
    Returns:
        list: List of renamed subtitle dicts with updated paths
    """
    print("Renaming subtitles to .lang.srt format...")
    
    # Group subtitles by language
    lang_groups = defaultdict(list)
    for sub in external_subs:
        lang_groups[sub['language']].append(sub)
    
    renamed_subs = []
    
    for language, subs in lang_groups.items():
        for i, sub in enumerate(subs):
            old_path = sub['path']
            old_filename = sub['filename']
            
            # Generate new filename
            if i == 0 and len(subs) == 1:
                # Single subtitle of this language
                new_filename = f"{basename}.{language}.srt"
            else:
                # Multiple subtitles of same language
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
