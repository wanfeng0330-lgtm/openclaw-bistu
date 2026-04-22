#!/usr/bin/env python3
"""
北信科校园生活信息
支持: 校历、教学周、食堂推荐、图书馆查询、邮箱、往年资源、镜像换源、正版软件、在线工具
"""

import argparse
import io
import json
import sys
from datetime import datetime
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


CONFIG_PATH = Path(__file__).parent.parent / "config.json"


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        print(f"❌ 配置文件不存在: {CONFIG_PATH}", file=sys.stderr)
        sys.exit(1)
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


# ── 校历与教学周 ──────────────────────────────────────

# 北信科 2025-2026 学年校历（需根据实际校历更新）
SEMESTER_CONFIG = {
    "2025-2026-1": {
        "name": "2025-2026 第一学期",
        "start": "2025-09-01",
        "end": "2026-01-16",
        "weeks": 20,
        "events": [
            {"week": 1, "name": "开学注册"},
            {"week": 18, "name": "考试周开始"},
            {"week": 20, "name": "考试周结束 / 寒假开始"},
        ],
    },
    "2025-2026-2": {
        "name": "2025-2026 第二学期",
        "start": "2026-02-23",
        "end": "2026-07-03",
        "weeks": 19,
        "events": [
            {"week": 1, "name": "开学注册"},
            {"week": 17, "name": "考试周开始"},
            {"week": 19, "name": "考试周结束 / 暑假开始"},
        ],
    },
}


def get_current_semester() -> str:
    """获取当前学期"""
    now = datetime.now()
    for sem_key, sem_info in SEMESTER_CONFIG.items():
        start = datetime.strptime(sem_info["start"], "%Y-%m-%d")
        end = datetime.strptime(sem_info["end"], "%Y-%m-%d")
        if start <= now <= end:
            return sem_key
    # 默认返回最近的学期
    return "2025-2026-2"


def get_current_week() -> int:
    """计算当前教学周"""
    sem_key = get_current_semester()
    sem = SEMESTER_CONFIG.get(sem_key, {})
    start = datetime.strptime(sem.get("start", "2025-09-01"), "%Y-%m-%d")
    now = datetime.now()
    diff = (now - start).days
    week = diff // 7 + 1
    return max(1, min(week, sem.get("weeks", 20)))


def cmd_calendar(args):
    """显示校历"""
    sem_key = args.semester or get_current_semester()
    sem = SEMESTER_CONFIG.get(sem_key, {})

    if not sem:
        print(f"📭 未找到学期 {sem_key} 的校历信息")
        return

    lines = [f"📅 校历 - {sem['name']}"]
    lines.append(f"  学期: {sem['start']} ~ {sem['end']} ({sem['weeks']} 周)")
    lines.append(f"  当前教学周: 第 {get_current_week()} 周")

    if sem.get("events"):
        lines.append("  📌 重要时间节点:")
        for e in sem["events"]:
            current = " ← 当前" if e["week"] == get_current_week() else ""
            lines.append(f"    第 {e['week']} 周: {e['name']}{current}")

    print("\n".join(lines))


def cmd_week(args):
    """显示当前教学周"""
    sem_key = get_current_semester()
    sem = SEMESTER_CONFIG.get(sem_key, {})
    week = get_current_week()
    weekday_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    weekday = weekday_names[datetime.now().weekday()]

    print(f"📅 今天是 {sem.get('name', '')} 第 {week} 周 {weekday}")


# ── 食堂推荐 ──────────────────────────────────────────

