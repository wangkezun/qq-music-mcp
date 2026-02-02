"""QQ Music API 数据模型"""

from pydantic import BaseModel, Field


class Singer(BaseModel):
    """歌手信息"""

    id: int = Field(default=0, alias="singerid")
    mid: str = Field(default="", alias="singermid")
    name: str = Field(default="", alias="singername")

    class Config:
        populate_by_name = True


class SongFile(BaseModel):
    """歌曲文件信息（各音质文件大小，大于0表示该音质可用）"""

    size_m4a: int = Field(default=0, alias="size_96aac")  # M4A/AAC
    size_128: int = Field(default=0, alias="size_128mp3")  # 128kbps MP3
    size_320: int = Field(default=0, alias="size_320mp3")  # 320kbps MP3
    size_flac: int = Field(default=0, alias="size_flac")  # FLAC 无损
    size_ape: int = Field(default=0, alias="size_ape")  # APE 无损
    size_hires: int = Field(default=0, alias="size_hires")  # 臻品母带
    size_atmos: int = Field(default=0, alias="size_dolby")  # 臻品全景声

    class Config:
        populate_by_name = True

    def available_qualities(self) -> list[str]:
        """返回可用的音质列表"""
        qualities = []
        if self.size_m4a > 0:
            qualities.append("m4a")
        if self.size_128 > 0:
            qualities.append("128")
        if self.size_320 > 0:
            qualities.append("320")
        if self.size_flac > 0:
            qualities.append("flac")
        if self.size_ape > 0:
            qualities.append("ape")
        if self.size_hires > 0:
            qualities.append("hires")
        if self.size_atmos > 0:
            qualities.append("atmos")
        return qualities


class Song(BaseModel):
    """歌曲信息"""

    id: int = Field(default=0, alias="songid")
    mid: str = Field(default="", alias="songmid")
    name: str = Field(default="", alias="songname")
    album_id: int = Field(default=0, alias="albumid")
    album_mid: str = Field(default="", alias="albummid")
    album_name: str = Field(default="", alias="albumname")
    singers: list[Singer] = Field(default_factory=list, alias="singer")
    duration: int = Field(default=0, alias="interval")
    pay_play: int = Field(default=0)  # 是否付费播放
    file: SongFile | None = None  # 文件信息（各音质大小）

    class Config:
        populate_by_name = True

    @property
    def singer_names(self) -> str:
        """获取歌手名称字符串"""
        return " / ".join(s.name for s in self.singers)

    @property
    def available_qualities(self) -> list[str]:
        """返回可用的音质列表"""
        if self.file:
            return self.file.available_qualities()
        return []


class Album(BaseModel):
    """专辑信息"""

    id: int = Field(default=0, alias="albumid")
    mid: str = Field(default="", alias="albummid")
    name: str = Field(default="", alias="albumname")
    singers: list[Singer] = Field(default_factory=list, alias="singer")
    publish_date: str = Field(default="", alias="aDate")
    desc: str = Field(default="")
    song_count: int = Field(default=0, alias="total_song_num")

    class Config:
        populate_by_name = True


class Playlist(BaseModel):
    """歌单信息"""

    id: int = Field(default=0, alias="dissid")
    name: str = Field(default="", alias="dissname")
    cover: str = Field(default="", alias="imgurl")
    creator: str = Field(default="", alias="creator")
    listen_count: int = Field(default=0, alias="listennum")
    song_count: int = Field(default=0, alias="song_count")

    class Config:
        populate_by_name = True


class MV(BaseModel):
    """MV 信息"""

    vid: str = Field(default="")
    name: str = Field(default="", alias="mv_name")
    singers: list[Singer] = Field(default_factory=list, alias="singer_list")
    cover: str = Field(default="", alias="mv_pic_url")
    play_count: int = Field(default=0, alias="play_cnt")
    duration: int = Field(default=0)

    class Config:
        populate_by_name = True


class Lyric(BaseModel):
    """歌词信息"""

    lyric: str = Field(default="")  # 原歌词
    trans: str = Field(default="")  # 翻译歌词


class SearchResult(BaseModel):
    """搜索结果"""

    keyword: str = Field(default="")
    total: int = Field(default=0, alias="totalnum")
    page: int = Field(default=1, alias="curpage")
    page_size: int = Field(default=20, alias="curnum")
    songs: list[Song] = Field(default_factory=list, alias="list")

    class Config:
        populate_by_name = True


class SongUrl(BaseModel):
    """歌曲播放链接"""

    mid: str = Field(default="")
    url: str = Field(default="")
    quality: str = Field(default="")
    size: int = Field(default=0)
