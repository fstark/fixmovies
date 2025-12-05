# Problem Statement

My Samsung TV often has issues playing movies with subtitles from my dlna server. Not all configurations are supported.
When something goes wrong, it is hard to debug, and the server is in the basement, so it takes a lot of time.
The goal is to create a tool that makes a media file viewable on the Samsung TV.

# What a proper media file looks like

It seems that .mkv files have more issues, I suspect due to the presence of embedded subtitles.

Subtitles with 3 letters language codes are not recognized.

# Spec

The software runs on Linux.

The software show a window. The user can drag and drop a media file (mkv or mp4) on that window.

The software will scan the directory for associated subtitles (with the same name, and a .srt or .lang.srt extension).

The software will present:

## The media file. When clicked, it will launch VLC.

The list of subtitles present in the media file with their language and their sizes.

The list of subtitles present in the directory, with their language and their sizes.

Only 'srt' files will be recognised.

The languages for srt files will be deduced from the file content. Only English and French are supported. (a simple method could be to look for some specific letters or pair of letter frequency, but there are other options). 

There is a "cleanup" button.

## If the file is a 'mkv' a preliminary step will be perfomed:

### extract the subtitles from the mkv file with proper names and extensions. If subtitles already exist, the ones extracted will have a -1, -2 added.

### convert the file to mp4 (using ffmpeg, for instance)

It will the reload the user interface with the mp4 file.

The mkv file will be deleted:
 if a .Trash folder exists on the file's volume the file will be moved there (eiter via a rename or by using some command-line tool).
 if not, a confirm dialog will popup and file will be rm'ed if confirmed

## The the process will continue:

It will rename existing subtitles to follow the .lang.srt rule, with 'lang' being the 2 letter iso code.

### Result

After potential conversion and renaming, we will have an mp4 file and the best suitable subtitles availalble as .lang.srt, with -nn for multiple subtitles.

Identical subtitles (same content) will be folded into one (ie: one copy left, all others removed)

###

Additional UI: a button (check box) that will allow the user to specify that he wants to convert+rename to be executed automatically when a file is dropped.
