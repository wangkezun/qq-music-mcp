"""QQ Music MCP Server"""

import json
import logging
import sys
from pathlib import Path
from typing import Literal

from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

# 支持直接运行和作为模块导入两种方式
if __name__ == "__main__" or __package__ is None or __package__ == "":
    # 直接运行时，添加 src 目录到路径
    src_dir = Path(__file__).parent.parent
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))
    from qq_music_api.client import QQMusicClient
    from qq_music_api.models import Song, Album, Playlist, Lyric, SongUrl
else:
    # 作为包导入时，使用相对导入
    from .client import QQMusicClient
    from .models import Song, Album, Playlist, Lyric, SongUrl

# 加载环境变量
load_dotenv()

# 配置日志输出到 stderr
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

# 创建 MCP 服务器
mcp = FastMCP("qq-music")


def _format_song(song: Song) -> dict:
    """格式化歌曲信息为字典"""
    return {
        "mid": song.mid,
        "name": song.name,
        "singers": song.singer_names,
        "album": song.album_name,
        "album_mid": song.album_mid,
        "duration_seconds": song.duration,
        "available_qualities": song.available_qualities if song.file else [],
    }


def _format_album(album: Album) -> dict:
    """格式化专辑信息为字典"""
    return {
        "mid": album.mid,
        "name": album.name,
        "singers": " / ".join(s.name for s in album.singers),
        "publish_date": album.publish_date,
        "description": album.desc,
        "song_count": album.song_count,
    }


def _format_playlist(playlist: Playlist) -> dict:
    """格式化歌单信息为字典"""
    return {
        "id": playlist.id,
        "name": playlist.name,
        "cover": playlist.cover,
        "creator": playlist.creator,
        "listen_count": playlist.listen_count,
        "song_count": playlist.song_count,
    }


@mcp.tool()
async def search_music(
    keyword: str,
    search_type: Literal["song", "album", "playlist", "mv", "lyric", "user"] = "song",
    page: int = 1,
    page_size: int = 20,
) -> str:
    """搜索 QQ 音乐

    Args:
        keyword: 搜索关键词
        search_type: 搜索类型，可选值: song(歌曲), album(专辑), playlist(歌单), mv, lyric(歌词), user(用户)
        page: 页码，从1开始
        page_size: 每页数量，默认20

    Returns:
        搜索结果的 JSON 字符串
    """
    async with QQMusicClient() as client:
        result = await client.search(keyword, search_type, page, page_size)
        return json.dumps(
            {
                "keyword": result.keyword,
                "total": result.total,
                "page": result.page,
                "page_size": result.page_size,
                "songs": [_format_song(song) for song in result.songs],
            },
            ensure_ascii=False,
            indent=2,
        )


@mcp.tool()
async def get_song_detail(song_mid: str) -> str:
    """获取歌曲详情

    Args:
        song_mid: 歌曲的 MID 标识符

    Returns:
        歌曲详情的 JSON 字符串，包含歌曲名、歌手、专辑、时长、可用音质等信息
    """
    async with QQMusicClient() as client:
        song = await client.get_song_detail(song_mid)
        if song is None:
            return json.dumps({"error": "歌曲不存在"}, ensure_ascii=False)
        return json.dumps(_format_song(song), ensure_ascii=False, indent=2)


@mcp.tool()
async def get_song_quality(song_mid: str) -> str:
    """获取歌曲可用的音质列表

    Args:
        song_mid: 歌曲的 MID 标识符

    Returns:
        可用音质列表的 JSON 字符串。音质类型包括:
        - m4a: AAC 格式
        - 128: 128kbps MP3
        - 320: 320kbps MP3
        - flac: FLAC 无损
        - ape: APE 无损
        - hires: 臻品母带 (24bit/192kHz)
        - atmos: 臻品全景声 (Dolby Atmos)
    """
    async with QQMusicClient() as client:
        song = await client.get_song_detail(song_mid)
        if song is None:
            return json.dumps({"error": "歌曲不存在"}, ensure_ascii=False)
        return json.dumps(
            {
                "mid": song.mid,
                "name": song.name,
                "available_qualities": song.available_qualities,
            },
            ensure_ascii=False,
            indent=2,
        )


@mcp.tool()
async def get_lyric(song_mid: str) -> str:
    """获取歌词

    Args:
        song_mid: 歌曲的 MID 标识符

    Returns:
        歌词的 JSON 字符串，包含原歌词和翻译歌词（如有）
    """
    async with QQMusicClient() as client:
        lyric = await client.get_lyric(song_mid)
        return json.dumps(
            {"lyric": lyric.lyric, "translation": lyric.trans},
            ensure_ascii=False,
            indent=2,
        )


