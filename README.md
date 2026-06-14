# Music Transfer
 
A Python script that transfers all your Liked Songs from Spotify to a new playlist on YouTube Music, with a custom name and description of your choice.
 
## Features
 
- Fetches your Liked Songs from Spotify
- Creates a new playlist on YouTube Music with a name and description you specify
- Adds the transferred songs to that playlist
## Prerequisites
 
- Python 3.x
- A Spotify account and API access (for reading your Liked Songs)
- A YouTube Music account
## Setup
 
YouTube Music setup requires some manual steps on your end before running the script.
 
1. Clone the repository:
```bash
   git clone https://github.com/shreyasjeetsingh/Music_Transfer.git
   cd Music_Transfer
```
 
2. Install any required dependencies (see script for details).
3. Follow the in-program instructions to complete the YouTube Music authentication setup. This step is a bit tedious and must be done manually before the transfer can run.
## Usage
 
```bash
python is_this_it.py
```
 
Follow the prompts to authenticate with Spotify and YouTube Music, then specify a name and description for the new playlist. The script will fetch your Liked Songs and recreate them as a playlist on YouTube Music.
 
## Notes
 
- This is a one-way transfer: Spotify Liked Songs to a new YouTube Music playlist.
- Make sure the YouTube Music setup instructions in the script are completed first, or the transfer will fail.
