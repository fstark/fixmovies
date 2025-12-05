"""
UI Components for Samsung TV Media File Converter
"""
import os
import subprocess
import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk

from media_handler import MediaHandler
from converter import convert_mkv_to_mp4
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
        self.embedded_store = Gtk.ListStore(str, str)  # Language, Size
        self.embedded_view = Gtk.TreeView(model=self.embedded_store)
        
        lang_renderer = Gtk.CellRendererText()
        lang_column = Gtk.TreeViewColumn("Language", lang_renderer, text=0)
        self.embedded_view.append_column(lang_column)
        
        size_renderer = Gtk.CellRendererText()
        size_column = Gtk.TreeViewColumn("Size", size_renderer, text=1)
        self.embedded_view.append_column(size_column)
        
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
        self.external_store = Gtk.ListStore(str, str)  # Language, Size
        self.external_view = Gtk.TreeView(model=self.external_store)
        
        lang_renderer2 = Gtk.CellRendererText()
        lang_column2 = Gtk.TreeViewColumn("Language", lang_renderer2, text=0)
        self.external_view.append_column(lang_column2)
        
        size_renderer2 = Gtk.CellRendererText()
        size_column2 = Gtk.TreeViewColumn("Size", size_renderer2, text=1)
        self.external_view.append_column(size_column2)
        
        external_scroll = Gtk.ScrolledWindow()
        external_scroll.set_size_request(-1, 120)
        external_scroll.set_shadow_type(Gtk.ShadowType.IN)
        external_scroll.add(self.external_view)
        main_box.pack_start(external_scroll, True, True, 5)
        
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
        
        # Store current subtitle list for comparison
        self.last_subtitle_list = [sub['filename'] for sub in external_subs if 'filename' in sub]
        
        # Update embedded subtitles list
        self.embedded_store.clear()
        for sub in embedded_subs:
            self.embedded_store.append([sub['language'], sub['size']])
        
        # Update external subtitles list
        self.external_store.clear()
        for sub in external_subs:
            self.external_store.append([sub['language'], sub['size']])
        
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
