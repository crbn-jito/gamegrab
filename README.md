# gamegrab

A command-line downloader and catalog browser for legally-obtained game files and public-domain archives.

Important: This tool is intended only for downloading files you have the legal right to download. Do not use it to download copyrighted material without permission.

Features:
- Interactive catalog search and selection
- Resumable, concurrent downloads with progress bars
- Retry/backoff, configurable concurrency and user-agent
- Optional SHA256 checksum validation
- Configurable download directory

Install
1. Python 3.10+
2. Create a venv and install:
   python -m venv .venv
   source .venv/bin/activate
   pip install .

Usage
- Initialize a catalog:
  gamegrab catalog init --catalog catalog.json

- Add an entry:
  gamegrab catalog add --catalog catalog.json --title "My Game" --url "https://example.com/file.wbfs" --sha256 "..." 

- Interactive search & download:
  gamegrab fetch --catalog catalog.json

- Direct download by ID:
  gamegrab fetch --catalog catalog.json --id 1

Configuration
- Default config is at ~/.config/gamegrab/config.toml
- You can override concurrency, download directory, user_agent, retries.

Legal and ethical notice
This project contains no site-specific scraping. Do not use it to download copyrighted ROMs or other material you do not have the right to download. Check the target site's Terms of Service and robots.txt and obtain permission if needed.
