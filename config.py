# config.py

# Discord Bot Token
BOT_TOKEN = ''

# Command Prefix
COMMAND_PREFIX = '/'

# Admin IDs
ADMIN_IDS = [818226562045837313, 764413811201146890]

# Test Guild ID
TEST_GUILD_ID = 743709112839438416

# YouTube Downloader Options
YTDL_FORMAT_OPTIONS = {
    'format': 'bestaudio/best',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'opus',
    }],
    'extractaudio': True,
    'audioformat': 'opus',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': False,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'
}

# FFmpeg Options
FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn -af "volume=-5dB"'
}

# Cache Duration (in seconds)
CACHE_DURATION = 3600  # 1 hour