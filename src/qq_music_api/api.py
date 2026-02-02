"""QQ Music API FastAPI 路由"""

from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import FastAPI, Query, HTTPException
from pydantic import BaseModel

from .client import QQMusicClient
from .models import Album, Lyric, Playlist, SearchResult, Song, SongFile, SongUrl


# 全局客户端
_client: QQMusicClient | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global _client
    _client = QQMusicClient()
    yield
    await _client.close()


app = FastAPI(
    title="QQ Music API",
    description="QQ 音乐 API 接口服务",
    version="0.1.0",
    lifespan=lifespan,
)


def get_client() -> QQMusicClient:
    """获取客户端实例"""
    if _client is None:
        raise HTTPException(status_code=500, detail="Client not initialized")
    return _client


# ============ 响应模型 ============


class BaseResponse(BaseModel):
    """基础响应"""

    code: int = 0
    message: str = "success"


class SearchResponse(BaseResponse):
    """搜索响应"""

    data: SearchResult | None = None


class SongResponse(BaseResponse):
    """歌曲详情响应"""

    data: Song | None = None


class LyricResponse(BaseResponse):
    """歌词响应"""

    data: Lyric | None = None


class SongUrlResponse(BaseResponse):
    """歌曲链接响应"""

    data: list[SongUrl] = []


class AlbumResponse(BaseResponse):
    """专辑响应"""

    data: Album | None = None


class AlbumSongsResponse(BaseResponse):
    """专辑歌曲列表响应"""

    data: list[Song] = []


class PlaylistResponse(BaseResponse):
    """歌单响应"""

    class PlaylistData(BaseModel):
        playlist: Playlist | None = None
        songs: list[Song] = []

    data: PlaylistData | None = None


class CoverResponse(BaseResponse):
    """封面响应"""

    data: str = ""


class QualityResponse(BaseResponse):
    """音质信息响应"""

    class QualityData(BaseModel):
        mid: str = ""
        name: str = ""
        available_qualities: list[str] = []
        file: SongFile | None = None

    data: QualityData | None = None


# ============ API 路由 ============


@app.get("/")
async def root():
    """API 根路径"""
    return {
        "name": "QQ Music API",
        "version": "0.1.0",
        "endpoints": {
            "search": "/search",
            "song": "/song/{song_mid}",
            "quality": "/quality/{song_mid}",
            "lyric": "/lyric/{song_mid}",
            "url": "/url/{song_mid}",
            "album": "/album/{album_mid}",
            "album_songs": "/album/{album_mid}/songs",
            "playlist": "/playlist/{playlist_id}",
            "cover": "/cover/{album_mid}",
        },
    }


@app.get("/search", response_model=SearchResponse)
async def search(
    keyword: Annotated[str, Query(description="搜索关键词")],
    type: Annotated[str, Query(description="搜索类型: song/album/playlist/mv")] = "song",
    page: Annotated[int, Query(ge=1, description="页码")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="每页数量")] = 20,
):
    """
    搜索歌曲、专辑、歌单等

    - **keyword**: 搜索关键词
    - **type**: 搜索类型 (song/album/playlist/mv/lyric/user)
    - **page**: 页码，从 1 开始
    - **page_size**: 每页数量，最大 100
    """
    client = get_client()
    result = await client.search(keyword, type, page, page_size)
    return SearchResponse(data=result)


@app.get("/song/{song_mid}", response_model=SongResponse)
async def get_song(song_mid: str):
    """
    获取歌曲详情

    - **song_mid**: 歌曲 MID
    """
    client = get_client()
    song = await client.get_song_detail(song_mid)
    if not song:
        return SongResponse(code=404, message="Song not found")
    return SongResponse(data=song)


@app.get("/quality/{song_mid}", response_model=QualityResponse)
async def get_quality(song_mid: str):
    """
    获取歌曲可用音质

    - **song_mid**: 歌曲 MID

    返回该歌曲支持的所有音质及对应文件大小。
    可用音质: m4a, 128, 320, flac, ape, hires(臻品母带), atmos(全景声)
    """
    client = get_client()
    song = await client.get_song_detail(song_mid)
    if not song:
        return QualityResponse(code=404, message="Song not found")
    return QualityResponse(
        data=QualityResponse.QualityData(
            mid=song.mid,
            name=song.name,
            available_qualities=song.available_qualities,
            file=song.file,
        )
    )


@app.get("/lyric/{song_mid}", response_model=LyricResponse)
async def get_lyric(song_mid: str):
    """
    获取歌词

    - **song_mid**: 歌曲 MID
    """
    client = get_client()
    lyric = await client.get_lyric(song_mid)
    return LyricResponse(data=lyric)


@app.get("/url/{song_mid}", response_model=SongUrlResponse)
async def get_song_url(
    song_mid: str,
    quality: Annotated[str, Query(description="音质: m4a/128/320/flac/ape/hires/atmos")] = "128",
):
    """
    获取歌曲播放链接

    - **song_mid**: 歌曲 MID
    - **quality**: 音质 (m4a/128/320/flac/ape/hires/atmos)
    """
    client = get_client()
    urls = await client.get_song_url(song_mid, quality)
    return SongUrlResponse(data=urls)


@app.get("/url", response_model=SongUrlResponse)
async def get_song_urls(
    mids: Annotated[str, Query(description="歌曲 MID 列表，逗号分隔")],
    quality: Annotated[str, Query(description="音质: m4a/128/320/flac/ape/hires/atmos")] = "128",
):
    """
    批量获取歌曲播放链接

    - **mids**: 歌曲 MID 列表，用逗号分隔
    - **quality**: 音质 (m4a/128/320/flac/ape/hires/atmos)
    """
    client = get_client()
    mid_list = [m.strip() for m in mids.split(",") if m.strip()]
    if not mid_list:
        return SongUrlResponse(code=400, message="No valid MIDs provided")
    urls = await client.get_song_url(mid_list, quality)
    return SongUrlResponse(data=urls)


@app.get("/album/{album_mid}", response_model=AlbumResponse)
async def get_album(album_mid: str):
    """
    获取专辑详情

    - **album_mid**: 专辑 MID
    """
    client = get_client()
    album = await client.get_album_detail(album_mid)
    if not album:
        return AlbumResponse(code=404, message="Album not found")
    return AlbumResponse(data=album)


@app.get("/album/{album_mid}/songs", response_model=AlbumSongsResponse)
async def get_album_songs(album_mid: str):
    """
    获取专辑歌曲列表

    - **album_mid**: 专辑 MID
    """
    client = get_client()
    songs = await client.get_album_songs(album_mid)
    return AlbumSongsResponse(data=songs)


@app.get("/playlist/{playlist_id}", response_model=PlaylistResponse)
async def get_playlist(playlist_id: int):
    """
    获取歌单详情和歌曲列表

    - **playlist_id**: 歌单 ID
    """
    client = get_client()
    playlist, songs = await client.get_playlist_detail(playlist_id)
    if not playlist:
        return PlaylistResponse(code=404, message="Playlist not found")
    return PlaylistResponse(
        data=PlaylistResponse.PlaylistData(playlist=playlist, songs=songs)
    )


@app.get("/cover/{album_mid}", response_model=CoverResponse)
async def get_cover(
    album_mid: str,
    size: Annotated[int, Query(description="图片尺寸")] = 300,
):
    """
    获取专辑封面 URL

    - **album_mid**: 专辑 MID
    - **size**: 图片尺寸 (默认 300)
    """
    url = QQMusicClient.get_album_cover(album_mid, size)
    return CoverResponse(data=url)
