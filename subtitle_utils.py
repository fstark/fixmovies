"""
Subtitle processing and finalization for MP4 files
"""
import os
import shutil
from collections import defaultdict
from media_handler import MediaHandler


def process_mp4_subtitles(mp4_path):
    """
    Process subtitles for MP4 file:
    1. Rename all external subtitles to .lang.srt format
    2. Copy best subtitle (French > English) as .srt without language code
    
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
    
    # Copy best subtitle as default .srt
    copy_best_subtitle(renamed_subs, basename, directory)
    
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


def copy_best_subtitle(renamed_subs, basename, directory):
    """
    Copy the best subtitle (French > English) as basename.srt.
    
    Args:
        renamed_subs: List of renamed subtitle dicts
        basename: Base filename without extension
        directory: Directory path
    """
    print("Copying best subtitle as default .srt...")
    
    # Find French subtitle first
    french_sub = None
    english_sub = None
    
    for sub in renamed_subs:
        if sub['language'] == 'fr' and not french_sub:
            french_sub = sub
        elif sub['language'] == 'en' and not english_sub:
            english_sub = sub
    
    # Choose best subtitle
    best_sub = french_sub if french_sub else english_sub
    
    if not best_sub:
        print("  No French or English subtitle found")
        return
    
    # Copy to basename.srt
    source_path = best_sub['path']
    dest_path = os.path.join(directory, f"{basename}.srt")
    
    try:
        print(f"  Copying: {best_sub['filename']} -> {basename}.srt")
        shutil.copy2(source_path, dest_path)
        print(f"  Default subtitle set: {best_sub['language']}")
    except Exception as e:
        print(f"  Error copying default subtitle: {e}")
