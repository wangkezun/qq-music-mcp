"""QQ Music API HTTP 客户端"""

import base64
import json
import os
import random
import re
import time

import httpx

from .config import (
    ALBUM_COVER_URL,
    BASE_URLS,
    DEFAULT_HEADERS,
    QUALITY_TYPE,
    SEARCH_TYPE,
)
from .models import Album, Lyric, MV, Playlist, SearchResult, Singer, Song, SongFile, SongUrl


class QQMusicClient:
    """QQ 音乐 API 客户端"""

    def __init__(self, cookie: str | None = None):
        """
        初始化客户端

        Args:
            cookie: QQ 音乐 cookie，用于获取 VIP 内容。
                    如果未提供，将尝试从环境变量 QQ_MUSIC_COOKIE 获取。
        """
        # 优先使用传入的 cookie，否则从环境变量获取
        if cookie is None:
            cookie = os.environ.get("QQ_MUSIC_COOKIE", "")
        self.cookie = cookie
        self._client = httpx.AsyncClient(
            headers=DEFAULT_HEADERS,
            timeout=30.0,
            follow_redirects=True,
        )
        if cookie:
            self._client.headers["Cookie"] = cookie

    async def close(self):
        """关闭客户端"""
        await self._client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    def _generate_guid(self) -> str:
        """生成随机 GUID"""
        return str(random.randint(1000000000, 9999999999))

    async def _request(
        self,
        url: str,
        params: dict | None = None,
        data: dict | None = None,
        method: str = "GET",
    ) -> dict:
        """
        发送请求

        Args:
            url: 请求 URL
            params: URL 参数
            data: POST 数据
            method: 请求方法

        Returns:
            JSON 响应数据
        """
        if method == "GET":
            response = await self._client.get(url, params=params)
        else:
            response = await self._client.post(url, params=params, json=data)

        response.raise_for_status()

        text = response.text
        # 处理 JSONP 响应
        if text.startswith("callback(") or text.startswith("MusicJsonCallback("):
            match = re.search(r"\(({.*})\)", text, re.DOTALL)
            if match:
                text = match.group(1)

        return json.loads(text)

    async def search(
        self,
        keyword: str,
        search_type: str = "song",
        page: int = 1,
        page_size: int = 20,
    ) -> SearchResult:
        """
        搜索歌曲、专辑、歌单等

        Args:
            keyword: 搜索关键词
            search_type: 搜索类型 (song/album/playlist/mv/lyric/user)
            page: 页码
            page_size: 每页数量

        Returns:
            SearchResult 搜索结果
        """
        url = f"{BASE_URLS['c']}/soso/fcgi-bin/client_search_cp"
        params = {
            "w": keyword,
            "p": page,
            "n": page_size,
            "t": SEARCH_TYPE.get(search_type, 0),
            "format": "json",
            "inCharset": "utf8",
            "outCharset": "utf-8",
            "new_json": 1,
            "aggr": 1,
            "cr": 1,
            "lossless": 0,
        }

        result = await self._request(url, params)

        if result.get("code") != 0:
            return SearchResult(keyword=keyword)

        song_data = result.get("data", {}).get("song", {})
        songs = []
        for item in song_data.get("list", []):
            singers = [
                Singer(
                    singerid=s.get("id", 0),
                    singermid=s.get("mid", ""),
                    singername=s.get("name", ""),
                )
                for s in item.get("singer", [])
            ]
            song = Song(
                songid=item.get("id", 0),
                songmid=item.get("mid", ""),
                songname=item.get("name", ""),
                albumid=item.get("album", {}).get("id", 0),
                albummid=item.get("album", {}).get("mid", ""),
                albumname=item.get("album", {}).get("name", ""),
                singer=singers,
                interval=item.get("interval", 0),
                pay_play=item.get("pay", {}).get("pay_play", 0),
            )
            songs.append(song)

        return SearchResult(
            keyword=keyword,
            totalnum=song_data.get("totalnum", 0),
            curpage=page,
            curnum=page_size,
            list=songs,
        )

    async def get_song_detail(self, song_mid: str) -> Song | None:
        """
        获取歌曲详情

        Args:
            song_mid: 歌曲 MID

        Returns:
            Song 歌曲详情
        """
        url = f"{BASE_URLS['u']}/cgi-bin/musicu.fcg"
        data = {
            "songinfo": {
                "method": "get_song_detail_yqq",
                "module": "music.pf_song_detail_svr",
                "param": {"song_mid": song_mid},
            }
        }

        params = {
            "format": "json",
            "data": json.dumps(data),
        }

        result = await self._request(url, params)

        if result.get("code") != 0:
            return None

        track = result.get("songinfo", {}).get("data", {}).get("track_info", {})
        if not track:
            return None

        singers = [
            Singer(
                singerid=s.get("id", 0),
                singermid=s.get("mid", ""),
                singername=s.get("name", ""),
            )
            for s in track.get("singer", [])
        ]

        # 解析文件信息
        file_info = track.get("file", {})
        song_file = SongFile(
            size_96aac=file_info.get("size_96aac", 0),
            size_128mp3=file_info.get("size_128mp3", 0),
            size_320mp3=file_info.get("size_320mp3", 0),
            size_flac=file_info.get("size_flac", 0),
            size_ape=file_info.get("size_ape", 0),
            size_hires=file_info.get("size_hires", 0),
            size_dolby=file_info.get("size_dolby", 0),
        )

        return Song(
            songid=track.get("id", 0),
            songmid=track.get("mid", ""),
            songname=track.get("name", ""),
            albumid=track.get("album", {}).get("id", 0),
            albummid=track.get("album", {}).get("mid", ""),
            albumname=track.get("album", {}).get("name", ""),
            singer=singers,
            interval=track.get("interval", 0),
            pay_play=track.get("pay", {}).get("pay_play", 0),
            file=song_file,
        )

    async def get_lyric(self, song_mid: str) -> Lyric:
        """
        获取歌词

        Args:
            song_mid: 歌曲 MID

        Returns:
            Lyric 歌词信息
        """
        url = f"{BASE_URLS['c']}/lyric/fcgi-bin/fcg_query_lyric_new.fcg"
        params = {
            "songmid": song_mid,
            "g_tk": 5381,
            "format": "json",
            "inCharset": "utf8",
            "outCharset": "utf-8",
            "nobase64": 0,
        }

        # 歌词接口需要特殊的 Referer
        headers = {"Referer": "https://y.qq.com/portal/player.html"}

        response = await self._client.get(url, params=params, headers=headers)
        response.raise_for_status()
        result = response.json()

        if result.get("code") != 0:
            return Lyric()

        lyric_b64 = result.get("lyric", "")
        trans_b64 = result.get("trans", "")

        lyric = ""
        trans = ""

        if lyric_b64:
            try:
                lyric = base64.b64decode(lyric_b64).decode("utf-8")
            except Exception:
                lyric = lyric_b64

        if trans_b64:
            try:
                trans = base64.b64decode(trans_b64).decode("utf-8")
            except Exception:
                trans = trans_b64

        return Lyric(lyric=lyric, trans=trans)

    async def get_song_url(
        self,
        song_mid: str | list[str],
        quality: str = "128",
    ) -> list[SongUrl]:
        """
        获取歌曲播放链接

        Args:
            song_mid: 歌曲 MID 或 MID 列表
            quality: 音质 (m4a/128/320/flac/ape/hires/atmos)

        Returns:
            SongUrl 列表
        """
        if isinstance(song_mid, str):
            song_mids = [song_mid]
        else:
            song_mids = song_mid

        quality_info = QUALITY_TYPE.get(quality, QUALITY_TYPE["128"])
        prefix = quality_info["prefix"]
        ext = quality_info["ext"]

        guid = self._generate_guid()
        uin = "0"

        # 从 cookie 中提取 uin
        if self.cookie:
            match = re.search(r"uin=(\d+)", self.cookie)
            if match:
                uin = match.group(1)

        url = f"{BASE_URLS['u']}/cgi-bin/musicu.fcg"

        filenames = [f"{prefix}{mid}{mid}.{ext}" for mid in song_mids]

        data = {
            "req_0": {
                "module": "vkey.GetVkeyServer",
                "method": "CgiGetVkey",
                "param": {
                    "guid": guid,
                    "songmid": song_mids,
                    "songtype": [0] * len(song_mids),
                    "uin": uin,
                    "loginflag": 1 if self.cookie else 0,
                    "platform": "20",
                    "filename": filenames,
                },
            }
        }

        params = {
            "format": "json",
            "data": json.dumps(data),
        }

        result = await self._request(url, params)

        if result.get("code") != 0:
            return []

        req_data = result.get("req_0", {}).get("data", {})
        sip = req_data.get("sip", [""])[0]
        midurlinfo = req_data.get("midurlinfo", [])

        urls = []
        for info in midurlinfo:
            purl = info.get("purl", "")
            mid = info.get("songmid", "")
            if purl:
                urls.append(
                    SongUrl(
                        mid=mid,
                        url=f"{sip}{purl}",
                        quality=quality,
                        size=info.get("filesize", 0),
                    )
                )
            else:
                urls.append(SongUrl(mid=mid, quality=quality))

        return urls

    async def get_album_detail(self, album_mid: str) -> Album | None:
        """
        获取专辑详情

        Args:
            album_mid: 专辑 MID

        Returns:
            Album 专辑详情
        """
        url = f"{BASE_URLS['c']}/v8/fcg-bin/fcg_v8_album_info_cp.fcg"
        params = {
            "albummid": album_mid,
            "format": "json",
            "inCharset": "utf8",
            "outCharset": "utf-8",
        }

        result = await self._request(url, params)

        if result.get("code") != 0:
            return None

        album_data = result.get("data", {})
        if not album_data:
            return None

        # 从歌曲列表中提取歌手信息
        song_list = album_data.get("list", [])
        singers = []
        if song_list:
            for s in song_list[0].get("singer", []):
                singers.append(
                    Singer(
                        singerid=s.get("id", 0),
                        singermid=s.get("mid", ""),
                        singername=s.get("name", ""),
                    )
                )

        return Album(
            albumid=album_data.get("id", 0),
            albummid=album_data.get("mid", ""),
            albumname=album_data.get("name", ""),
            singer=singers,
            aDate=album_data.get("aDate", ""),
            desc=album_data.get("desc", ""),
            total_song_num=album_data.get("total_song_num", len(song_list)),
        )

    async def get_album_songs(self, album_mid: str) -> list[Song]:
        """
        获取专辑歌曲列表

        Args:
            album_mid: 专辑 MID

        Returns:
            Song 列表
        """
        url = f"{BASE_URLS['c']}/v8/fcg-bin/fcg_v8_album_info_cp.fcg"
        params = {
            "albummid": album_mid,
            "format": "json",
            "inCharset": "utf8",
            "outCharset": "utf-8",
        }

        result = await self._request(url, params)

        if result.get("code") != 0:
            return []

        song_list = result.get("data", {}).get("list", [])

        songs = []
        for item in song_list:
            singers = [
                Singer(
                    singerid=s.get("id", 0),
                    singermid=s.get("mid", ""),
                    singername=s.get("name", ""),
                )
                for s in item.get("singer", [])
            ]
            song = Song(
                songid=item.get("songid", 0),
                songmid=item.get("songmid", ""),
                songname=item.get("songname", ""),
                albumid=item.get("albumid", 0),
                albummid=item.get("albummid", ""),
                albumname=item.get("albumname", ""),
                singer=singers,
                interval=item.get("interval", 0),
            )
            songs.append(song)

        return songs

    async def get_playlist_detail(self, playlist_id: int) -> tuple[Playlist | None, list[Song]]:
        """
        获取歌单详情和歌曲列表

        Args:
            playlist_id: 歌单 ID

        Returns:
            (Playlist, Song 列表)
        """
        url = f"{BASE_URLS['c']}/qzone/fcg-bin/fcg_ucc_getcdinfo_byids_cp.fcg"
        params = {
            "type": 1,
            "json": 1,
            "utf8": 1,
            "onlysong": 0,
            "disstid": playlist_id,
            "format": "json",
            "inCharset": "utf8",
            "outCharset": "utf-8",
        }

        result = await self._request(url, params)

        if result.get("code") != 0:
            return None, []

        cdlist = result.get("cdlist", [])
        if not cdlist:
            return None, []

        cd = cdlist[0]

        playlist = Playlist(
            dissid=cd.get("dissid", 0),
            dissname=cd.get("dissname", ""),
            imgurl=cd.get("logo", ""),
            creator=cd.get("nick", ""),
            listennum=cd.get("visitnum", 0),
            song_count=cd.get("songnum", 0),
        )

        songs = []
        for item in cd.get("songlist", []):
            singers = [
                Singer(
                    singerid=s.get("id", 0),
                    singermid=s.get("mid", ""),
                    singername=s.get("name", ""),
                )
                for s in item.get("singer", [])
            ]
            song = Song(
                songid=item.get("id", 0),
                songmid=item.get("mid", ""),
                songname=item.get("name", ""),
                albumid=item.get("album", {}).get("id", 0),
                albummid=item.get("album", {}).get("mid", ""),
                albumname=item.get("album", {}).get("name", ""),
                singer=singers,
                interval=item.get("interval", 0),
            )
            songs.append(song)

        return playlist, songs

    @staticmethod
    def get_album_cover(album_mid: str, size: int = 300) -> str:
        """
        获取专辑封面 URL

        Args:
            album_mid: 专辑 MID
            size: 图片尺寸

        Returns:
            封面图片 URL
        """
        return ALBUM_COVER_URL.format(size=size, albummid=album_mid)
