Discord Music Bot
A feature-rich Discord music bot with playlist support, user favorites, and an experience system. This bot allows users to play music from YouTube, manage playlists, save favorite songs, and gain experience points for using the bot.
Features

Play music from YouTube links or search queries
Queue system for multiple songs
Playlist support
User favorites system
Experience points and leveling system
Admin commands for managing the bot
Easy setup and configuration

Prerequisites

Python 3.8 or higher
pip (Python package manager)
FFmpeg

Installation

Clone this repository:
Copygit clone https://github.com/anwark581/discord-music.git
cd discord-music-bot

Run the bot:
Copypython main.py
The script will automatically create a config.py file and install the required packages.
Edit the config.py file and add your Discord bot token:
pythonCopyBOT_TOKEN = 'your_bot_token_here'

Run the bot again:
Copypython main.py


Usage
Here are some of the available commands:

/ak <url>: Play a song or add it to the queue
/ak2 <title>: Search for a song on YouTube and play it
/join: Make the bot join your voice channel
/mysong: View and play your favorite songs
/dashboard: View your music dashboard with stats and top songs

For a full list of commands, use the /help command in Discord.
Contributing
Contributions are welcome! Please feel free to submit a Pull Request.
License
This project is licensed under the MIT License - see the LICENSE file for details.
Acknowledgments

Thanks to the Discord.py and yt-dlp libraries for making this bot possible.
Special thanks to all contributors and users of this bot.

Support
If you encounter any issues or have questions, please open an issue on GitHub or contact the maintainer.
Enjoy your music bot!
