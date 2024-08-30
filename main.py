import os
import sys
import subprocess

def install_requirements():
    print("Installing required packages...")
    try:
        # Upgrade pip
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
        
        # Install discord.py
        subprocess.check_call([sys.executable, "-m", "pip", "install", "discord.py"])
        
        # Try to install aiohttp separately if needed
        try:
            import aiohttp
        except ImportError:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "aiohttp", "--no-build-isolation"])
        
        # Install other requirements
        subprocess.check_call([sys.executable, "-m", "pip", "install", "yt-dlp"])
        
        print("Requirements installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to install requirements: {e}")
        print("Please try to install the requirements manually:")
        print("1. Run: pip install --upgrade pip")
        print("2. Run: pip install discord.py")
        print("3. Run: pip install aiohttp --no-build-isolation")
        print("4. Run: pip install yt-dlp")
        sys.exit(1)

# Check if discord is installed, if not, install requirements
try:
    import discord
except ImportError:
    print("Discord module not found. Installing requirements...")
    install_requirements()
    import discord

import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import sqlite3
import yt_dlp
import yt_dlp as youtube_dl
from collections import Counter
from config import BOT_TOKEN, YTDL_FORMAT_OPTIONS, FFMPEG_OPTIONS
from discord import PCMVolumeTransformer
from concurrent.futures import ThreadPoolExecutor
from typing import Optional
import time
import logging
import hashlib
from discord import Activity, ActivityType
from yt_dlp import YoutubeDL
import traceback

# Check if config.py exists, if not, create it
if not os.path.exists('config.py'):
    print("Config file not found. Creating a new one...")
    with open('config.py', 'w') as f:
        f.write('''
# Discord Bot Token
BOT_TOKEN = ''

# Command Prefix
COMMAND_PREFIX = '/'

# Admin IDs
ADMIN_IDS = []

# Test Guild ID
TEST_GUILD_ID = None

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
''')
    print("Config file created. Please edit config.py and add your bot token.")

# Import configuration
from config import BOT_TOKEN, COMMAND_PREFIX, ADMIN_IDS, TEST_GUILD_ID, YTDL_FORMAT_OPTIONS, FFMPEG_OPTIONS, CACHE_DURATION

# Check if BOT_TOKEN is set
if not BOT_TOKEN:
    print("Please set your bot token in config.py")
    sys.exit(1)

# Install requirements
def install_requirements():
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("Requirements installed successfully.")
    except subprocess.CalledProcessError:
        print("Failed to install requirements. Please install them manually.")
        sys.exit(1)

# Check if requirements are already installed
try:
    import discord
except ImportError:
    print("Discord library not found. Installing requirements...")
    install_requirements()

TEST_GUILD_ID = 

ADMIN_IDS = [818226562045837313, 764413811201146890]

intents = discord.Intents.default()
intents.message_content = True

# Simple cache to store video information
video_cache = {}
CACHE_DURATION = 3600  # 1 hour

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('music_bot')



class MusicBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix='/', intents=intents)
        self.currently_playing = None
        self.queue = asyncio.Queue()
        self.db = sqlite3.connect('music_bot.db')
        self.create_tables()
        self.migrate_database()
        self.last_voice_channel = None

    async def setup_hook(self):
        try:
            synced = await self.tree.sync()
            print(f"Synced {len(synced)} command(s) globally")
        except Exception as e:
            print(f"Failed to sync commands: {e}")

    def create_tables(self):
        cursor = self.db.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS favorites (
            user_id INTEGER,
            song_title TEXT,
            song_url TEXT,
            song_id TEXT,
            PRIMARY KEY (user_id, song_url)
        )
        ''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_stats (
            user_id INTEGER PRIMARY KEY,
            songs_played INTEGER DEFAULT 0,
            favorites_added INTEGER DEFAULT 0,
            experience INTEGER DEFAULT 0
        )
        ''')
        self.db.commit()

    def migrate_database(self):
        cursor = self.db.cursor()
        
        # Check if the song_id column exists in favorites
        cursor.execute("PRAGMA table_info(favorites)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'song_id' not in columns:
            print("Migrating database: Adding 'song_id' column to favorites table")
            cursor.execute('ALTER TABLE favorites ADD COLUMN song_id TEXT')
            
            # Generate song_id for existing entries
            cursor.execute('SELECT user_id, song_title, song_url FROM favorites')
            existing_favorites = cursor.fetchall()
            for user_id, song_title, song_url in existing_favorites:
                song_id = hashlib.md5((song_title + song_url).encode()).hexdigest()[:20]
                cursor.execute('UPDATE favorites SET song_id = ? WHERE user_id = ? AND song_url = ?',
                               (song_id, user_id, song_url))
            
            self.db.commit()
            print("Favorites table migration complete")

        # Check if the experience column exists in user_stats
        cursor.execute("PRAGMA table_info(user_stats)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'experience' not in columns:
            print("Migrating database: Adding 'experience' column to user_stats table")
            cursor.execute('ALTER TABLE user_stats ADD COLUMN experience INTEGER DEFAULT 0')
            
            # Initialize experience based on songs_played
            cursor.execute('UPDATE user_stats SET experience = songs_played * 10')
            
            self.db.commit()
            print("User stats table migration complete")

    async def close(self):
        await super().close()
        self.db.close()

bot = MusicBot()



def calculate_level(exp):
    return exp // 99999  # Simplified level calculation

def get_level_emoji(level):
    emojis = ["🎵", "🎶", "🎸", "🎹", "🎼"]
    return emojis[min(level, len(emojis) - 1)]

async def update_user_exp(user_id, exp_gain):
    cursor = bot.db.cursor()
    cursor.execute('''
    INSERT INTO user_stats (user_id, experience, songs_played) 
    VALUES (?, ?, 1)
    ON CONFLICT(user_id) DO UPDATE SET 
    experience = experience + ?,
    songs_played = songs_played + 1
    ''', (user_id, exp_gain, exp_gain))
    bot.db.commit()

class MusicControls(discord.ui.View):
    def __init__(self, song_title, song_url, requester_id):
        super().__init__(timeout=None)
        self.song_title = song_title
        self.song_url = song_url
        self.requester_id = requester_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.data["custom_id"] == "add_to_favorites":
            return True
        
        # Check if the user has the DJ role
        dj_role = discord.utils.get(interaction.guild.roles, name="DJ")
        is_dj = dj_role in interaction.user.roles if dj_role else False
        
        return (
            interaction.user.id == self.requester_id 
            or interaction.user.id in ADMIN_IDS
            or (is_dj and interaction.data["custom_id"] in ["skip", "stop"])
        )

    @discord.ui.button(label="Pause/Resume", style=discord.ButtonStyle.primary)
    async def pause_resume(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.guild.voice_client:
            return await interaction.response.send_message("Not connected to a voice channel.", ephemeral=True)
        
        if interaction.guild.voice_client.is_paused():
            interaction.guild.voice_client.resume()
            await interaction.response.send_message("Resumed the song.", ephemeral=True)
        elif interaction.guild.voice_client.is_playing():
            interaction.guild.voice_client.pause()
            await interaction.response.send_message("Paused the song.", ephemeral=True)
        else:
            await interaction.response.send_message("Nothing is playing right now.", ephemeral=True)

    @discord.ui.button(label="Skip", style=discord.ButtonStyle.secondary, custom_id="skip")
    async def skip(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.guild.voice_client or not interaction.guild.voice_client.is_playing():
            return await interaction.response.send_message("Nothing is playing right now.", ephemeral=True)
        
        interaction.guild.voice_client.stop()
        await interaction.response.send_message("Skipped the song.", ephemeral=True)

    @discord.ui.button(label="Stop", style=discord.ButtonStyle.danger, custom_id="stop")
    async def stop(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.guild.voice_client:
            return await interaction.response.send_message("Not connected to a voice channel.", ephemeral=True)
        
        await interaction.guild.voice_client.disconnect()
        bot.currently_playing = None
        bot.queue = asyncio.Queue()  # Clear the queue
        await interaction.response.send_message("Stopped the music and disconnected.", ephemeral=True)

    @discord.ui.button(label="Volume -", style=discord.ButtonStyle.secondary)
    async def volume_down(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.guild.voice_client or not interaction.guild.voice_client.source:
            return await interaction.response.send_message("Not playing any audio right now.", ephemeral=True)
        
        current_volume = interaction.guild.voice_client.source.volume
        new_volume = max(0.0, current_volume - 0.05)  # Decrease by 5%, but not below 0
        interaction.guild.voice_client.source.volume = new_volume
        await interaction.response.send_message(f"Volume decreased to {new_volume:.0%}", ephemeral=True)

    @discord.ui.button(label="Volume +", style=discord.ButtonStyle.secondary)
    async def volume_up(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.guild.voice_client or not interaction.guild.voice_client.source:
            return await interaction.response.send_message("Not playing any audio right now.", ephemeral=True)
        
        current_volume = interaction.guild.voice_client.source.volume
        new_volume = min(2.0, current_volume + 0.05)  # Increase by 5%, but not above 200%
        interaction.guild.voice_client.source.volume = new_volume
        await interaction.response.send_message(f"Volume increased to {new_volume:.0%}", ephemeral=True)

    @discord.ui.button(label="Add to /mysong", style=discord.ButtonStyle.success, custom_id="add_to_favorites")
    async def add_to_favorites(self, interaction: discord.Interaction, button: discord.ui.Button):
        cursor = bot.db.cursor()
        song_id = hashlib.md5((self.song_title + self.song_url).encode()).hexdigest()[:20]
        cursor.execute('INSERT OR REPLACE INTO favorites (user_id, song_title, song_url, song_id) VALUES (?, ?, ?, ?)',
                       (interaction.user.id, self.song_title, self.song_url, song_id))
        cursor.execute('''
        INSERT INTO user_stats (user_id, favorites_added) VALUES (?, 1)
        ON CONFLICT(user_id) DO UPDATE SET favorites_added = favorites_added + 1
        ''', (interaction.user.id,))
        bot.db.commit()
        await interaction.response.send_message(f"Added '{self.song_title}' to your favorites!", ephemeral=True)

async def play_song(interaction: discord.Interaction, url: str):
    ydl_opts = YTDL_FORMAT_OPTIONS.copy()
    try:
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info = await bot.loop.run_in_executor(None, lambda: ydl.extract_info(url, download=False))
            if 'entries' in info:  # It's a playlist
                for entry in info['entries']:
                    if entry:
                        await bot.queue.put((entry['url'], entry.get('title', 'Unknown title')))
                await interaction.followup.send(f"Added {len(info['entries'])} songs from the playlist to the queue.")
            else:  # It's a single video
                await bot.queue.put((info['url'], info.get('title', 'Unknown title')))
                await interaction.followup.send(f"Added {info.get('title', 'Unknown title')} to the queue.")

        if not interaction.guild.voice_client.is_playing():
            await play_next(interaction)
    except Exception as e:
        print(f"An error occurred while processing the song/playlist: {e}")
        await interaction.followup.send(f"An error occurred while processing the song/playlist: {e}")

@bot.tree.command(name="ak", description="Play a song or playlist from YouTube")
async def play(interaction: discord.Interaction, url: str):
    if not interaction.guild.voice_client:
        if interaction.user.voice:
            await interaction.user.voice.channel.connect()
        else:
            return await interaction.response.send_message("You need to be in a voice channel to use this command!")

    await interaction.response.defer(thinking=True)
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'extract_flat': 'in_playlist',
        'ignoreerrors': True,
        'nocheckcertificate': True,
        'no_warnings': True,
        'quiet': True,
    }

    try:
        with ThreadPoolExecutor() as executor:
            loop = asyncio.get_event_loop()
            info = await loop.run_in_executor(executor, lambda: yt_dlp.YoutubeDL(ydl_opts).extract_info(url, download=False))

        if 'entries' in info:  # It's a playlist
            await interaction.followup.send(f"Adding playlist: {info.get('title', 'Unknown Playlist')}")
            for entry in info['entries']:
                if entry:
                    await bot.queue.put((entry['url'], entry.get('title', 'Unknown title')))
        else:  # It's a single video
            await bot.queue.put((info['webpage_url'], info.get('title', 'Unknown title')))
            await interaction.followup.send(f"Added {info.get('title', 'Unknown title')} to the queue.")

        if not interaction.guild.voice_client.is_playing():
            await play_next(interaction)

    except Exception as e:
        print(f"An error occurred while processing the song/playlist: {e}")
        await interaction.followup.send(f"An error occurred while processing the song/playlist. Please try again or use a different link.")

def is_bot_connected(guild):
    return guild.voice_client is not None and guild.voice_client.is_connected()

async def clear_queue_if_disconnected(guild):
    if not is_bot_connected(guild):
        bot.queue = asyncio.Queue()  # Clear the queue
        bot.currently_playing = None
        await bot.change_presence(activity=None)
        return True
    return False

async def play_next(ctx):
    channel = ctx.channel if hasattr(ctx, 'channel') else ctx
    guild = channel.guild

    if await clear_queue_if_disconnected(guild):
        await safe_send(channel, "I was disconnected from the voice channel. The queue has been cleared.")
        return

    if bot.queue.empty():
        bot.currently_playing = None
        await safe_send(channel, "The queue is empty. Use /play to add more songs!")
        await bot.change_presence(activity=None)  
        return

    if not is_bot_connected(guild):
        if bot.last_voice_channel and bot.last_voice_channel.guild == guild:
            try:
                await bot.last_voice_channel.connect()
                await safe_send(channel, f"Reconnected to {bot.last_voice_channel.name}")
            except Exception as e:
                await safe_send(channel, f"Failed to reconnect to the voice channel: {e}")
                return
        else:
            await safe_send(channel, "I'm not connected to a voice channel. Use the /join command to connect me.")
            return

    current_url, current_title = await bot.queue.get()

    try:
        if not is_bot_connected(guild):
            await safe_send(channel, "I'm not connected to a voice channel. Use the /join command to connect me.")
            return

        # Check if audio is already playing and stop it
        if guild.voice_client and guild.voice_client.is_playing():
            guild.voice_client.stop()

        # Check cache first
        if current_url in video_cache and time.time() - video_cache[current_url]['timestamp'] < CACHE_DURATION:
            stream_url = video_cache[current_url]['stream_url']
        else:
            stream_url = await extract_stream_url(current_url)
            
            # Cache the stream URL
            video_cache[current_url] = {
                'stream_url': stream_url,
                'timestamp': time.time()
            }

        audio_source = discord.FFmpegPCMAudio(stream_url, **FFMPEG_OPTIONS)
        volume_source = discord.PCMVolumeTransformer(audio_source, volume=1.0)
        
        def after_playing(error):
            bot.loop.create_task(after_playing_callback(error, guild))

        if guild.voice_client:
            guild.voice_client.play(volume_source, after=after_playing)

            await bot.change_presence(activity=Activity(type=ActivityType.listening, name=current_title))
            
            # Create embedded message with GIF
            embed = discord.Embed(title="Now Playing", description=current_title, color=discord.Color.blue())
            embed.set_image(url="https://cdn.discordapp.com/attachments/1200073995836473469/1274694574152880138/AK-crop.gif?ex=66c32f55&is=66c1ddd5&hm=888c0dcceb541da19f3cdfb04aadf1009f97d9a78c85be704335b9485337c66b&")
            embed.add_field(name="Volume", value=f"{int(volume_source.volume * 100)}%", inline=True)
            
            # Check for next song in queue
            if not bot.queue.empty():
                next_url, next_title = bot.queue._queue[0]
                embed.add_field(name="Up Next", value=next_title, inline=True)
            
            # Create and send new MusicControls with embedded message
            controls = MusicControls(current_title, current_url, guild.me.id)  # Use bot's ID as requester
            bot.currently_playing = await safe_send(channel, embed=embed, view=controls)
        else:
            raise Exception("Voice client is not connected.")

    except Exception as e:
        print(f"An error occurred while playing the song: {e}")
        print(f"Error details: {traceback.format_exc()}")
        await safe_send(channel, f"An error occurred while playing the song. Skipping to next.")
        if not bot.queue.empty():
            await play_next(channel)
        else:
            await safe_send(channel, "The queue is now empty.")

@bot.event
async def on_voice_state_update(member, before, after):
    if member == bot.user and after.channel is None:
        # Bot was disconnected from a voice channel
        bot.last_voice_channel = before.channel
        guild = before.channel.guild
        await clear_queue_if_disconnected(guild)
        
        # Find a suitable text channel to send the disconnection message
        text_channel = None
        if bot.currently_playing and hasattr(bot.currently_playing, 'channel'):
            text_channel = bot.get_channel(bot.currently_playing.channel.id)
        if text_channel is None and guild.text_channels:
            text_channel = guild.text_channels[0]  # Use the first text channel in the guild
        
        if text_channel:
            await safe_send(text_channel, "I was disconnected from the voice channel. The queue has been cleared. Use /join to reconnect me.")
        else:
            print("No suitable text channel found to send disconnection message")

async def safe_send(channel, content=None, embed=None, view=None):
    try:
        return await channel.send(content=content, embed=embed, view=view)
    except discord.errors.HTTPException as e:
        print(f"Failed to send message to channel: {e}")
        return None


async def extract_stream_url(current_url):
    max_retries = 3
    for attempt in range(max_retries):
        try:
            ydl_opts = {
                'format': 'bestaudio/best',
                'nocheckcertificate': True,
                'no_warnings': True,
                'quiet': True,
            }

            with ThreadPoolExecutor() as executor:
                loop = asyncio.get_event_loop()
                info = await loop.run_in_executor(executor, lambda: yt_dlp.YoutubeDL(ydl_opts).extract_info(current_url, download=False))

            return info['url']
        except Exception as e:
            print(f"Error extracting stream URL (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt == max_retries - 1:
                raise

@bot.tree.command(name="ak2", description="Search and play a song by title")
async def search(interaction: discord.Interaction, title: str):
    await interaction.response.defer(thinking=True)
    
    if not interaction.guild.voice_client:
        if interaction.user.voice:
            await interaction.user.voice.channel.connect()
        else:
            return await interaction.followup.send("You need to be in a voice channel to use this command!")

    ydl_opts = {
        'format': 'bestaudio/best',
        'default_search': 'ytsearch',
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        'ignoreerrors': True,
        'nocheckcertificate': True,
        'retries': 5,
    }

    async def extract_info(title):
        loop = asyncio.get_event_loop()
        with YoutubeDL(ydl_opts) as ydl:
            return await loop.run_in_executor(None, lambda: ydl.extract_info(f"ytsearch:{title}", download=False))

    try:
        for attempt in range(3):  # Try up to 3 times
            try:
                info = await extract_info(title)
                if 'entries' in info and info['entries']:
                    video = info['entries'][0]
                    await bot.queue.put((video['webpage_url'], video['title']))
                    await interaction.followup.send(f"Added {video['title']} to the queue.")
                    if not interaction.guild.voice_client.is_playing():
                        await play_next(interaction)
                    return
                else:
                    await interaction.followup.send("No results found for that title. Please try again with a different search term.")
                    return
            except Exception as e:
                if attempt < 2:  # If it's not the last attempt
                    await asyncio.sleep(1)  # Wait for a second before retrying
                else:
                    raise  # If it's the last attempt, raise the exception to be caught by the outer try-except

    except Exception as e:
        print(f"An error occurred while searching for the song: {e}")
        await interaction.followup.send("An error occurred while searching for the song. Please try again or use a direct URL.")



@bot.tree.command(name="join", description="Join the voice channel")
async def join(interaction: discord.Interaction):
    if not interaction.user.voice:
        return await interaction.response.send_message("You are not connected to a voice channel.")
    
    if interaction.guild.voice_client:
        await interaction.guild.voice_client.disconnect()
    
    await interaction.user.voice.channel.connect()
    bot.last_voice_channel = interaction.user.voice.channel
    await interaction.response.send_message(f"Joined {interaction.user.voice.channel.name}")

    if not bot.queue.empty():
        await play_next(interaction)

async def after_playing_callback(error, guild):
    if error:
        print(f"Error in playback: {error}")
    
    if await clear_queue_if_disconnected(guild):
        if bot.currently_playing and hasattr(bot.currently_playing, 'channel'):
            channel = bot.get_channel(bot.currently_playing.channel.id)
            await safe_send(channel, "I was disconnected from the voice channel. The queue has been cleared.")
        return

    if bot.currently_playing and hasattr(bot.currently_playing, 'channel'):
        channel = bot.get_channel(bot.currently_playing.channel.id)
        
        if bot.queue.empty():
            bot.currently_playing = None
            await safe_send(channel, "The queue is empty. Use /play to add more songs!")
            await bot.change_presence(activity=None)
        else:
            await play_next(channel)
    else:
        print("Warning: bot.currently_playing is None or doesn't have a channel attribute in after_playing_callback")
        if not bot.queue.empty():
            # Try to find a suitable channel to send the message
            if guild.text_channels:
                channel = guild.text_channels[0]  # Use the first text channel in the guild
                await play_next(channel)
            else:
                print("No suitable text channel found to continue playback")


@bot.tree.command(name="mysong", description="View and play your favorite songs")
async def mysong(interaction: discord.Interaction):
    cursor = bot.db.cursor()
    cursor.execute('SELECT song_title, song_url FROM favorites WHERE user_id = ?', (interaction.user.id,))
    favorites = cursor.fetchall()

    if not favorites:
        return await interaction.response.send_message("You don't have any favorite songs yet.", ephemeral=True)

    # Create a dictionary to map short IDs to URLs
    url_map = {str(i): url for i, (_, url) in enumerate(favorites)}
    
    options = [discord.SelectOption(label=title[:100], value=str(i)) for i, (title, _) in enumerate(favorites)]

    class FavoriteSelect(discord.ui.Select):
        def __init__(self):
            super().__init__(placeholder="Choose a song to play", options=options)

        async def callback(self, interaction: discord.Interaction):
            await interaction.response.defer()
            if not interaction.guild.voice_client:
                if interaction.user.voice:
                    await interaction.user.voice.channel.connect()
                else:
                    return await interaction.followup.send("You need to be in a voice channel to play music!")
            
            selected_id = self.values[0]
            selected_url = url_map[selected_id]
            selected_title = next(title for title, url in favorites if url == selected_url)
            
            await bot.queue.put((selected_url, selected_title))
            await interaction.followup.send(f"Added {selected_title} to the queue.")
            
            if not interaction.guild.voice_client.is_playing():
                await play_next(interaction)

    view = discord.ui.View()
    view.add_item(FavoriteSelect())
    await interaction.response.send_message("Here are your favorite songs:", view=view, ephemeral=True)

@bot.tree.command(name="dashboard", description="View your music dashboard")
async def dashboard(interaction: discord.Interaction):
    cursor = bot.db.cursor()
    cursor.execute('SELECT songs_played, favorites_added, experience FROM user_stats WHERE user_id = ?', (interaction.user.id,))
    stats = cursor.fetchone() or (0, 0, 0)
    songs_played, favorites_added, exp = stats
    
    level = calculate_level(exp)
    level_emoji = get_level_emoji(level)
    
    cursor.execute('SELECT COUNT(*) FROM favorites WHERE user_id = ?', (interaction.user.id,))
    total_favorites = cursor.fetchone()[0]
    
    # Get top 4 favorited songs
    cursor.execute('SELECT song_title, COUNT(*) as favorite_count FROM favorites GROUP BY song_title ORDER BY favorite_count DESC LIMIT 4')
    top_favorites = cursor.fetchall()
    
    # Get user ranking
    cursor.execute('SELECT user_id, experience FROM user_stats ORDER BY experience DESC')
    rankings = cursor.fetchall()
    user_rank = next((i for i, (uid, _) in enumerate(rankings, 1) if uid == interaction.user.id), "N/A")
    
    embed = discord.Embed(title=f"{interaction.user.name}'s Music Dashboard", color=discord.Color.blue())
    embed.add_field(name="Level", value=f"{level_emoji} {level}", inline=True)
    embed.add_field(name="Rank", value=f"#{user_rank}", inline=True)
    embed.add_field(name="Experience", value=f"{exp}/100", inline=True)
    embed.add_field(name="Songs Played", value=songs_played, inline=True)
    embed.add_field(name="Favorites Added", value=favorites_added, inline=True)
    embed.add_field(name="Total Favorites", value=total_favorites, inline=True)
    
    top_favorites_text = "\n".join([f"{i+1}. {title} ({count} ❤️)" for i, (title, count) in enumerate(top_favorites)])
    embed.add_field(name="Top 4 Favorited Songs", value=top_favorites_text or "No favorites yet", inline=False)
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="admin_favorites", description="Admin: Play any user's favorites")
@app_commands.checks.has_any_role(*ADMIN_IDS)
async def admin_favorites(interaction: discord.Interaction, user: discord.User):
    if interaction.user.id not in ADMIN_IDS:
        return await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
    
    cursor = bot.db.cursor()
    cursor.execute('SELECT song_title, song_url FROM favorites WHERE user_id = ?', (user.id,))
    favorites = cursor.fetchall()

    if not favorites:
        return await interaction.response.send_message(f"{user.name} doesn't have any favorite songs.", ephemeral=True)

    options = [discord.SelectOption(label=title[:100], value=url) for title, url in favorites]

    class AdminFavoriteSelect(discord.ui.Select):
        def __init__(self):
            super().__init__(placeholder=f"Choose a song from {user.name}'s favorites", options=options)

        async def callback(self, interaction: discord.Interaction):
            await interaction.response.defer()
            if not interaction.guild.voice_client:
                if interaction.user.voice:
                    await interaction.user.voice.channel.connect()
                else:
                    return await interaction.followup.send("You need to be in a voice channel to play music!")
            
            # Add all favorite songs to the queue
            for option in self.options:
                await bot.queue.put((option.value, option.label))
            
            await interaction.followup.send(f"Added all of {user.name}'s favorite songs to the queue.")
            
            if not interaction.guild.voice_client.is_playing():
                await play_next(interaction)

    view = discord.ui.View()
    view.add_item(AdminFavoriteSelect())
    await interaction.response.send_message(f"Here are {user.name}'s favorite songs:", view=view, ephemeral=True)


@bot.command()
@commands.is_owner()
async def sync(ctx):
    try:
        synced = await bot.tree.sync()
        await ctx.send(f"Synced {len(synced)} command(s)")
        print(f"Manually synced {len(synced)} command(s)")
    except Exception as e:
        await ctx.send(f"Failed to sync commands: {e}")
        print(f"Failed to manually sync commands: {e}")

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print("Registered commands:")
    for command in bot.tree.get_commands():
        print(f"- /{command.name}")
    print(f"\nInvite URL: https://discord.com/api/oauth2/authorize?client_id={bot.user.id}&permissions=8&scope=bot%20applications.commands")
    
    # Set initial status
    await bot.change_presence(activity=Activity(type=ActivityType.listening, name="nothing"))

bot.run(BOT_TOKEN)
    
    # Set initial status
    await bot.change_presence(activity=Activity(type=ActivityType.listening, name="nothing"))

if __name__ == "__main__":
    bot.run(BOT_TOKEN)
