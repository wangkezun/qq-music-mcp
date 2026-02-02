# QQ Music MCP Server

一个基于 MCP (Model Context Protocol) 的 QQ 音乐 API 服务器，让大语言模型能够搜索音乐、获取歌曲信息、歌词和播放链接。

## 安装

```bash
# 使用 pip
pip install qq-music-mcp

# 或使用 uv
uv pip install qq-music-mcp
```

## 在 Claude Desktop 中使用

编辑 Claude Desktop 配置文件：

- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%AppData%\Claude\claude_desktop_config.json`

添加以下配置：

```json
{
  "mcpServers": {
    "qq-music": {
      "command": "uvx",
      "args": ["qq-music-mcp"]
    }
  }
}
```

或者如果使用 pip 安装：

```json
{
  "mcpServers": {
    "qq-music": {
      "command": "qq-music-mcp"
    }
  }
}
```

然后重启 Claude Desktop。

## 功能

提供以下 MCP Tools：

| Tool 名称 | 描述 |
|-----------|------|
| `search_music` | 搜索歌曲、专辑、歌单等 |
| `get_song_detail` | 获取歌曲详情 |
| `get_song_quality` | 获取歌曲可用音质 |
| `get_lyric` | 获取歌词 |
| `get_song_url` | 获取单首歌曲播放链接 |
| `get_batch_song_urls` | 批量获取歌曲播放链接 |
| `get_album_detail` | 获取专辑详情 |
| `get_album_songs` | 获取专辑歌曲列表 |
| `get_playlist_detail` | 获取歌单详情 |
| `get_album_cover` | 获取专辑封面 URL |

## VIP 内容访问

如需获取 VIP 歌曲的高品质播放链接，请设置环境变量：

```bash
export QQ_MUSIC_COOKIE="your_qq_music_cookie_here"
```

或在 Claude Desktop 配置中添加：

```json
{
  "mcpServers": {
    "qq-music": {
      "command": "uvx",
      "args": ["qq-music-mcp"],
      "env": {
        "QQ_MUSIC_COOKIE": "your_cookie_here"
      }
    }
  }
}
```

获取 Cookie 的步骤：
1. 打开浏览器访问 https://y.qq.com
2. 登录你的 QQ 账号
3. 打开开发者工具 (F12) -> Application -> Cookies
4. 复制完整的 Cookie 字符串

## 音质类型说明

| 音质代码 | 说明 |
|----------|------|
| `m4a` | AAC 格式 |
| `128` | 128kbps MP3 |
| `320` | 320kbps MP3 |
| `flac` | FLAC 无损 |
| `ape` | APE 无损 |
| `hires` | 臻品母带 (24bit/192kHz) |
| `atmos` | 臻品全景声 (Dolby Atmos) |

## 开发

```bash
# 克隆项目
git clone https://github.com/yourusername/qq-music-mcp.git
cd qq-music-mcp

# 安装依赖
uv sync

# 运行测试
uv run mcp dev src/qq_music_api/server.py
```

## 作为 Python 库使用

```python
import asyncio
from qq_music_api import QQMusicClient

async def main():
    async with QQMusicClient() as client:
        # 搜索歌曲
        result = await client.search("周杰伦")
        print(result)

        # 获取歌词
        lyric = await client.get_lyric("000paPeF1SZp2I")
        print(lyric)

asyncio.run(main())
```

## 许可证

MIT