CANTEEN_DATA = {
    "沙河": [
        {
            "name": "一食堂",
            "floors": 3,
            "rating": 4.3,
            "detail": {
                1: ["基本伙", "御膳房烤鸭刀削面", "四季粥饼", "昌顺马记"],
                2: ["肯德基", "霸蛮米线", "小鱼大作", "西式简餐", "醉面", "武圣羊汤", "呈记烧卤", "驴肉火烧"],
                3: ["粤来越鲜", "自选菜", "瓦罐汤", "石磨肠粉"],
            },
            "features": ["烤鸭刀削面", "肯德基", "粤来越鲜", "瓦罐汤", "石磨肠粉"],
        },
        {
            "name": "二食堂",
            "floors": 4,
            "rating": 4.5,
            "detail": {
                1: ["陕西凉皮肉夹馍", "川湘木桶饭", "基本伙"],
                2: ["自选菜", "果切", "民族餐厅", "味之佳韩式炸鸡", "张亮麻辣烫", "时光卷卷寿司", "下课炸一串", "一纸鸡锡纸烤肉饭"],
                3: ["味之佳汉堡", "好伦哥", "风味小吃", "闷锅饭烤鱼饭", "滑蛋饭", "石锅拌饭", "糊涂婶老式黏糊麻辣烫"],
                4: ["川湘菜", "M小俄餐猪排饭", "炉知府炙烤五花肉", "茶瀑布"],
            },
            "features": ["韩式炸鸡", "张亮麻辣烫", "好伦哥", "石锅拌饭", "M小俄餐猪排饭", "茶瀑布"],
            "nearby": ["蜜雪冰城", "茶百道"],
        },
    ],
    "小营": [
        {"name": "一食堂", "floors": 2, "features": ["自选菜", "面食", "麻辣烫"], "rating": 4.2},
        {"name": "二食堂", "floors": 3, "features": ["自选菜", "烧烤", "奶茶", "水果"], "rating": 4.5},
        {"name": "教工食堂", "floors": 1, "features": ["小炒", "套餐"], "rating": 4.0},
    ],
}


def cmd_canteen(args):
    """食堂推荐"""
    config = load_config()
    default_campus = config.get("campus", {}).get("default_campus", "小营")
    campus = args.campus or default_campus

    canteens = CANTEEN_DATA.get(campus, [])
    if not canteens:
        print(f"📭 未找到 {campus} 校区的食堂信息")
        print(f"  可选校区: {', '.join(CANTEEN_DATA.keys())}")
        return

    lines = [f"🍽️ {campus}校区食堂推荐："]
    for c in canteens:
        stars = "⭐" * int(c["rating"])
        lines.append(f"\n  🏢 {c['name']} ({c['floors']}层) | {stars}")

        # 如果有详细楼层信息，逐层展示
        if "detail" in c:
            for floor, shops in c["detail"].items():
                lines.append(f"    {floor}F: {'、'.join(shops)}")
        elif "features" in c:
            lines.append(f"    特色: {'、'.join(c['features'])}")

        # 周边饮品
        if "nearby" in c:
            lines.append(f"    🥤 周边: {'、'.join(c['nearby'])}")

    # 随机推荐
    import random
    if canteens:
        pick = random.choice(canteens)
        # 优先从楼层详情中随机推荐
        if "detail" in pick:
            floor = random.choice(list(pick["detail"].keys()))
            shop = random.choice(pick["detail"][floor])
            print("\n".join(lines))
            print(f"\n🎲 今日推荐: {pick['name']} {floor}F 「{shop}」，去尝尝吧！")
        else:
            feat = random.choice(pick["features"]) if pick.get("features") else ""
            print("\n".join(lines))
            print(f"\n🎲 今日推荐: {pick['name']}，试试{feat}吧！")


# ── 图书馆查询 ────────────────────────────────────────

LIBRARY_DATA = {
    "小营": {
        "name": "小营校区图书馆",
        "hours": "8:00-22:00（周一至周五）/ 9:00-21:00（周末）",
        "seats": 800,
        "features": ["自习室", "电子阅览室", "研讨间"],
    },
    "清河": {
        "name": "清河校区图书馆",
        "hours": "8:00-21:30（周一至周五）/ 9:00-20:00（周末）",
        "seats": 400,
        "features": ["自习室", "电子阅览室"],
    },
}


def cmd_library(args):
    """图书馆查询"""
    if args.action == "search" and args.keyword:
        _library_search(args.keyword)
    else:
        _library_info(args.campus)


