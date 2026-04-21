#!/usr/bin/env python3
"""
超星学习通 API 客户端
支持: 课程列表、作业查询、签到查询、课程资源
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


CONFIG_PATH = Path(__file__).parent.parent / "config.json"
CHAOXING_BASE_URL = "https://mooc1-1.chaoxing.com"
CHAOXING_API_URL = "https://mooc1-api.chaoxing.com"


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        print(f"❌ 配置文件不存在: {CONFIG_PATH}", file=sys.stderr)
        sys.exit(1)
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


class ChaoxingApi:
    """超星学习通 API 客户端"""

    def __init__(self, config: Optional[dict] = None):
        self.config = config or load_config()
        self.chaoxing_config = self.config.get("chaoxing", {})
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Linux; Android 12; Pixel 6) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Mobile Safari/537.36"
            ),
        })
        self._logged_in = False

    def _ensure_login(self):
        """确保已登录学习通（使用移动端免验证码接口）"""
        if self._logged_in:
            return

        phone = self.chaoxing_config.get("phone", "")
        password = self.chaoxing_config.get("password", "")

        if not phone or not password:
            print("❌ 未配置学习通账号，请编辑 config.json 填写 chaoxing.phone 和 chaoxing.password", file=sys.stderr)
            sys.exit(1)

        # 学习通移动端登录接口（免验证码）
        login_url = "https://passport2-api.chaoxing.com/v11/loginregister"
        resp = self.session.get(login_url, params={
            "uname": phone,
            "code": password,
            "cx_xxt_passport": "json",
            "loginType": "1",
            "roleSelect": "true",
        })

        if resp.status_code != 200:
            print("❌ 学习通登录请求失败，请检查网络", file=sys.stderr)
            sys.exit(1)

        try:
            result = resp.json()
        except Exception:
            print("❌ 学习通登录响应解析失败", file=sys.stderr)
            sys.exit(1)

        if not result.get("status"):
            mes = result.get("mes", "未知错误")
            print(f"❌ 学习通登录失败: {mes}", file=sys.stderr)
            sys.exit(1)

        # 登录成功后访问 SSO 回调页面，确保 Cookie 完整
        sso_url = result.get("url", "")
        if sso_url:
            self.session.get(sso_url, allow_redirects=True)

        self._logged_in = True

    # ── 课程列表 ──────────────────────────────────────

    def get_courses(self) -> list:
        """获取当前学期课程列表"""
        self._ensure_login()
        try:
            resp = self.session.get(
                f"{CHAOXING_API_URL}/mycourse/backclazzdata",
                params={"courseType": 1, "courseFid": 0},
            )
            data = resp.json()
        except Exception:
            return [{"note": "学习通课程接口暂不可用"}]

        courses = []
        channel_list = data.get("channelList", [])
        for ch in channel_list:
            content = ch.get("content", {})
            course_data = content.get("course", {}).get("data", [])
            if not course_data:
                continue
            info = course_data[0]
            courses.append({
                "id": info.get("id", ""),
                "name": info.get("name", ""),
                "teacher": info.get("teacherfactor", ""),
                "class_id": ch.get("key", ""),
                "school": info.get("schools", ""),
                "cpi": ch.get("cpi", ""),
                "class_name": content.get("name", ""),
                "student_count": content.get("studentcount", 0),
                "is_start": content.get("isstart", False),
            })
        return courses

    def format_courses(self, courses: list) -> str:
        """格式化课程列表输出"""
        if not courses:
            return "📭 暂无学习通课程"

        if len(courses) == 1 and "note" in courses[0]:
            return f"⚠️ {courses[0]['note']}"

        lines = [f"📚 学习通课程（共 {len(courses)} 门）："]
        for c in courses:
            status = "🟢" if c.get("is_start") else "⚪"
            lines.append(
                f"  {status} {c['name']} | {c['teacher']} | {c['school']} | ID: {c['id']}"
            )
        return "\n".join(lines)

    # ── 作业/活动查询 ──────────────────────────────────────

    # 活动类型映射
    ACTIVE_TYPE_MAP = {
        1: "问卷", 2: "签到", 3: "抢答", 4: "选人",
        5: "讨论", 6: "直播", 14: "投票", 43: "投票",
        44: "资料", 45: "考试/作业",
    }

    def get_tasks(self, course_name: str = "") -> list:
        """
        获取未完成的作业/考试活动

        通过 activelist API 获取各课程的活动列表，
        筛选出未参与的作业/考试/讨论等活动。

        Args:
            course_name: 课程名称筛选
        """
        self._ensure_login()
        tasks = []

        try:
            courses_resp = self.session.get(
                f"{CHAOXING_API_URL}/mycourse/backclazzdata",
                params={"courseType": 1, "courseFid": 0},
            )
            courses_data = courses_resp.json()
        except Exception:
            return [{"note": "学习通课程接口暂不可用"}]

        channel_list = courses_data.get("channelList", [])
        for ch in channel_list:
            content = ch.get("content", {})
            course_data = content.get("course", {}).get("data", [])
            if not course_data:
                continue
            info = course_data[0]
            c_name = info.get("name", "")
            c_id = info.get("id", "")
            class_id = ch.get("key", "")

            if course_name and course_name not in c_name:
                continue

            try:
                resp = self.session.get(
                    "https://mobilelearn.chaoxing.com/v2/apis/active/student/activelist",
                    params={"fid": "1874", "courseId": c_id, "classId": class_id},
                )
                data = resp.json()
            except Exception:
                continue

            if data.get("result") != 1:
                continue

            active_list = data.get("data", {}).get("activeList", [])
            for a in active_list:
                a_type = a.get("activeType", a.get("type", 0))
                # 筛选作业/考试/讨论等（排除签到）
                if a_type == 2:
                    continue

                user_status = a.get("userStatus", 0)
                is_done = user_status == 1

                # 解析时间戳
                start_ts = a.get("startTime", 0)
                end_ts = a.get("endTime", 0)
                start_time = ""
                end_time = ""
                if start_ts:
                    try:
                        from datetime import datetime
                        start_time = datetime.fromtimestamp(int(start_ts) / 1000).strftime("%m-%d %H:%M")
                    except Exception:
                        start_time = str(start_ts)
                if end_ts:
                    try:
                        from datetime import datetime
                        end_time = datetime.fromtimestamp(int(end_ts) / 1000).strftime("%m-%d %H:%M")
                    except Exception:
                        end_time = str(end_ts)

                # 判断是否已过期
                import time
                is_expired = bool(end_ts and int(end_ts) < int(time.time() * 1000))

                task_info = {
                    "name": a.get("nameOne", ""),
                    "course": c_name,
                    "type": str(a_type),
                    "type_name": self.ACTIVE_TYPE_MAP.get(a_type, f"类型{a_type}"),
                    "status": "已完成" if is_done else ("已过期" if is_expired else "未完成"),
                    "start_time": start_time,
                    "end_time": end_time,
                    "is_done": is_done,
                    "is_expired": is_expired,
                }

                # 只保留未完成且未过期的
                if not is_done and not is_expired:
                    tasks.append(task_info)

        # 按截止时间排序
        tasks.sort(key=lambda t: t.get("end_time", ""))
        return tasks

    def format_tasks(self, tasks: list) -> str:
        """格式化作业输出"""
        if not tasks:
            return "✅ 暂无未完成的学习通作业"

        if len(tasks) == 1 and "note" in tasks[0]:
            return f"⚠️ {tasks[0]['note']}"

        lines = [f"📝 学习通未完成作业/活动（共 {len(tasks)} 项）："]
        for t in tasks:
            lines.append(
                f"  🔴 [{t['type_name']}] {t['course']} - {t['name']}"
            )
            lines.append(
                f"     截止: {t['end_time']} | {t['status']}"
            )
        return "\n".join(lines)

    # ── 签到查询 ──────────────────────────────────────

    def get_checkin(self, course_name: str = "", all_courses: bool = False) -> list:
        """
        查询待签到课程

        Args:
            course_name: 指定课程
            all_courses: 查询所有课程
        """
        self._ensure_login()
        checkins = []

        # 先获取课程列表
        try:
            courses_resp = self.session.get(
                f"{CHAOXING_API_URL}/mycourse/backclazzdata",
                params={"courseType": 1, "courseFid": 0},
            )
            courses_data = courses_resp.json()
        except Exception:
            return [{"note": "学习通课程接口暂不可用"}]

        channel_list = courses_data.get("channelList", [])
        for ch in channel_list:
            content = ch.get("content", {})
            course_data = content.get("course", {}).get("data", [])
            if not course_data:
                continue
            info = course_data[0]
            c_name = info.get("name", "")
            c_id = info.get("id", "")
            class_id = ch.get("key", "")

            if course_name and course_name not in c_name:
                continue

            try:
                resp = self.session.get(
                    "https://mobilelearn.chaoxing.com/v2/apis/active/student/activelist",
                    params={
                        "fid": "1874",
                        "courseId": c_id,
                        "classId": class_id,
                    },
                )
                data = resp.json()
            except Exception:
                continue

            if data.get("result") != 1:
                continue

            active_list = data.get("data", {}).get("activeList", [])
            for a in active_list:
                a_type = a.get("activeType", a.get("type", ""))
                # type=2 是签到
                if a_type != 2 and not all_courses:
                    continue
                checkin_info = {
                    "course": c_name,
                    "type": str(a_type),
                    "name": a.get("nameOne", ""),
                    "status": "已参与" if a.get("userStatus") == 1 else "未参与",
                    "start_time": a.get("startTime", ""),
                    "end_time": a.get("endTime", ""),
                    "group_id": a.get("groupId", ""),
                }
                if not all_courses and "已参与" in checkin_info["status"]:
                    continue
                checkins.append(checkin_info)

        return checkins

    def format_checkin(self, checkins: list) -> str:
        """格式化签到输出"""
        if not checkins:
            return "✅ 暂无待签到的课程"

        if len(checkins) == 1 and "note" in checkins[0]:
            return f"⚠️ {checkins[0]['note']}"

        lines = ["📋 学习通签到："]
        for c in checkins:
            status_icon = "🔴" if "待签" in c.get("status", "") else "🟢"
            sign_type = {
                "1": "问卷", "2": "签到", "3": "抢答",
                "4": "选人", "5": "讨论", "6": "直播",
            }.get(c.get("type", ""), f"类型{c.get('type', '?')}")
            lines.append(
                f"  {status_icon} {c['course']} | 类型: {sign_type} "
                f"| 时间: {c['start_time']}~{c['end_time']} | {c['status']}"
            )
        lines.append("\n⚠️ 签到需在手机端完成，本功能仅提供提醒")
        return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="超星学习通 API")
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # 课程列表
    subparsers.add_parser("courses", help="课程列表")

    # 作业查询
    tasks_parser = subparsers.add_parser("tasks", help="未完成作业")
    tasks_parser.add_argument("--course", type=str, default="", help="按课程名筛选")

    # 签到查询
    checkin_parser = subparsers.add_parser("checkin", help="签到查询")
    checkin_parser.add_argument("--course", type=str, default="", help="按课程名筛选")
    checkin_parser.add_argument("--all", action="store_true", help="显示所有（含已签到）")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    api = ChaoxingApi()

    if args.command == "courses":
        courses = api.get_courses()
        print(api.format_courses(courses))

    elif args.command == "tasks":
        tasks = api.get_tasks(course_name=args.course)
        print(api.format_tasks(tasks))

    elif args.command == "checkin":
        checkins = api.get_checkin(course_name=args.course, all_courses=args.all)
        print(api.format_checkin(checkins))


if __name__ == "__main__":
    main()
