"""QQ Music MCP Server 入口"""

from .server import run_server


def main():
    """启动 MCP 服务器"""
    run_server()


if __name__ == "__main__":
    main()