def _library_info(campus: str = ""):
    """图书馆基本信息"""
    config = load_config()
    default_campus = config.get("campus", {}).get("default_campus", "小营")
    campus = campus or default_campus

    lib = LIBRARY_DATA.get(campus)
    if not lib:
        print(f"📭 未找到 {campus} 校区的图书馆信息")
        return

    lines = [f"🏛️ {lib['name']}"]
    lines.append(f"  开馆时间: {lib['hours']}")
    lines.append(f"  座位数: {lib['seats']}")
    lines.append(f"  设施: {'、'.join(lib['features'])}")
    print("\n".join(lines))


def _library_search(keyword: str):
    """图书馆书目搜索"""
    print(f"🔍 搜索: {keyword}")
    print("⚠️ 图书馆书目搜索需要接入 OPAC 系统，暂未实现")
    print("   可访问 https://lib.bistu.edu.cn 进行在线检索")


# ── 校园邮箱 ──────────────────────────────────────────

def cmd_email(args):
    """校园邮箱"""
    import imaplib
    import email
    from email.header import decode_header

    config = load_config()
    email_config = config.get("bistu_email", {})
    addr = email_config.get("address", "")
    pwd = email_config.get("password", "")
    server = email_config.get("imap_server", "imap.bistu.edu.cn")

    if not addr or not pwd:
        print("❌ 未配置校园邮箱，请编辑 config.json 填写 bistu_email", file=sys.stderr)
        return

    if args.action == "list":
        try:
            mail = imaplib.IMAP4_SSL(server)
            mail.login(addr, pwd)
            mail.select("INBOX")

            _, msg_ids = mail.search(None, "ALL")
            ids = msg_ids[0].split()[-args.limit:]  # 最近 N 封

            lines = [f"📧 校园邮箱 ({addr})："]
            for mid in reversed(ids):
                _, msg_data = mail.fetch(mid, "(BODY[HEADER.FIELDS (SUBJECT FROM DATE)])")
                for part in msg_data:
                    if isinstance(part, tuple):
                        msg = email.message_from_bytes(part[1])
                        subject = decode_header(msg["Subject"])[0]
                        subject_text = subject[0].decode(subject[1] or "utf-8") if isinstance(subject[0], bytes) else subject[0]
                        from_addr = msg["From"]
                        date = msg["Date"]
                        lines.append(f"  • [{date}] {subject_text} — {from_addr}")

            mail.logout()
            print("\n".join(lines))
        except Exception as e:
            print(f"❌ 邮箱连接失败: {e}", file=sys.stderr)

    elif args.action == "read":
        print(f"⚠️ 邮件阅读功能开发中")


# ── 往年资源 ──────────────────────────────────────────

def cmd_past_exams(args):
    """往年试卷资源"""
    course = args.course
    print(f"📖 往年资源搜索: {course}")
    print("⚠️ 往年资源需要接入校园资源库，暂未实现")
    print("   可访问学校相关资源平台搜索")


# ── 工具类 ────────────────────────────────────────────

MIRROR_SOURCES = {
    "pip": {
        "tsinghua": "https://pypi.tuna.tsinghua.edu.cn/simple",
        "aliyun": "https://mirrors.aliyun.com/pypi/simple",
        "bistu_comment": "北信科暂无官方 pip 镜像，推荐使用清华源",
    },
    "npm": {
        "taobao": "https://registry.npmmirror.com",
        "bistu_comment": "北信科暂无官方 npm 镜像，推荐使用淘宝源",
    },
}

SOFTWARE_DATA = [
    {"name": "Microsoft Office 365", "desc": "学校提供正版 Office 套件", "url": "https://my.bistu.edu.cn/fe/"},
    {"name": "MATLAB", "desc": "学校有校园许可", "url": "https://www.mathworks.com/academia/campus.html"},
    {"name": "JetBrains IDE", "desc": "学生免费教育许可", "url": "https://www.jetbrains.com/shop/eform/students"},
    {"name": "GitHub Education", "desc": "学生开发包", "url": "https://education.github.com/"},
    {"name": "AutoCAD", "desc": "学校有校园许可", "url": ""},
]

