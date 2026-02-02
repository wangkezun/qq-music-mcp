"""QQ Music API 入口"""

import uvicorn
from dotenv import load_dotenv


def main():
    """启动 API 服务"""
    # 加载 .env 文件
    load_dotenv()

    uvicorn.run(
        "qq_music_api.api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )


if __name__ == "__main__":
    main()
