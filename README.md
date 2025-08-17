# SpotDL GUI Downloader

A simple PyQt6-based GUI for downloading songs from Spotify using [spotdl](https://github.com/spotDL/spotify-downloader).

## Features

- Select a text file containing Spotify URLs
- Choose an output folder for downloads
- View individual song download progress
- Pause, resume, and stop downloads
- Overall progress bar

## Requirements

- Python 3.8+
- [spotdl](https://github.com/spotDL/spotify-downloader) installed (`pip install spotdl`)
- PyQt6 (`pip install PyQt6`)

## Usage

1. Run the application:
    ```sh
    python index.py
    ```
2. Select a `.txt` file containing Spotify track/album/playlist URLs (one per line).
3. Choose an output folder.
4. Click **Start** to begin downloading.
5. Use **Pause**, **Resume**, and **Stop** as needed.

## Example URL List

```
https://open.spotify.com/track/xxxxxxxxxxxxxx
https://open.spotify.com/track/yyyyyyyyyyyyyy
```

##