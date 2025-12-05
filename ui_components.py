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
        self.set_default_size(700, 500)
        self.set_border_width(10)
        
        self.current_file = None
        self.media_handler = MediaHandler()
        
        self._build_ui()
        self._setup_drag_and_drop()
    
    def _build_ui(self):
        """Build the user interface."""
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.add(main_box)
        
        # Drop zone
        self.drop_zone = Gtk.Label()
        self.drop_zone.set_markup("<big>Drop a video file here (MKV or MP4)</big>")
        self.drop_zone.set_size_request(-1, 100)
        drop_frame = Gtk.Frame()
        drop_frame.add(self.drop_zone)
        main_box.pack_start(drop_frame, False, False, 0)
        
        # Media file label (clickable)
        self.media_label = Gtk.Label()
        self.media_label.set_markup("<b>No file loaded</b>")
        self.media_label.set_selectable(True)
        event_box = Gtk.EventBox()
        event_box.add(self.media_label)
        event_box.connect("button-press-event", self._on_media_label_clicked)
        event_box.set_above_child(True)
        main_box.pack_start(event_box, False, False, 0)
        
        # Status label
        self.status_label = Gtk.Label()
        self.status_label.set_markup("<i>Ready</i>")
        main_box.pack_start(self.status_label, False, False, 0)
        
        # Embedded subtitles section
        embed_label = Gtk.Label()
        embed_label.set_markup("<b>Embedded Subtitles:</b>")
        embed_label.set_halign(Gtk.Align.START)
        main_box.pack_start(embed_label, False, False, 0)
        
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
        embed_scroll.set_size_request(-1, 100)
        embed_scroll.add(self.embedded_view)
        main_box.pack_start(embed_scroll, True, True, 0)
        
        # External subtitles section
        external_label = Gtk.Label()
        external_label.set_markup("<b>External Subtitles:</b>")
        external_label.set_halign(Gtk.Align.START)
        main_box.pack_start(external_label, False, False, 0)
        
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
        external_scroll.set_size_request(-1, 100)
        external_scroll.add(self.external_view)
        main_box.pack_start(external_scroll, True, True, 0)
        
        # Action button
        self.action_button = Gtk.Button(label="Load a file")
        self.action_button.set_sensitive(False)
        self.action_button.connect("clicked", self._on_action_button_clicked)
        main_box.pack_start(self.action_button, False, False, 0)
    
    def _setup_drag_and_drop(self):
        """Setup drag and drop functionality."""
        self.drop_zone.drag_dest_set(
            Gtk.DestDefaults.ALL,
            [],
            Gdk.DragAction.COPY
        )
        self.drop_zone.drag_dest_add_uri_targets()
        self.drop_zone.connect("drag-data-received", self._on_file_dropped)
    
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
            else:
                self._show_error("Invalid file type. Please drop an MKV or MP4 file.")
    
    def load_file(self, file_path):
        """Load and analyze a media file."""
        print(f"Loading file: {file_path}")
        self.current_file = file_path
        
        # Update media label
        filename = os.path.basename(file_path)
        self.media_label.set_markup(f"<b>File:</b> {filename}\n<i>(Click to open in VLC)</i>")
        
        # Analyze file
        embedded_subs, external_subs = self.media_handler.analyze_file(file_path)
        
        # Update embedded subtitles list
        self.embedded_store.clear()
        for sub in embedded_subs:
            self.embedded_store.append([sub['language'], sub['size']])
        
        # Update external subtitles list
        self.external_store.clear()
        for sub in external_subs:
            self.external_store.append([sub['language'], sub['size']])
        
        # Update action button
        if file_path.lower().endswith('.mkv'):
            self.action_button.set_label("Convert to MP4")
            self.action_button.set_sensitive(True)
        elif file_path.lower().endswith('.mp4'):
            self.action_button.set_label("Go (Finalize)")
            self.action_button.set_sensitive(True)
        
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
    
    def _on_action_button_clicked(self, button):
        """Handle action button click (Convert or Go)."""
        if not self.current_file:
            return
        
        # Disable button during processing
        self.action_button.set_sensitive(False)
        self.status_label.set_markup("<i>Processing...</i>")
        
        try:
            if self.current_file.lower().endswith('.mkv'):
                self._convert_mkv()
            elif self.current_file.lower().endswith('.mp4'):
                self._process_mp4()
        except Exception as e:
            print(f"Error during processing: {e}")
            self._show_error(f"Processing failed: {e}")
            self.action_button.set_sensitive(True)
            self.status_label.set_markup("<i>Error</i>")
    
    def _convert_mkv(self):
        """Convert MKV to MP4."""
        print("Starting MKV conversion...")
        
        try:
            output_file = convert_mkv_to_mp4(self.current_file)
            print(f"Conversion complete: {output_file}")
            self.status_label.set_markup("<i>Conversion complete!</i>")
            
            # Reload with the new MP4 file
            self.load_file(output_file)
        except Exception as e:
            raise
    
    def _process_mp4(self):
        """Process MP4 subtitles."""
        print("Starting MP4 subtitle processing...")
        
        try:
            process_mp4_subtitles(self.current_file)
            print("MP4 processing complete")
            self.status_label.set_markup("<i>Complete! Files ready for Samsung TV</i>")
            
            # Reload to show updated subtitles
            self.load_file(self.current_file)
        except Exception as e:
            raise
    
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
