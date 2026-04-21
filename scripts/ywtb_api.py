#!/usr/bin/env python3
"""
北京信息科技大学一网通办平台 API
平台地址: https://my.bistu.edu.cn/fe/
支持: 应用查询、服务列表、搜索、站点信息
"""

import argparse
import io
import json
import sys
from pathlib import Path
from typing import Optional

# Windows GBK 编码兼容
if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, 'buffer') and sys.stdout.encoding != 'utf-8':
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        if hasattr(sys.stderr, 'buffer') and sys.stderr.encoding != 'utf-8':
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

import requests
import warnings
warnings.filterwarnings("ignore")

sys.path.insert(0, str(Path(__file__).parent))
from bistu_sso import YWTB_BASE_URL, load_config


YWTB_API_BASE = f"{YWTB_BASE_URL}/api"


class YWTBApi:
    """北信科一网通办 API 客户端"""

    def __init__(self, config: Optional[dict] = None):
        self.config = config or load_config()
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "application/json, text/plain, */*",
        })
        self.session.verify = False
        self._logged_in = False

    def _api_get(self, endpoint: str, params: dict = None) -> dict:
        """发送 GET 请求到一网通办 API"""
        url = f"{YWTB_API_BASE}/{endpoint}"
        try:
            resp = self.session.get(url, params=params, timeout=10)
            return resp.json()
        except Exception as e:
            return {"e": "ERROR", "m": str(e)}

    def _api_post(self, endpoint: str, data: dict = None) -> dict:
        """发送 POST 请求到一网通办 API"""
        url = f"{YWTB_API_BASE}/{endpoint}"
        try:
            resp = self.session.post(url, json=data or {}, timeout=10)
            return resp.json()
        except Exception as e:
            return {"e": "ERROR", "m": str(e)}

    def _check_ok(self, data: dict) -> bool:
        return data.get("e") == "OK"

    # ── 站点信息 ──────────────────────────────────────

    def get_site_info(self) -> dict:
        """获取站点信息"""
        data = self._api_get("site/info")
        if self._check_ok(data):
            return data.get("d", {})
        return {}

    def format_site_info(self, info: dict) -> str:
        """格式化站点信息输出"""
        if not info:
            return "暂无站点信息"

        lines = ["一网通办 - 站点信息："]
        name = info.get("website_name", {})
        if isinstance(name, dict):
            lines.append(f"  网站名称: {name.get('zh', '')}")
        else:
            lines.append(f"  网站名称: {name}")

        desc = info.get("website_desc", {})
        if isinstance(desc, dict):
            lines.append(f"  网站描述: {desc.get('zh', '')}")
        else:
            lines.append(f"  网站描述: {desc}")

        copyright_info = info.get("website_copyright", {})
        if isinstance(copyright_info, dict):
            lines.append(f"  版权信息: {copyright_info.get('zh', '')}")

        icp = info.get("icp_info", {})
        if isinstance(icp, dict):
            lines.append(f"  ICP备案: {icp.get('zh', '')}")

        return "\n".join(lines)

    # ── 应用查询 ──────────────────────────────────────

    def get_app_list(self) -> list:
        """获取应用列表"""
        data = self._api_get("app/list")
        if self._check_ok(data):
            return data.get("d", {}).get("list", [])
        return []

    def format_app_list(self, apps: list) -> str:
        """格式化应用列表输出"""
        if not apps:
            return "暂无可用的应用"

        lines = ["一网通办 - 应用列表："]
        for app in apps:
            name = app.get("name", {})
            name_str = name.get("zh", "") if isinstance(name, dict) else str(name)
            app_type = app.get("type", "")
            app_id = app.get("id", "")
            type_map = {1: "网页应用", 2: "微信应用", 3: "数据导入"}
            type_str = type_map.get(app_type, f"类型{app_type}")
            lines.append(f"  • {name_str} ({type_str}, ID: {app_id})")
        return "\n".join(lines)

    # ── 服务分类 ──────────────────────────────────────

    def get_service_list(self) -> list:
        """获取服务分类列表"""
        data = self._api_get("app/service-list")
        if self._check_ok(data):
            return data.get("d", [])
        return []

    def format_service_list(self, services: list) -> str:
        """格式化服务分类输出"""
        if not services:
            return "暂无服务分类数据"

        lines = ["一网通办 - 服务分类："]
        for svc in services:
            name = svc.get("name", "")
            svc_id = svc.get("id", "")
            apps = svc.get("apps", [])
            lines.append(f"  • {name} (ID: {svc_id}, 应用数: {len(apps)})")
            for app in apps[:3]:
                app_name = app.get("name", {})
                app_name_str = app_name.get("zh", "") if isinstance(app_name, dict) else str(app_name)
                lines.append(f"    - {app_name_str}")
        return "\n".join(lines)

    # ── 搜索 ──────────────────────────────────────

    def search(self, keyword: str) -> dict:
        """
        搜索服务/应用

        Args:
            keyword: 搜索关键词
        """
        data = self._api_get("home-page/search", {"keyword": keyword})
        if self._check_ok(data):
            return data.get("d", {})
        return {}

    def format_search(self, result: dict) -> str:
        """格式化搜索结果输出"""
        if not result:
            return "搜索结果为空"

        lines = ["搜索结果："]
        apps = result.get("apps", [])
        if apps:
            lines.append("  应用：")
            for app in apps[:10]:
                name = app.get("name", {})
                name_str = name.get("zh", "") if isinstance(name, dict) else str(name)
                lines.append(f"    • {name_str}")

        return "\n".join(lines) if len(lines) > 1 else "未找到相关服务"

    # ── 热门服务 ──────────────────────────────────────

    def get_hot_services(self) -> list:
        """获取热门服务"""
        data = self._api_get("home-page/hotService")
        if self._check_ok(data):
            return data.get("d", [])
        return []

    # ── 轮播图 ──────────────────────────────────────

    def get_swiper_list(self) -> list:
        """获取轮播图列表"""
        data = self._api_get("home-page/swiperList")
        if self._check_ok(data):
            return data.get("d", [])
        return []

    # ── 访客登录（微信） ──────────────────────────────

    def visitor_login(self) -> dict:
        """获取访客微信登录URL"""
        data = self._api_post("visitor/pc-login", {})
        if self._check_ok(data):
            return data.get("d", {})
        return {}

    # ── RSA公钥 ──────────────────────────────────────

    def get_pubkey(self) -> str:
        """获取登录用RSA公钥"""
        data = self._api_get("login/pubkey")
        if self._check_ok(data):
            return data.get("d", {}).get("key", "")
        return ""

    # ── 账号登录 ──────────────────────────────────────

    def login_by_account(self, account: str = "", password: str = "") -> dict:
        """
        账号密码登录一网通办

        注意：密码需要RSA加密后提交
        """
        if not account:
            ywtb_config = self.config.get("ywtb", {})
            account = self.config.get("bistu_sso", {}).get("username", "")
        if not password:
            password = self.config.get("bistu_sso", {}).get("password", "")

        # 获取公钥并加密密码
        pubkey = self.get_pubkey()
        if pubkey:
            try:
                from Crypto.PublicKey import RSA
                from Crypto.Cipher import PKCS1_v1_5
                import base64
                key = RSA.import_key(pubkey)
                cipher = PKCS1_v1_5.new(key)
                encrypted = cipher.encrypt(password.encode())
                encrypted_pwd = base64.b64encode(encrypted).decode()
            except ImportError:
                # 如果没有 pycryptodome，使用明文密码
                encrypted_pwd = password
        else:
            encrypted_pwd = password

        data = self._api_post("login/account", {
            "account": account,
            "password": encrypted_pwd,
        })

        if self._check_ok(data):
            self._logged_in = True
            token = data.get("d", {}).get("token", "")
            if token:
                self.session.headers["Authorization"] = f"Bearer {token}"

        return data


