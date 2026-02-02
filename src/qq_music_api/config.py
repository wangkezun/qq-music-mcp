"""QQ Music API 配置"""

# QQ 音乐 API 基础 URL
BASE_URLS = {
    "c": "https://c.y.qq.com",
    "u": "https://u.y.qq.com",
    "shc": "https://shc.y.qq.com",
}

# 默认请求头
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://y.qq.com/",
    "Origin": "https://y.qq.com",
}

# 搜索类型
SEARCH_TYPE = {
    "song": 0,      # 歌曲
    "album": 2,     # 专辑
    "playlist": 3,  # 歌单
    "mv": 4,        # MV
    "lyric": 7,     # 歌词
    "user": 8,      # 用户
}

# 音质类型
QUALITY_TYPE = {
    "m4a": {"prefix": "C400", "ext": "m4a"},
    "128": {"prefix": "M500", "ext": "mp3"},
    "320": {"prefix": "M800", "ext": "mp3"},
    "flac": {"prefix": "F000", "ext": "flac"},
    "ape": {"prefix": "A000", "ext": "ape"},
    "hires": {"prefix": "RS01", "ext": "flac"},  # 臻品母带 24bit/192kHz
    "atmos": {"prefix": "Q001", "ext": "flac"},  # 臻品全景声 Dolby Atmos
}

# 专辑封面 URL 模板
ALBUM_COVER_URL = "https://y.qq.com/music/photo_new/T002R{size}x{size}M000{albummid}.jpg"
