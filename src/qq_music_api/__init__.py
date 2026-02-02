"""QQ Music MCP Server"""

from .client import QQMusicClient
from .models import Album, Lyric, MV, Playlist, SearchResult, Singer, Song, SongUrl
from .server import mcp, run_server

__version__ = "0.1.0"

__all__ = [
    "QQMusicClient",
    "Album",
    "Lyric",
    "MV",
    "Playlist",
    "SearchResult",
    "Singer",
    "Song",
    "SongUrl",
    "mcp",
    "run_server",
]