def main():
    parser = argparse.ArgumentParser(description="北信科一网通办 API")
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # 站点信息
    subparsers.add_parser("info", help="查询站点信息")

    # 应用列表
    subparsers.add_parser("apps", help="查询应用列表")

    # 服务分类
    subparsers.add_parser("services", help="查询服务分类")

    # 搜索
    search_parser = subparsers.add_parser("search", help="搜索服务/应用")
    search_parser.add_argument("keyword", type=str, help="搜索关键词")

    # 热门服务
    subparsers.add_parser("hot", help="热门服务")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    api = YWTBApi()

    if args.command == "info":
        info = api.get_site_info()
        print(api.format_site_info(info))

    elif args.command == "apps":
        apps = api.get_app_list()
        print(api.format_app_list(apps))

    elif args.command == "services":
        services = api.get_service_list()
        print(api.format_service_list(services))

    elif args.command == "search":
        result = api.search(args.keyword)
        print(api.format_search(result))

    elif args.command == "hot":
        hot = api.get_hot_services()
        if hot:
            print("热门服务：")
            for h in hot:
                name = h.get("name", {})
                name_str = name.get("zh", "") if isinstance(name, dict) else str(name)
                print(f"  • {name_str}")
        else:
            print("暂无热门服务")


if __name__ == "__main__":
    main()
