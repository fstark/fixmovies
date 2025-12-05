#!/usr/bin/env python3
"""
Samsung TV Media File Converter
Main application entry point
"""
import sys
import shutil
import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from ui_components import MainWindow


def check_dependencies():
    """Check if required external dependencies are installed."""
    missing = []
    
    if not shutil.which('ffmpeg'):
        missing.append('ffmpeg')
    
    if not shutil.which('vlc'):
        missing.append('vlc')
    
    return missing


def show_dependency_error(missing_deps):
    """Show error dialog for missing dependencies."""
    dialog = Gtk.MessageDialog(
        transient_for=None,
        flags=0,
        message_type=Gtk.MessageType.ERROR,
        buttons=Gtk.ButtonsType.OK,
        text="Missing Dependencies"
    )
    
    deps_list = ', '.join(missing_deps)
    dialog.format_secondary_text(
        f"The following required dependencies are not installed: {deps_list}\n\n"
        f"Please install them:\n"
        f"sudo apt-get install {' '.join(missing_deps)}"
    )
    
    dialog.run()
    dialog.destroy()


def main():
    """Main application entry point."""
    print("Starting Samsung TV Media File Converter...")
    
    # Check dependencies
    missing = check_dependencies()
    if missing:
        print(f"ERROR: Missing dependencies: {missing}")
        show_dependency_error(missing)
        sys.exit(1)
    
    print("All dependencies found: ffmpeg, vlc")
    
    # Create and run the application
    app = MainWindow()
    app.connect("destroy", Gtk.main_quit)
    app.show_all()
    
    print("Application window created. Ready for file input.")
    Gtk.main()


if __name__ == '__main__':
    main()
