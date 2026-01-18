"""
UI Components for Samsung TV Media File Converter
"""
import os
import subprocess
import tempfile
import shutil
import threading
import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib

from media_handler import MediaHandler, TARGET_LANGUAGE
from converter import convert_mkv_to_mp4, extract_single_subtitle
from subtitle_utils import process_mp4_subtitles


class MainWindow(Gtk.Window):
    """Main application window."""
    
    def __init__(self):
        super().__init__(title="Samsung TV Media File Converter")
        self.set_default_size(800, 600)
        self.set_border_width(20)
        
        self.current_file = None
        self.media_handler = MediaHandler()
        self.last_subtitle_list = []
        self.embedded_subs = []
        self.external_subs = []
        
        self._build_ui()
        self._setup_drag_and_drop()
        
        # Set up focus event to check for new subtitles
        self.connect("focus-in-event", self._on_window_focus)
    
    def _build_ui(self):
        """Build the user interface."""
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.add(main_box)
        
        # Drop zone message (shown when no file loaded)
        self.drop_zone = Gtk.Label()
        self.drop_zone.set_markup("<span size='large' color='#999999'><i>Drop a video file anywhere in the window (MKV or MP4)</i></span>")
        self.drop_zone.set_size_request(-1, 30)
        main_box.pack_start(self.drop_zone, False, False, 10)
        
        # Media file section with auto-convert checkbox
        media_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=15)
        main_box.pack_start(media_box, False, False, 15)
        
        # Media file label (clickable)
        self.media_label = Gtk.Label()
        self.media_label.set_markup("<span size='large' weight='bold'>No file loaded</span>")
        self.media_label.set_selectable(True)
        self.media_label.set_halign(Gtk.Align.START)
        self.media_label.set_line_wrap(True)
        media_event_box = Gtk.EventBox()
        media_event_box.add(self.media_label)
        media_event_box.connect("button-press-event", self._on_media_label_clicked)
        media_event_box.set_above_child(True)
        media_box.pack_start(media_event_box, True, True, 0)
        
        # Auto-convert checkbox
        self.auto_convert_check = Gtk.CheckButton(label="⚡ Auto-convert")
        self.auto_convert_check.set_tooltip_text("Automatically process files when dropped")
        media_box.pack_start(self.auto_convert_check, False, False, 0)
        
        # Status label
        self.status_label = Gtk.Label()
        self.status_label.set_markup("<span color='#666666'><i>Ready</i></span>")
        main_box.pack_start(self.status_label, False, False, 5)
        
        # Embedded subtitles section
        embed_label = Gtk.Label()
        embed_label.set_markup("<span size='large' weight='bold'>📎 Embedded Subtitles</span>")
        embed_label.set_halign(Gtk.Align.START)
        main_box.pack_start(embed_label, False, False, 10)
        
        # Embedded subtitles list
        self.embedded_store = Gtk.ListStore(str, str, str, str, str)  # Language, Title, Format, Size, View
        self.embedded_view = Gtk.TreeView(model=self.embedded_store)
        self.embedded_view.get_selection().set_mode(Gtk.SelectionMode.SINGLE)
        self.embedded_view.get_selection().connect("changed", self._on_subtitle_selection_changed)
        
        lang_renderer = Gtk.CellRendererText()
        lang_column = Gtk.TreeViewColumn("Language", lang_renderer, text=0)
        self.embedded_view.append_column(lang_column)
        
        title_renderer = Gtk.CellRendererText()
        title_column = Gtk.TreeViewColumn("Title", title_renderer, text=1)
        self.embedded_view.append_column(title_column)
        
        format_renderer = Gtk.CellRendererText()
        format_column = Gtk.TreeViewColumn("Format", format_renderer, text=2)
        self.embedded_view.append_column(format_column)
        
        size_renderer = Gtk.CellRendererText()
        size_column = Gtk.TreeViewColumn("Size", size_renderer, text=3)
        self.embedded_view.append_column(size_column)
        
        view_renderer = Gtk.CellRendererText()
        view_column = Gtk.TreeViewColumn("👁", view_renderer, text=4)
        view_column.set_clickable(True)
        self.embedded_view.append_column(view_column)
        self.embedded_view.connect("row-activated", self._on_embedded_subtitle_activated)
        
        embed_scroll = Gtk.ScrolledWindow()
        embed_scroll.set_size_request(-1, 120)
        embed_scroll.set_shadow_type(Gtk.ShadowType.IN)
        embed_scroll.add(self.embedded_view)
        main_box.pack_start(embed_scroll, True, True, 5)
        
        # External subtitles section
        external_label = Gtk.Label()
        external_label.set_markup("<span size='large' weight='bold'>📄 External Subtitles</span>")
        external_label.set_halign(Gtk.Align.START)
        main_box.pack_start(external_label, False, False, 10)
        
        # External subtitles list
        self.external_store = Gtk.ListStore(str, str, str, str)  # Language, Format, Size, View
        self.external_view = Gtk.TreeView(model=self.external_store)
        self.external_view.get_selection().set_mode(Gtk.SelectionMode.SINGLE)
        self.external_view.get_selection().connect("changed", self._on_subtitle_selection_changed)
        
        lang_renderer2 = Gtk.CellRendererText()
        lang_column2 = Gtk.TreeViewColumn("Language", lang_renderer2, text=0)
        self.external_view.append_column(lang_column2)
        
        format_renderer2 = Gtk.CellRendererText()
        format_column2 = Gtk.TreeViewColumn("Format", format_renderer2, text=1)
        self.external_view.append_column(format_column2)
        
        size_renderer2 = Gtk.CellRendererText()
        size_column2 = Gtk.TreeViewColumn("Size", size_renderer2, text=2)
        self.external_view.append_column(size_column2)
        
        view_renderer2 = Gtk.CellRendererText()
        view_column2 = Gtk.TreeViewColumn("👁", view_renderer2, text=3)
        view_column2.set_clickable(True)
        self.external_view.append_column(view_column2)
        self.external_view.connect("row-activated", self._on_external_subtitle_activated)
        
        external_scroll = Gtk.ScrolledWindow()
        external_scroll.set_size_request(-1, 120)
        external_scroll.set_shadow_type(Gtk.ShadowType.IN)
        external_scroll.add(self.external_view)
        main_box.pack_start(external_scroll, True, True, 5)
        
        # Translate button
        self.translate_button = Gtk.Button(label="🌐 Translate Selected Subtitle to French")
        self.translate_button.set_size_request(-1, 40)
        self.translate_button.set_sensitive(False)  # Disabled until non-French subtitle is selected
        self.translate_button.connect("clicked", self._on_translate_button_clicked)
        main_box.pack_start(self.translate_button, False, False, 10)
        
        # Cleanup button (works for both MKV and MP4 files)
        self.cleanup_button = Gtk.Button(label="🧹 Cleanup & Optimize")
        self.cleanup_button.set_size_request(-1, 50)
        self.cleanup_button.set_sensitive(False)  # Disabled until file is loaded
        self.cleanup_button.connect("clicked", self._on_cleanup_button_clicked)
        main_box.pack_start(self.cleanup_button, False, False, 15)
    
    def _setup_drag_and_drop(self):
        """Setup drag and drop functionality for the entire window."""
        # Set up drag and drop on the entire window
        self.drag_dest_set(
            Gtk.DestDefaults.ALL,
            [],
            Gdk.DragAction.COPY
        )
        self.drag_dest_add_uri_targets()
        self.connect("drag-data-received", self._on_file_dropped)
    
    def _on_file_dropped(self, widget, drag_context, x, y, data, info, time):
        """Handle file drop event."""
        uris = data.get_uris()
        if uris:
            file_path = uris[0].replace('file://', '')
            # URL decode the path
            import urllib.parse
            file_path = urllib.parse.unquote(file_path)
            
            if file_path.lower().endswith(('.mkv', '.mp4')):
                print(f"File dropped: {file_path}")
                self.load_file(file_path)
                
                # Auto-convert if checkbox is checked
                if self.auto_convert_check.get_active():
                    print("Auto-convert is enabled, processing automatically...")
                    self._on_cleanup_button_clicked(None)
            else:
                self._show_error("Invalid file type. Please drop an MKV or MP4 file.")
    
    def load_file(self, file_path):
        """Load and analyze a media file."""
        print(f"Loading file: {file_path}")
        self.current_file = file_path
        
        # Update media label
        filename = os.path.basename(file_path)
        self.media_label.set_markup(
            f"<span size='large' weight='bold'>🎬 {filename}</span>\n"
            f"<span size='small' color='#666666'><i>Click to open in VLC</i></span>"
        )
        
        # Analyze file
        embedded_subs, external_subs = self.media_handler.analyze_file(file_path)
        
        # Store subtitle data for translation feature
        self.embedded_subs = embedded_subs
        self.external_subs = external_subs
        
        # Store current subtitle list for comparison
        self.last_subtitle_list = [sub['filename'] for sub in external_subs if 'filename' in sub]
        
        # Update embedded subtitles list
        self.embedded_store.clear()
        for sub in embedded_subs:
            self.embedded_store.append([sub['language'], sub.get('title', ''), sub['format'], sub['size'], '👁'])
        
        # Update external subtitles list
        self.external_store.clear()
        for sub in external_subs:
            self.external_store.append([sub['language'], sub['format'], sub['size'], '👁'])
        
        # Enable cleanup button
        self.cleanup_button.set_sensitive(True)
        
        self.status_label.set_markup("<i>Ready</i>")
    
    def _on_media_label_clicked(self, widget, event):
        """Launch VLC when media label is clicked."""
        if self.current_file and os.path.exists(self.current_file):
            print(f"Launching VLC for: {self.current_file}")
            try:
                subprocess.Popen(['vlc', self.current_file])
            except Exception as e:
                print(f"Error launching VLC: {e}")
                self._show_error(f"Failed to launch VLC: {e}")
    
    def _on_cleanup_button_clicked(self, button):
        """Handle cleanup button click (works for both MKV and MP4)."""
        if not self.current_file:
            return
        
        # Disable button during processing
        self.cleanup_button.set_sensitive(False)
        self.status_label.set_markup("<i>Processing...</i>")
        
        try:
            # If MKV, convert first then cleanup
            if self.current_file.lower().endswith('.mkv'):
                self._convert_and_cleanup_mkv()
            # If MP4, just cleanup subtitles
            elif self.current_file.lower().endswith('.mp4'):
                self._cleanup_subtitles()
        except Exception as e:
            print(f"Error during processing: {e}")
            self._show_error(f"Processing failed: {e}")
            self.cleanup_button.set_sensitive(True)
            self.status_label.set_markup("<i>Error</i>")
    
    def _convert_and_cleanup_mkv(self):
        """Convert MKV to MP4, delete MKV, and cleanup subtitles."""
        print("Starting MKV conversion and cleanup...")
        
        try:
            mkv_file = self.current_file
            output_file = convert_mkv_to_mp4(mkv_file)
            print(f"Conversion complete: {output_file}")
            
            # Delete the MKV file
            self._delete_mkv_file(mkv_file)
            
            # Reload with the new MP4 file
            self.load_file(output_file)
            
            # Now cleanup subtitles
            self._cleanup_subtitles()
            
        except Exception as e:
            raise
    
    def _cleanup_subtitles(self):
        """Cleanup MP4 subtitles: rename to .lang.srt format and remove duplicates."""
        print("Starting subtitle cleanup...")
        
        try:
            process_mp4_subtitles(self.current_file)
            print("Subtitle cleanup complete")
            self.status_label.set_markup("<i>Complete! Files ready for Samsung TV</i>")
            
            # Reload to show updated subtitles
            self.load_file(self.current_file)
        except Exception as e:
            raise
    
    def _delete_mkv_file(self, mkv_file):
        """Delete MKV file, either to .Trash or with confirmation."""
        import shutil
        
        directory = os.path.dirname(mkv_file)
        filename = os.path.basename(mkv_file)
        
        # Check for .Trash folder on the volume
        mount_point = self._get_mount_point(directory)
        trash_dir = os.path.join(mount_point, '.Trash')
        
        if os.path.exists(trash_dir) and os.path.isdir(trash_dir):
            # Move to trash
            try:
                trash_path = os.path.join(trash_dir, filename)
                # Handle name collision in trash
                counter = 1
                while os.path.exists(trash_path):
                    base, ext = os.path.splitext(filename)
                    trash_path = os.path.join(trash_dir, f"{base}_{counter}{ext}")
                    counter += 1
                
                print(f"Moving {mkv_file} to {trash_path}")
                shutil.move(mkv_file, trash_path)
                print(f"MKV file moved to trash")
            except Exception as e:
                print(f"Error moving to trash: {e}")
                self._show_error(f"Failed to move MKV to trash: {e}")
        else:
            # No trash folder, ask for confirmation
            dialog = Gtk.MessageDialog(
                transient_for=self,
                flags=0,
                message_type=Gtk.MessageType.QUESTION,
                buttons=Gtk.ButtonsType.YES_NO,
                text="Delete MKV file?"
            )
            dialog.format_secondary_text(
                f"No .Trash folder found. Permanently delete:\n{filename}?"
            )
            response = dialog.run()
            dialog.destroy()
            
            if response == Gtk.ResponseType.YES:
                try:
                    print(f"Deleting {mkv_file}")
                    os.remove(mkv_file)
                    print("MKV file deleted")
                except Exception as e:
                    print(f"Error deleting file: {e}")
                    self._show_error(f"Failed to delete MKV: {e}")
            else:
                print("MKV file deletion cancelled by user")
    
    def _get_mount_point(self, path):
        """Get the mount point for a given path, resolving symlinks."""
        # Resolve all symbolic links first
        path = os.path.realpath(path)
        path = os.path.abspath(path)
        
        while not os.path.ismount(path):
            parent = os.path.dirname(path)
            if parent == path:
                # Reached root
                break
            path = parent
        return path
    
    def _on_window_focus(self, window, event):
        """Check for new/changed subtitles when window gains focus."""
        if not self.current_file or not os.path.exists(self.current_file):
            return
        
        # Get current external subtitles
        _, external_subs = self.media_handler.analyze_file(self.current_file)
        current_subtitle_list = [sub['filename'] for sub in external_subs if 'filename' in sub]
        
        # Check if subtitle list has changed
        if set(current_subtitle_list) != set(self.last_subtitle_list):
            print("Subtitle files changed, reloading...")
            self.load_file(self.current_file)
    
    def _on_subtitle_selection_changed(self, selection):
        """Handle subtitle selection change - enable translate button for non-French subtitles."""
        model, treeiter = selection.get_selected()
        
        if treeiter is None:
            self.translate_button.set_sensitive(False)
            return
        
        # Get language of selected subtitle
        language = model[treeiter][0]
        
        # Enable translate button only if subtitle is not French
        is_french = language.lower() in ['fr', 'french', 'fra', 'fre']
        self.translate_button.set_sensitive(not is_french)
    
    def _on_translate_button_clicked(self, button):
        """Handle translate button click - extract and translate selected subtitle."""
        if not self.current_file:
            return
        
        # Determine which subtitle is selected (embedded or external)
        embedded_selection = self.embedded_view.get_selection()
        external_selection = self.external_view.get_selection()
        
        embedded_model, embedded_iter = embedded_selection.get_selected()
        external_model, external_iter = external_selection.get_selected()
        
        temp_dir = None
        subtitle_path = None
        is_embedded = False
        
        try:
            # Check embedded subtitles first
            if embedded_iter is not None:
                is_embedded = True
                # Get the index of the selected subtitle
                path = embedded_model.get_path(embedded_iter)
                index = path.get_indices()[0]
                sub_info = self.embedded_subs[index]
                
                # Extract to temp directory
                temp_dir = tempfile.mkdtemp(prefix='subtitle_translate_')
                subtitle_path = extract_single_subtitle(
                    self.current_file,
                    sub_info['index'],
                    sub_info['language'],
                    temp_dir
                )
                
            # Check external subtitles
            elif external_iter is not None:
                path = external_model.get_path(external_iter)
                index = path.get_indices()[0]
                sub_info = self.external_subs[index]
                subtitle_path = sub_info['path']
            
            if not subtitle_path:
                self._show_error("No subtitle selected")
                return
            
            # Determine output filename
            video_dir = os.path.dirname(self.current_file)
            video_base = os.path.splitext(os.path.basename(self.current_file))[0]
            output_file = os.path.join(video_dir, f"{video_base}.fr.srt")
            
            # Check if output file already exists
            if os.path.exists(output_file):
                dialog = Gtk.MessageDialog(
                    transient_for=self,
                    flags=0,
                    message_type=Gtk.MessageType.QUESTION,
                    buttons=Gtk.ButtonsType.YES_NO,
                    text="Overwrite existing French subtitle?"
                )
                dialog.format_secondary_text(
                    f"The file {os.path.basename(output_file)} already exists. Overwrite it?"
                )
                response = dialog.run()
                dialog.destroy()
                
                if response != Gtk.ResponseType.YES:
                    return
            
            # Show translation dialog with live output
            dialog = TranslationDialog(self, subtitle_path, output_file)
            response = dialog.run()
            dialog.destroy()
            
            if response == Gtk.ResponseType.OK:
                # Reload file to show new subtitle
                self.load_file(self.current_file)
                self.status_label.set_markup("<i>Translation complete!</i>")
            
        except Exception as e:
            print(f"Error during translation: {e}")
            self._show_error(f"Translation failed: {e}")
        
        finally:
            # Clean up temp directory
            if temp_dir and os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                    print(f"Cleaned up temp directory: {temp_dir}")
                except Exception as e:
                    print(f"Warning: Failed to clean up temp directory: {e}")
    
    def _on_embedded_subtitle_activated(self, treeview, path, column):
        """Handle double-click or activation on embedded subtitle."""
        # Get the selected subtitle index
        model = treeview.get_model()
        iter = model.get_iter(path)
        row_index = path.get_indices()[0]
        
        if row_index < len(self.embedded_subs):
            sub = self.embedded_subs[row_index]
            self._view_embedded_subtitle(sub)
    
    def _on_external_subtitle_activated(self, treeview, path, column):
        """Handle double-click or activation on external subtitle."""
        # Get the selected subtitle index
        model = treeview.get_model()
        iter = model.get_iter(path)
        row_index = path.get_indices()[0]
        
        if row_index < len(self.external_subs):
            sub = self.external_subs[row_index]
            self._view_external_subtitle(sub)
    
    def _view_embedded_subtitle(self, subtitle):
        """Extract and view an embedded subtitle."""
        if not self.current_file:
            return
        
        try:
            # Create temp directory
            temp_dir = tempfile.mkdtemp()
            output_file = os.path.join(temp_dir, f"temp_subtitle_{subtitle['index']}.srt")
            
            # Extract subtitle using ffmpeg
            cmd = [
                'ffmpeg',
                '-i', self.current_file,
                '-map', f"0:{subtitle['index']}",
                '-c:s', 'srt',
                '-y',
                output_file
            ]
            
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            # Read and display content
            with open(output_file, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            
            # Get file size
            file_size = os.path.getsize(output_file)
            
            # Clean up temp file
            shutil.rmtree(temp_dir, ignore_errors=True)
            
            # Show dialog
            self._show_subtitle_viewer(f"{subtitle['language']} - {subtitle.get('title', '')} (Embedded)", content, file_size)
            
        except Exception as e:
            self._show_error(f"Failed to view subtitle: {e}")
    
    def _view_external_subtitle(self, subtitle):
        """View an external subtitle file."""
        try:
            with open(subtitle['path'], 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            
            # Get file size
            file_size = os.path.getsize(subtitle['path'])
            
            self._show_subtitle_viewer(f"{subtitle['language']} - {subtitle['filename']}", content, file_size)
            
        except Exception as e:
            self._show_error(f"Failed to read subtitle file: {e}")
    
    def _show_subtitle_viewer(self, title, content, file_size):
        """Show a dialog window with subtitle content."""
        dialog = Gtk.Dialog(title=title, parent=self, modal=True)
        dialog.set_default_size(700, 500)
        dialog.add_button("Close", Gtk.ResponseType.CLOSE)
        
        content_area = dialog.get_content_area()
        
        # Create scrolled window with text view
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_shadow_type(Gtk.ShadowType.IN)
        
        text_view = Gtk.TextView()
        text_view.set_editable(False)
        text_view.set_monospace(True)
        text_view.set_left_margin(10)
        text_view.set_right_margin(10)
        text_view.get_buffer().set_text(content)
        
        scrolled.add(text_view)
        content_area.pack_start(scrolled, True, True, 0)
        
        # Calculate statistics
        line_count = content.count('\n') + 1 if content else 0
        
        # Format file size
        if file_size < 1024:
            size_str = f"{file_size} B"
        elif file_size < 1024 * 1024:
            size_str = f"{file_size / 1024:.1f} KB"
        elif file_size < 1024 * 1024 * 1024:
            size_str = f"{file_size / (1024 * 1024):.1f} MB"
        else:
            size_str = f"{file_size / (1024 * 1024 * 1024):.1f} GB"
        
        # Create info label
        info_label = Gtk.Label()
        info_label.set_markup(f"<small>Size: {size_str}  |  Lines: {line_count:,}</small>")
        info_label.set_halign(Gtk.Align.START)
        info_label.set_margin_start(10)
        info_label.set_margin_end(10)
        info_label.set_margin_top(5)
        info_label.set_margin_bottom(5)
        
        content_area.pack_start(info_label, False, False, 0)
        
        dialog.show_all()
        dialog.run()
        dialog.destroy()
    
    def _show_error(self, message):
        """Show error dialog."""
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text="Error"
        )
        dialog.format_secondary_text(message)
        dialog.run()
        dialog.destroy()


class TranslationDialog(Gtk.Dialog):
    """Dialog that shows live output from subtitle translation."""
    
    def __init__(self, parent, input_file, output_file):
        super().__init__(title="Translating Subtitle to French", transient_for=parent, flags=0)
        self.add_buttons(Gtk.STOCK_CLOSE, Gtk.ResponseType.OK)
        self.set_default_size(700, 500)
        self.set_border_width(10)
        
        self.input_file = input_file
        self.output_file = output_file
        self.process = None
        self.translation_successful = False
        
        # Make dialog non-modal but disable parent interaction
        self.set_modal(True)
        
        # Build UI
        box = self.get_content_area()
        box.set_spacing(10)
        
        # Info label
        info_label = Gtk.Label()
        info_label.set_markup(
            f"<b>Translating:</b> {os.path.basename(input_file)}\n"
            f"<b>Output:</b> {os.path.basename(output_file)}"
        )
        info_label.set_halign(Gtk.Align.START)
        box.pack_start(info_label, False, False, 0)
        
        # Scrolled window with text view for output
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_shadow_type(Gtk.ShadowType.IN)
        scrolled.set_vexpand(True)
        
        self.text_view = Gtk.TextView()
        self.text_view.set_editable(False)
        self.text_view.set_cursor_visible(False)
        self.text_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.text_view.set_monospace(True)
        
        self.text_buffer = self.text_view.get_buffer()
        scrolled.add(self.text_view)
        box.pack_start(scrolled, True, True, 0)
        
        # Status label
        self.status_label = Gtk.Label()
        self.status_label.set_markup("<i>Starting translation...</i>")
        self.status_label.set_halign(Gtk.Align.START)
        box.pack_start(self.status_label, False, False, 0)
        
        # Disable close button until done
        self.set_response_sensitive(Gtk.ResponseType.OK, False)
        
        self.show_all()
        
        # Start translation in background thread
        thread = threading.Thread(target=self._run_translation, daemon=True)
        thread.start()
    
    def _run_translation(self):
        """Run the translation subprocess in background thread."""
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            translate_script = os.path.join(script_dir, "srt_translate.py")
            
            # Command to run translation
            cmd = [
                'python3',
                '-u',  # Unbuffered output for real-time progress
                translate_script,
                TARGET_LANGUAGE,
                self.input_file,
                '-o', self.output_file  # Specify exact output location
            ]
            
            self._append_output(f"Running: {' '.join(cmd)}\n\n")
            
            # Run process and capture output line by line
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # Read output line by line
            for line in self.process.stdout:
                GLib.idle_add(self._append_output, line)
            
            # Wait for process to complete
            return_code = self.process.wait()
            
            if return_code == 0:
                # Check if output file was created
                if os.path.exists(self.output_file):
                    GLib.idle_add(self._translation_complete, True, "Translation completed successfully!")
                else:
                    GLib.idle_add(self._translation_complete, False, f"Translation failed: output file not created")
            else:
                GLib.idle_add(self._translation_complete, False, f"Translation failed with exit code {return_code}")
        
        except Exception as e:
            error_msg = f"Error during translation: {e}"
            print(error_msg)
            GLib.idle_add(self._append_output, f"\n\nERROR: {error_msg}\n")
            GLib.idle_add(self._translation_complete, False, error_msg)
    
    def _append_output(self, text):
        """Append text to the output view (must be called from main thread)."""
        end_iter = self.text_buffer.get_end_iter()
        self.text_buffer.insert(end_iter, text)
        
        # Auto-scroll to bottom
        mark = self.text_buffer.get_insert()
        self.text_view.scroll_to_mark(mark, 0.0, True, 0.0, 1.0)
        
        return False  # Don't repeat (for GLib.idle_add)
    
    def _translation_complete(self, success, message):
        """Called when translation is complete (must be called from main thread)."""
        self.translation_successful = success
        
        if success:
            self.status_label.set_markup(f"<b><span color='green'>✓ {message}</span></b>")
        else:
            self.status_label.set_markup(f"<b><span color='red'>✗ {message}</span></b>")
        
        # Enable close button
        self.set_response_sensitive(Gtk.ResponseType.OK, True)
        
        return False  # Don't repeat (for GLib.idle_add)
