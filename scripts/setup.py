#!/usr/bin/env python3
"""
openclaw-bistu 一键交互式配置向导
引导用户完成所有平台的认证配置
"""

import json
import os
import sys
from pathlib import Path


CONFIG_PATH = Path(__file__).parent.parent / "config.json"
EXAMPLE_PATH = Path(__file__).parent.parent / "config.example.json"


def colored_input(prompt: str, default: str = "") -> str:
    """带默认值的输入"""
    if default:
        result = input(f"{prompt} [{default}]: ").strip()
        return result if result else default
    return input(f"{prompt}: ").strip()


def mask_password(password: str) -> str:
    """密码脱敏"""
    if len(password) <= 2:
        return "*" * len(password)
    return password[0] + "*" * (len(password) - 2) + password[-1]


def main():
    print("🎓 openclaw-bistu 配置向导")
    print("=" * 50)
    print("本向导将帮助你配置北信科校园助手的各项服务凭证\n")

    # 读取示例配置
    if EXAMPLE_PATH.exists():
        with open(EXAMPLE_PATH, "r", encoding="utf-8") as f:
            config = json.load(f)
    else:
        config = {}

    # ── 1. 统一身份认证 ─────────────────────────────
    print("📡 第 1 步: 统一身份认证 (SSO)")
    print("   用于登录教管平台和一网通办")
    print("   SSO 地址: https://sso.bistu.edu.cn")
    print()

    sso = config.get("bistu_sso", {})
    sso["username"] = colored_input("学号/教工号", sso.get("username", ""))
    sso["password"] = colored_input("密码 (输入后将明文存储)", "")
    sso["login_method"] = colored_input(
        "登录方式 (password/qrcode/sms/webauthn)", 
        sso.get("login_method", "password")
    )
    config["bistu_sso"] = sso
    print("✅ SSO 配置完成\n")

    # ── 2. 学习通 ────────────────────────────────────
    print("📡 第 2 步: 超星学习通 (可选)")
    print("   用于查询课程、作业和签到")
    print()

    chaoxing = config.get("chaoxing", {})
    configure_chaoxing = colored_input("是否配置学习通? (y/n)", "n")
    if configure_chaoxing.lower() == "y":
        chaoxing["phone"] = colored_input("学习通手机号", chaoxing.get("phone", ""))
        chaoxing["password"] = colored_input("学习通密码", "")
    config["chaoxing"] = chaoxing
    print("✅ 学习通配置完成\n")

    # ── 3. 校友圈 ────────────────────────────────────
    print("📡 第 3 步: 云上校友圈 BISTU 论坛 (可选)")
    print("   微信小程序校友圈接入")
    print("   获取方式见 docs/ALUMNI_CIRCLE_GUIDE.md")
    print()

    alumni = config.get("alumni_circle", {})
    configure_alumni = colored_input("是否配置校友圈? (y/n)", "n")
    if configure_alumni.lower() == "y":
        alumni["token"] = colored_input("校友圈 Token", "")
        alumni["env_id"] = colored_input("云开发环境 ID (可选)", alumni.get("env_id", ""))
        alumni["api_base"] = colored_input("自定义 API 地址 (可选)", alumni.get("api_base", ""))
    config["alumni_circle"] = alumni
    print("✅ 校友圈配置完成\n")

    # ── 4. 校园邮箱 ──────────────────────────────────
    print("📡 第 4 步: 校园邮箱 (可选)")
    print("   用于查看邮件 (IMAP 协议)")
    print()

    email_cfg = config.get("bistu_email", {})
    configure_email = colored_input("是否配置校园邮箱? (y/n)", "n")
    if configure_email.lower() == "y":
        email_cfg["address"] = colored_input("邮箱地址", email_cfg.get("address", ""))
        email_cfg["password"] = colored_input("邮箱密码", "")
        email_cfg["imap_server"] = colored_input(
            "IMAP 服务器", email_cfg.get("imap_server", "imap.bistu.edu.cn")
        )
        email_cfg["smtp_server"] = colored_input(
            "SMTP 服务器", email_cfg.get("smtp_server", "smtp.bistu.edu.cn")
        )
    config["bistu_email"] = email_cfg
    print("✅ 邮箱配置完成\n")

    # ── 5. 校区偏好 ──────────────────────────────────
    print("📡 第 5 步: 校区偏好")
    campus = config.get("campus", {})
    campus["default_campus"] = colored_input(
        "默认校区 (小营/清河/太行路)", campus.get("default_campus", "小营")
    )
    config["campus"] = campus
    print("✅ 校区配置完成\n")

    # ── 确认并保存 ────────────────────────────────────
    print("=" * 50)
    print("📋 配置摘要：")
    print(f"  SSO 用户名: {sso.get('username', '(未配置)')}")
    print(f"  SSO 密码: {mask_password(sso.get('password', ''))}")
    print(f"  学习通: {'已配置' if chaoxing.get('phone') else '未配置'}")
    print(f"  校友圈: {'已配置' if alumni.get('token') else '未配置'}")
    print(f"  校园邮箱: {'已配置' if email_cfg.get('address') else '未配置'}")
    print(f"  默认校区: {campus.get('default_campus', '小营')}")
    print()

    confirm = colored_input("确认保存配置? (y/n)", "y")
    if confirm.lower() != "y":
        print("❌ 配置已取消")
        return

    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

    print(f"\n✅ 配置已保存到 {CONFIG_PATH}")
    print("🔒 请勿将 config.json 分享给他人")
    print("\n🚀 现在可以开始使用 openclaw-bistu 了！")
    print("   直接与 AI 对话即可，例如：'今天有什么课？'")


if __name__ == "__main__":
    main()