@mcp.tool()
async def get_song_url(
    song_mid: str,
    quality: Literal["m4a", "128", "320", "flac", "ape", "hires", "atmos"] = "128",
) -> str:
    """获取单首歌曲的播放链接

    Args:
        song_mid: 歌曲的 MID 标识符
        quality: 音质类型，可选值:
            - m4a: AAC 格式
            - 128: 128kbps MP3 (默认)
            - 320: 320kbps MP3
            - flac: FLAC 无损
            - ape: APE 无损
            - hires: 臻品母带
            - atmos: 臻品全景声

    Returns:
        播放链接的 JSON 字符串。注意：高品质音源可能需要 VIP 权限
    """
    async with QQMusicClient() as client:
        urls = await client.get_song_url(song_mid, quality)
        if not urls:
            return json.dumps({"error": "获取播放链接失败"}, ensure_ascii=False)
        url_info = urls[0]
        return json.dumps(
            {
                "mid": url_info.mid,
                "url": url_info.url,
                "quality": url_info.quality,
                "size": url_info.size,
            },
            ensure_ascii=False,
            indent=2,
        )


@mcp.tool()
async def get_batch_song_urls(
    mids: str,
    quality: Literal["m4a", "128", "320", "flac", "ape", "hires", "atmos"] = "128",
) -> str:
    """批量获取多首歌曲的播放链接

    Args:
        mids: 多个歌曲 MID，用逗号分隔，例如 "mid1,mid2,mid3"
        quality: 音质类型，可选值:
            - m4a: AAC 格式
            - 128: 128kbps MP3 (默认)
            - 320: 320kbps MP3
            - flac: FLAC 无损
            - ape: APE 无损
            - hires: 臻品母带
            - atmos: 臻品全景声

    Returns:
        播放链接列表的 JSON 字符串
    """
    mid_list = [m.strip() for m in mids.split(",") if m.strip()]
    if not mid_list:
        return json.dumps({"error": "请提供有效的歌曲 MID"}, ensure_ascii=False)

    async with QQMusicClient() as client:
        urls = await client.get_song_url(mid_list, quality)
        return json.dumps(
            {
                "quality": quality,
                "urls": [
                    {
                        "mid": u.mid,
                        "url": u.url,
                        "size": u.size,
                    }
                    for u in urls
                ],
            },
            ensure_ascii=False,
            indent=2,
        )


@mcp.tool()
async def get_album_detail(album_mid: str) -> str:
    """获取专辑详情

    Args:
        album_mid: 专辑的 MID 标识符

    Returns:
        专辑详情的 JSON 字符串，包含专辑名、歌手、发行日期、描述、歌曲数量等
    """
    async with QQMusicClient() as client:
        album = await client.get_album_detail(album_mid)
        if album is None:
            return json.dumps({"error": "专辑不存在"}, ensure_ascii=False)
        result = _format_album(album)
        result["cover_url"] = client.get_album_cover(album_mid, 500)
        return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool()
async def get_album_songs(album_mid: str) -> str:
    """获取专辑的歌曲列表

    Args:
        album_mid: 专辑的 MID 标识符

    Returns:
        专辑歌曲列表的 JSON 字符串
    """
    async with QQMusicClient() as client:
        songs = await client.get_album_songs(album_mid)
        return json.dumps(
            {
                "album_mid": album_mid,
                "song_count": len(songs),
                "songs": [_format_song(song) for song in songs],
            },
            ensure_ascii=False,
            indent=2,
        )


@mcp.tool()
async def get_playlist_detail(playlist_id: int) -> str:
    """获取歌单详情和歌曲列表

    Args:
        playlist_id: 歌单 ID（数字）

    Returns:
        歌单详情和歌曲列表的 JSON 字符串
    """
    async with QQMusicClient() as client:
        playlist, songs = await client.get_playlist_detail(playlist_id)
        if playlist is None:
            return json.dumps({"error": "歌单不存在"}, ensure_ascii=False)
        result = _format_playlist(playlist)
        result["songs"] = [_format_song(song) for song in songs]
        return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool()
def get_album_cover(album_mid: str, size: int = 300) -> str:
    """获取专辑封面图片 URL

    Args:
        album_mid: 专辑的 MID 标识符
        size: 图片尺寸，常用值: 150, 300, 500

    Returns:
        专辑封面图片的 URL
    """
    url = QQMusicClient.get_album_cover(album_mid, size)
    return json.dumps(
        {"album_mid": album_mid, "size": size, "url": url},
        ensure_ascii=False,
        indent=2,
    )


def run_server():
    """运行 MCP 服务器"""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    run_server()