ONLINE_TOOLS = [
    {"name": "Overleaf", "desc": "在线 LaTeX 编辑器", "url": "https://www.overleaf.com/"},
    {"name": "Draw.io", "desc": "在线流程图", "url": "https://app.diagrams.net/"},
    {"name": "Carbon", "desc": "代码截图美化", "url": "https://carbon.now.sh/"},
    {"name": "Mathpix", "desc": "数学公式 OCR", "url": "https://mathpix.com/"},
]


def cmd_mirror(args):
    """镜像换源"""
    tool = args.tool
    if tool not in MIRROR_SOURCES:
        print(f"❌ 不支持的工具: {tool}，支持: {list(MIRROR_SOURCES.keys())}")
        return

    sources = MIRROR_SOURCES[tool]
    lines = [f"🪞 {tool} 镜像源："]

    for name, url in sources.items():
        if name.endswith("_comment"):
            continue
        lines.append(f"  • {name}: {url}")

    comment = sources.get("bistu_comment", "")
    if comment:
        lines.append(f"\n  💡 {comment}")

    if tool == "pip":
        lines.append("\n  使用方法:")
        lines.append('  pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple')
    elif tool == "npm":
        lines.append("\n  使用方法:")
        lines.append('  npm config set registry https://registry.npmmirror.com')

    print("\n".join(lines))


def cmd_software(args):
    """正版软件"""
    lines = ["🖥️ 校园正版软件 / 学生免费资源："]
    for s in SOFTWARE_DATA:
        url_part = f"\n    🔗 {s['url']}" if s["url"] else ""
        lines.append(f"  • {s['name']}: {s['desc']}{url_part}")
    print("\n".join(lines))


def cmd_online_tools(args):
    """在线工具"""
    lines = ["🧰 常用在线工具："]
    for t in ONLINE_TOOLS:
        lines.append(f"  • {t['name']}: {t['desc']}")
        lines.append(f"    🔗 {t['url']}")
    print("\n".join(lines))


def main():
    parser = argparse.ArgumentParser(description="北信科校园生活")
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # 校历
    cal_parser = subparsers.add_parser("calendar", help="校历")
    cal_parser.add_argument("--semester", type=str, help="学期 (如 2025-2026-1)")

    # 教学周
    subparsers.add_parser("week", help="当前教学周")

    # 食堂
    canteen_parser = subparsers.add_parser("canteen", help="食堂推荐")
    canteen_parser.add_argument("--campus", type=str, help="校区 (小营/清河/太行路)")

    # 图书馆
    lib_parser = subparsers.add_parser("library", help="图书馆查询")
    lib_parser.add_argument("--action", type=str, default="info", choices=["info", "search"])
    lib_parser.add_argument("--keyword", type=str, help="搜索关键词")
    lib_parser.add_argument("--campus", type=str, help="校区")

    # 邮箱
    email_parser = subparsers.add_parser("email", help="校园邮箱")
    email_parser.add_argument("--action", type=str, default="list", choices=["list", "read"])
    email_parser.add_argument("--id", type=str, help="邮件 ID")
    email_parser.add_argument("--limit", type=int, default=10, help="返回条数")

    # 往年资源
    exam_parser = subparsers.add_parser("past-exams", help="往年资源")
    exam_parser.add_argument("--course", type=str, required=True, help="课程名")

    # 镜像换源
    mirror_parser = subparsers.add_parser("mirror", help="镜像换源")
    mirror_parser.add_argument("--tool", type=str, default="pip", choices=["pip", "npm"])

    # 正版软件
    subparsers.add_parser("software", help="正版软件")

    # 在线工具
    subparsers.add_parser("online-tools", help="在线工具")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    cmd_map = {
        "calendar": cmd_calendar,
        "week": cmd_week,
        "canteen": cmd_canteen,
        "library": cmd_library,
        "email": cmd_email,
        "past-exams": cmd_past_exams,
        "mirror": cmd_mirror,
        "software": cmd_software,
        "online-tools": cmd_online_tools,
    }

    handler = cmd_map.get(args.command)
    if handler:
        handler(args)


if __name__ == "__main__":
    main()
