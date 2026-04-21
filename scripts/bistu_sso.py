#!/usr/bin/env python3
"""
北京信息科技大学统一身份认证 (SSO) 登录模块
SSO 地址: https://wxjw.bistu.edu.cn/authserver/login
支持: 账号密码登录
"""

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
from bs4 import BeautifulSoup

warnings.filterwarnings("ignore", message="Unverified HTTPS request")

CONFIG_PATH = Path(__file__).parent.parent / "config.json"
SSO_BASE_URL = "https://wxjw.bistu.edu.cn"
JWXT_BASE_URL = "https://jwxt.bistu.edu.cn"
YWTB_BASE_URL = "https://my.bistu.edu.cn"


def load_config() -> dict:
    """加载配置文件"""
    if not CONFIG_PATH.exists():
        print("配置文件不存在，请先运行 python scripts/setup.py", file=sys.stderr)
        sys.exit(1)
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


class BISTUSSOClient:
    """北京信息科技大学统一身份认证客户端"""

    def __init__(self, config: Optional[dict] = None):
        self.config = config or load_config()
        self.sso_config = self.config.get("bistu_sso", {})
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        })
        self.session.verify = False
        self._logged_in = False
        self._weu_token = None

    def _get_lt_and_execution(self, login_url: str) -> tuple:
        """从登录页面提取 lt 和 execution 参数"""
        resp = self.session.get(login_url, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        lt = ""
        execution = ""

        # 获取 lt（可能为空）
        lt_input = soup.find("input", {"name": "lt", "type": "hidden"})
        if lt_input:
            lt = lt_input.get("value", "")

        # 获取 execution
        execution_input = soup.find("input", {"name": "execution", "type": "hidden"})
        if execution_input:
            execution = execution_input.get("value", "")

        return lt, execution

    def login_by_password(self, service_url: str = "") -> requests.Session:
        """
        通过账号密码方式登录 SSO

        Args:
            service_url: 目标服务的回调 URL，登录成功后自动跳转

        Returns:
            已认证的 requests.Session
        """
        username = self.sso_config.get("username", "")
        password = self.sso_config.get("password", "")

        if not username or not password:
            print("未配置 SSO 用户名或密码", file=sys.stderr)
            sys.exit(1)

        # 构建登录 URL
        if service_url:
            login_url = f"{SSO_BASE_URL}/authserver/login?service={service_url}"
        else:
            login_url = f"{SSO_BASE_URL}/authserver/login"

        # 获取 lt 和 execution
        lt, execution = self._get_lt_and_execution(login_url)

        # 提交登录表单
        # 注意：BISTU SSO 使用 passwordText（明文）+ password（隐藏，由JS填充）
        # cllt 必须设为 userNameLogin
        login_data = {
            "username": username,
            "passwordText": password,
            "password": password,
            "lt": lt,
            "execution": execution,
            "_eventId": "submit",
            "cllt": "userNameLogin",
            "dllt": "generalLogin",
            "rmShown": "1",
        }

        resp = self.session.post(
            f"{SSO_BASE_URL}/authserver/login",
            data=login_data,
            allow_redirects=True,
            timeout=15,
        )

        # 检查登录是否成功
        if "authserver/login" in resp.url and "needCaptcha" not in resp.url:
            print("SSO 登录失败，请检查用户名和密码", file=sys.stderr)
            sys.exit(1)

        self._logged_in = True

        # 提取 _WEU token 用于 CSRF 防护
        for cookie in self.session.cookies:
            if cookie.name == "_WEU":
                self._weu_token = cookie.value
                break

        return self.session

    def get_jwxt_session(self) -> requests.Session:
        """获取已认证的教管平台 Session"""
        service_url = f"{JWXT_BASE_URL}/jwapp/sys/homeapp/index.do"
        session = self.login_by_password(service_url)

        # 设置教管平台 API 所需的 headers
        session.headers.update({
            "X-Requested-With": "XMLHttpRequest",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Referer": f"{JWXT_BASE_URL}/jwapp/sys/homeapp/home/index.html",
        })

        # 设置 CSRF token
        if self._weu_token:
            session.headers["X-CSRF-TOKEN"] = self._weu_token

        return session

    def get_ywtb_session(self) -> requests.Session:
        """获取一网通办 Session（需要单独登录）"""
        # 一网通办使用独立的登录系统，暂不支持 SSO 直连
        # 返回一个新 session，后续需要单独调用 YWTB 的登录 API
        return self.session

    @property
    def weu_token(self) -> Optional[str]:
        """获取 CSRF token (_WEU)"""
        return self._weu_token

    @property
    def is_logged_in(self) -> bool:
        return self._logged_in


if __name__ == "__main__":
    config = load_config()
    client = BISTUSSOClient(config)

    session = client.get_jwxt_session()
    if client.is_logged_in:
        print("SSO 登录成功")
        print(f"CSRF Token (_WEU): {client.weu_token[:20] if client.weu_token else 'N/A'}...")
        print(f"Cookies: {[c.name for c in session.cookies]}")
    else:
        print("SSO 登录失败")
