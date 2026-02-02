"""QQ Music API"""

from .client import QQMusicClient
from .models import Album, Lyric, MV, Playlist, SearchResult, Singer, Song, SongUrl

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
]
