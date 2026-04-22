#!/usr/bin/env python3
"""
北京信息科技大学教管平台 API
基于金智教育 (正方) 微服务平台
支持: 课表查询、培养方案查询、待办查询、成绩查询、考试查询、
     空闲教室、个人信息、学籍信息、选课查询、评教查询、通知公告、学期周次
"""

import argparse
import io
import json
import re
import sys
import time
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
import warnings
warnings.filterwarnings("ignore")

sys.path.insert(0, str(Path(__file__).parent))
from bistu_sso import BISTUSSOClient, JWXT_BASE_URL, load_config


JWXT_API_BASE = f"{JWXT_BASE_URL}/jwapp/sys/homeapp/api/home"


class JWXTApi:
    """北京信息科技大学教管平台 API 客户端"""

    def __init__(self, config: Optional[dict] = None):
        self.config = config or load_config()
        self.sso_client = BISTUSSOClient(self.config)
        self.session: Optional[requests.Session] = None

    def _ensure_session(self):
        """确保有有效的 Session"""
        if self.session is None:
            self.session = self.sso_client.get_jwxt_session()

    def _api_post(self, endpoint: str, data: dict = None) -> dict:
        """发送 POST 请求到教管平台 API"""
        self._ensure_session()
        url = f"{JWXT_API_BASE}/{endpoint}"
        resp = self.session.post(url, data=data or {}, timeout=15)
        try:
            return resp.json()
        except Exception:
            return {"code": "error", "msg": f"非JSON响应: {resp.text[:100]}"}

    # ── 培养方案 ──────────────────────────────────────

    def get_educational_program(self) -> list:
        """查询培养方案/学业进度"""
        data = self._api_post("student/educational-program.do")
        if data.get("code") == "0":
            return data.get("datas", [])
        return []

    def format_educational_program(self, programs: list) -> str:
        """格式化培养方案输出"""
        if not programs:
            return "暂无培养方案数据"

        lines = ["培养方案："]
        for p in programs:
            name = p.get("planName", "未知方案")
            total = p.get("totalCredit", 0)
            gained = p.get("alreadyGainCredit", 0)
            is_major = "主修" if p.get("major") else "辅修"
            pct = (gained / total * 100) if total > 0 else 0
            bar_len = int(pct / 5)
            bar = "█" * bar_len + "░" * (20 - bar_len)
            lines.append(f"  {name} ({is_major})")
            lines.append(f"  学分: {gained}/{total} ({pct:.1f}%) [{bar}]")
        return "\n".join(lines)

    # ── 课表查询 ──────────────────────────────────────

    def get_schedule(self, xnxqdm: str = "") -> dict:
        """
        查询课程表/选课批次

        Args:
            xnxqdm: 学年学期代码，如 "2025-2026-2"
        """
        if not xnxqdm:
            # 自动推算当前学期
            now = datetime.now()
            year = now.year
            month = now.month
            if month >= 9:
                xnxqdm = f"{year}-{year + 1}-1"
            elif month >= 2:
                xnxqdm = f"{year - 1}-{year}-2"
            else:
                xnxqdm = f"{year - 1}-{year}-1"

        data = self._api_post("kb/zzypc.do", {"xnxqdm": xnxqdm})
        return {"xnxqdm": xnxqdm, "data": data}

    def format_schedule(self, result: dict) -> str:
        """格式化课表输出"""
        data = result.get("data", {})
        xnxqdm = result.get("xnxqdm", "")

        if data.get("code") != "0":
            return f"课表查询失败: {data.get('msg', '未知错误')} (学期: {xnxqdm})"

        items = data.get("datas", [])
        if not items:
            return f"学期 {xnxqdm} 暂无课表数据"

        lines = [f"课表 (学期: {xnxqdm})："]
        for item in items:
            name = item.get("itemName", "")
            code = item.get("itemCode", "")
            selected = item.get("selected", "")
            lines.append(f"  • {name} (代码: {code})" +
                        (f" [已选]" if selected else ""))
        return "\n".join(lines)

    # ── 我的待办 ──────────────────────────────────────

    def get_todo(self, user_type: str = "student") -> dict:
        """
        获取待办事项

        Args:
            user_type: 用户类型 "student" 或 "teacher"
        """
        return self._api_post("myTodo.do", {"userType": user_type})

    def format_todo(self, data: dict) -> str:
        """格式化待办输出"""
        if data.get("code") != "0":
            return f"待办查询失败: {data.get('msg', '未知错误')}"

        todo_app = data.get("datas", {}).get("todoApp", [])
        if not todo_app:
            return "暂无待办事项"

        lines = ["待办事项："]
        for item in todo_app:
            lines.append(f"  • {item}")
        return "\n".join(lines)

    # ── 待办详情 ──────────────────────────────────────

    def get_todo_details(self) -> dict:
        """获取待办详情"""
        return self._api_post("todo/generate_tododetails.do")

    def format_todo_details(self, data: dict) -> str:
        """格式化待办详情输出"""
        if data.get("code") != "0":
            return f"待办详情查询失败"

        details = data.get("datas", {}).get("generate_tododetails")
        if not details:
            return "暂无待办详情"

        return f"待办详情: {json.dumps(details, ensure_ascii=False)[:500]}"

    # ── 已完成任务 ──────────────────────────────────────

    def get_completed_tasks(self, page: int = 1, page_size: int = 10) -> dict:
        """获取已完成任务"""
        return self._api_post("todo/completedTasks.do", {
            "pageNumber": str(page),
            "pageSize": str(page_size),
        })

    # ── 开课单位 ──────────────────────────────────────

    def get_departments(self) -> list:
        """获取开课单位列表"""
        data = self._api_post("kb/kkdw.do")
        if data.get("code") == "0":
            return data.get("datas", [])
        return []

    # ── 按钮点击统计 ──────────────────────────────────────

    def button_click(self, type_code: str = "home") -> dict:
        """记录按钮点击（用于统计）"""
        return self._api_post("buttonClick.do", {"typeCode": type_code})

    # ── 登出 ──────────────────────────────────────

    def get_logout_url(self) -> str:
        """获取登出 URL"""
        data = self._api_post("logout_url.do")
        if data.get("code") == "0":
            return data.get("datas", "")
        return ""

    # ── 成绩查询 ──────────────────────────────────────

    def get_scores(self, term_code: str = "") -> list:
        """
        查询成绩

        Args:
            term_code: 学期代码，如 "2025-2026-1"，为空则查当前学期
        """
        self._ensure_session()
        if not term_code:
            term_code = self._get_current_term_code()
        data = self._api_post("student/scores.do", {"termCode": term_code})
        if data.get("code") == "0":
            return data.get("datas", [])
        return []

    def format_scores(self, scores: list, term_code: str = "") -> str:
        """格式化成绩输出"""
        if not scores:
            return f"学期 {term_code} 暂无成绩数据"
        lines = [f"📊 成绩（学期: {term_code}，共 {len(scores)} 门）："]
        for s in scores:
            status = "✅" if s.get("passStatus") else "❌"
            lines.append(
                f"  {status} {s.get('courseName', '')} | {s.get('score', '-')} | "
                f"{s.get('courseType', '')} | {s.get('credit', 0)}学分"
            )
        total_credit = sum(s.get("credit", 0) for s in scores if s.get("passStatus"))
        lines.append(f"  已通过学分: {total_credit}")
        return "\n".join(lines)

    # ── 考试查询 ──────────────────────────────────────

    def get_exams(self, term_code: str = "") -> list:
        """
        查询考试安排

        Args:
            term_code: 学期代码，如 "2025-2026-2"
        """
        self._ensure_session()
        if not term_code:
            term_code = self._get_current_term_code()
        data = self._api_post("student/exams.do", {"termCode": term_code})
        if data.get("code") == "0":
            return data.get("datas", [])
        return []

    def format_exams(self, exams: list, term_code: str = "") -> str:
        """格式化考试安排输出"""
        if not exams:
            return f"学期 {term_code} 暂无考试安排"
        lines = [f"📋 考试安排（学期: {term_code}）："]
        for e in exams:
            exam_status_map = {1: "未开始", 2: "进行中", 3: "已结束"}
            status = exam_status_map.get(e.get("examStatus", 0), "未知")
            lines.append(
                f"  📌 {e.get('courseName', '')} | {e.get('examType', '')} | {status}"
            )
            lines.append(
                f"     时间: {e.get('examTimeDescription', '')} | 地点: {e.get('examPlace', '')} | 座位: {e.get('examSeatNo', '')}"
            )
        return "\n".join(lines)

    # ── 课程信息 ──────────────────────────────────────

    def get_courses_info(self, term_code: str = "") -> list:
        """
        查询课程信息（含上课地点）

        Args:
            term_code: 学期代码
        """
        self._ensure_session()
        if not term_code:
            term_code = self._get_current_term_code()
        data = self._api_post("student/courses.do", {"termCode": term_code})
        if data.get("code") == "0":
            return data.get("datas", [])
        return []

    # ── 课表详情 ──────────────────────────────────────

    def get_schedule_detail(self, term_code: str = "") -> dict:
        """
        获取课表详情（含教室信息）

        Args:
            term_code: 学期代码
        """
        self._ensure_session()
        if not term_code:
            term_code = self._get_current_term_code()
        data = self._api_post("student/getMyScheduleDetail.do", {"termCode": term_code})
        if data.get("code") == "0":
            return data.get("datas", {})
        return {}

    # ── 空闲教室查询 ──────────────────────────────────────

    def get_empty_classrooms(self, term_code: str = "",
                              campus_id: str = "",
                              week: int = 0,
                              weekday: int = 0,
                              section: int = 0) -> dict:
        """
        查询空闲教室

        基于课表数据推断空闲教室：
        1. 获取所有已排课的课程及其教室
        2. 按周次/星期/节次筛选已占用的教室
        3. 计算空闲教室

        Args:
            term_code: 学期代码
            campus_id: 校区ID（"10"=沙河校区）
            week: 周次（1-20），0=当前周
            weekday: 星期几（1=周一，7=周日），0=今天
            section: 第几节（1-13），0=全天
        """
        self._ensure_session()
        if not term_code:
            term_code = self._get_current_term_code()

        # 获取当前周次
        if week == 0:
            week_info = self._get_current_week()
            week = week_info.get("week", 1)
        if weekday == 0:
            weekday = datetime.now().isoweekday()  # 1=周一

        # 获取课表详情
        schedule_data = self.get_schedule_detail(term_code)
        arranged_list = schedule_data.get("arrangedList", [])

        # 获取课程信息（含完整教室地点）
        courses_info = self.get_courses_info(term_code)

        # 从课程信息提取所有教室
        all_rooms = {}  # room_code -> room_info
        for c in courses_info:
            place_str = c.get("classDateAndPlace", "") or ""
            # 格式: "1-9周[讲授]/星期一/第8节-第9节/刘旭红[主讲]/XXB-301"
            room_matches = re.findall(r'([A-Z\u4e00-\u9fff]{2,4}[-]\d{2,4})', place_str)
            for rm in room_matches:
                if rm not in all_rooms:
                    # 推断校区
                    campus = "沙河"
                    if rm.startswith("WLA") or rm.startswith("WLB") or rm.startswith("WLC"):
                        campus = "小营"
                    elif rm.startswith("XX"):
                        campus = "小营"
                    all_rooms[rm] = {"code": rm, "campus": campus}

        # 从课表详情提取教室
        for item in arranged_list:
            for cell in item.get("cellDetail", []):
                text = cell.get("text", "")
                m = re.search(r'[A-Z\u4e00-\u9fff]{2,4}[-]\d{2,4}', text)
                if m:
                    rm = m.group()
                    if rm not in all_rooms:
                        campus = "沙河"
                        if rm.startswith("WLA") or rm.startswith("WLB") or rm.startswith("WLC"):
                            campus = "小营"
                        elif rm.startswith("XX"):
                            campus = "小营"
                        all_rooms[rm] = {"code": rm, "campus": campus}

        # 标记已占用的教室
        occupied = {}  # (room_code, section_range) -> course_info
        for item in arranged_list:
            week_str = item.get("week", "")
            begin_sec = item.get("beginSection", 0)
            end_sec = item.get("endSection", 0)
            course_name = item.get("courseName", "")
            begin_time = item.get("beginTime", "")

            # 判断该课程在指定周次是否有课
            has_class = self._week_matches(week_str, week)
            if not has_class:
                continue

            # 提取教室
            room_code = ""
            for cell in item.get("cellDetail", []):
                text = cell.get("text", "")
                m = re.search(r'[A-Z\u4e00-\u9fff]{2,4}[-]\d{2,4}', text)
                if m:
                    room_code = m.group()
                    break

            if not room_code:
                continue

            for sec in range(begin_sec, end_sec + 1):
                key = (room_code, sec)
                if key not in occupied:
                    occupied[key] = {
                        "course": course_name,
                        "begin_section": begin_sec,
                        "end_section": end_sec,
                        "time": begin_time,
                    }

        # 生成空闲教室报告
        sections = list(range(1, 14))  # 第1-13节
        if section > 0:
            sections = [section]

        free_rooms = {}
        for room_code, room_info in all_rooms.items():
            if campus_id and room_info["campus"] != campus_id:
                # 简化校区匹配
                if campus_id == "10" and room_info["campus"] != "沙河":
                    continue
                if campus_id == "小营" and room_info["campus"] != "小营":
                    continue

            free_sections = []
            for sec in sections:
                if (room_code, sec) not in occupied:
                    free_sections.append(sec)

            if free_sections:
                free_rooms[room_code] = {
                    "code": room_code,
                    "campus": room_info["campus"],
                    "free_sections": free_sections,
                }

        weekday_names = ["", "周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        return {
            "term_code": term_code,
            "week": week,
            "weekday": weekday,
            "weekday_name": weekday_names[weekday] if 1 <= weekday <= 7 else "",
            "section": section,
            "all_rooms_count": len(all_rooms),
            "free_rooms": free_rooms,
        }

    def format_empty_classrooms(self, result: dict) -> str:
        """格式化空闲教室输出"""
        if not result.get("free_rooms"):
            return f"第{result.get('week', '?')}周 {result.get('weekday_name', '')} 暂无空闲教室数据"

        weekday_name = result.get("weekday_name", "")
        week = result.get("week", "?")
        section = result.get("section", 0)
        section_desc = f"第{section}节" if section > 0 else "全天"

        free_rooms = result["free_rooms"]

        # 按校区分组
        by_campus = {}
        for rm in free_rooms.values():
            campus = rm["campus"]
            if campus not in by_campus:
                by_campus[campus] = []
            by_campus[campus].append(rm)

        lines = [f"🏫 空闲教室 | 第{week}周 {weekday_name} {section_desc}"]

        section_ranges = {
            "上午 (1-4节)": lambda secs: [s for s in secs if 1 <= s <= 4],
            "下午 (5-9节)": lambda secs: [s for s in secs if 5 <= s <= 9],
            "晚上 (10-13节)": lambda secs: [s for s in secs if 10 <= s <= 13],
        }

        for campus, rooms in by_campus.items():
            lines.append(f"\n  📍 {campus}校区:")
            for rm in sorted(rooms, key=lambda x: x["code"]):
                secs = rm["free_sections"]
                time_parts = []
                for label, filt in section_ranges.items():
                    filtered = filt(secs)
                    if filtered:
                        if section == 0:
                            time_parts.append(f"{label}: 第{filtered[0]}-{filtered[-1]}节")
                        else:
                            time_parts.append(f"第{section}节空闲")
                if time_parts:
                    lines.append(f"    {rm['code']}  {' | '.join(time_parts)}")

        lines.append(f"\n  共 {len(free_rooms)} 个教室有空闲时段")
        return "\n".join(lines)

    # ── 辅助方法 ──────────────────────────────────────

    # ── 个人信息 ──────────────────────────────────────

    def get_student_info(self) -> dict:
        """查询学生个人基本信息"""
        data = self._api_post("student/studentInfo.do")
        if data.get("code") == "0":
            return data.get("datas", {})
        return {}

    def format_student_info(self, info: dict) -> str:
        """格式化个人信息输出"""
        if not info:
            return "暂无个人信息数据"

        lines = ["👤 学生个人信息："]
        field_map = {
            "studentName": "姓名",
            "studentCode": "学号",
            "gender": "性别",
            "grade": "年级",
            "collegeName": "学院",
            "majorName": "专业",
            "className": "班级",
            "studentType": "学生类型",
            "educationLevel": "学历层次",
            "campusName": "校区",
            "phone": "联系电话",
            "email": "邮箱",
        }
        for key, label in field_map.items():
            val = info.get(key, "")
            if val:
                lines.append(f"  {label}: {val}")

        # 如果上面的字段没有命中，展示所有非空字段
        if len(lines) <= 2:
            for key, val in info.items():
                if val and key not in field_map:
                    lines.append(f"  {key}: {val}")

        return "\n".join(lines)

    # ── 学籍信息 ──────────────────────────────────────

    def get_student_status(self) -> dict:
        """查询学籍信息（更详细的学籍状态）"""
        data = self._api_post("student/studentStatus.do")
        if data.get("code") == "0":
            return data.get("datas", {})
        return {}

    def format_student_status(self, info: dict) -> str:
        """格式化学籍信息输出"""
        if not info:
            return "暂无学籍信息数据"

        lines = ["📋 学籍信息："]
        field_map = {
            "studentName": "姓名",
            "studentCode": "学号",
            "gender": "性别",
            "status": "学籍状态",
            "registerStatus": "注册状态",
            "grade": "年级",
            "collegeName": "学院",
            "majorName": "专业",
            "className": "班级",
            "educationLevel": "学历层次",
            "studyDuration": "学制",
            "admissionDate": "入学日期",
            "expectedGraduationDate": "预计毕业日期",
        }
        for key, label in field_map.items():
            val = info.get(key, "")
            if val:
                lines.append(f"  {label}: {val}")

        if len(lines) <= 2:
            for key, val in info.items():
                if val and key not in field_map:
                    lines.append(f"  {key}: {val}")

        return "\n".join(lines)

    # ── 选课查询 ──────────────────────────────────────

    def get_selected_courses(self, term_code: str = "") -> list:
        """
        查询已选课程

        Args:
            term_code: 学期代码，如 "2025-2026-2"
        """
        self._ensure_session()
        if not term_code:
            term_code = self._get_current_term_code()
        data = self._api_post("student/selectedCourses.do", {"termCode": term_code})
        if data.get("code") == "0":
            return data.get("datas", [])
        return []

    def format_selected_courses(self, courses: list, term_code: str = "") -> str:
        """格式化已选课程输出"""
        if not courses:
            return f"学期 {term_code} 暂无已选课程数据"

        lines = [f"📚 已选课程（学期: {term_code}，共 {len(courses)} 门）："]
        for c in courses:
            name = c.get("courseName", "")
            teacher = c.get("teacherName", "")
            credit = c.get("credit", 0)
            course_type = c.get("courseType", "")
            lines.append(f"  • {name} | {teacher} | {credit}学分 | {course_type}")
        return "\n".join(lines)

    # ── 选课批次 ──────────────────────────────────────

    def get_course_selection_batches(self, term_code: str = "") -> list:
        """
        查询选课批次

        Args:
            term_code: 学期代码
        """
        self._ensure_session()
        if not term_code:
            term_code = self._get_current_term_code()
        data = self._api_post("student/courseSelectionBatches.do", {"termCode": term_code})
        if data.get("code") == "0":
            return data.get("datas", [])
        return []

    def format_course_selection_batches(self, batches: list, term_code: str = "") -> str:
        """格式化选课批次输出"""
        if not batches:
            return f"学期 {term_code} 暂无选课批次"

        lines = [f"🗳️ 选课批次（学期: {term_code}）："]
        for b in batches:
            name = b.get("batchName", "")
            status = "🟢 进行中" if b.get("isActive") else "🔴 已结束"
            start = b.get("startTime", "")
            end = b.get("endTime", "")
            lines.append(f"  {status} {name} | {start} ~ {end}")
        return "\n".join(lines)

    # ── 评教查询 ──────────────────────────────────────

    def get_evaluation_status(self, term_code: str = "") -> dict:
        """
        查询评教状态

        Args:
            term_code: 学期代码
        """
        self._ensure_session()
        if not term_code:
            term_code = self._get_current_term_code()
        data = self._api_post("student/evaluationStatus.do", {"termCode": term_code})
        if data.get("code") == "0":
            return data.get("datas", {})
        return {}

    def format_evaluation_status(self, data: dict, term_code: str = "") -> str:
        """格式化评教状态输出"""
        if not data:
            return f"学期 {term_code} 暂无评教数据"

        evaluated = data.get("evaluatedCount", 0)
        total = data.get("totalCount", 0)
        unevaluated = total - evaluated

        lines = [f"📝 评教状态（学期: {term_code}）："]
        lines.append(f"  已评教: {evaluated}/{total}")
        if unevaluated > 0:
            lines.append(f"  ⚠️ 未评教: {unevaluated} 门")

        # 显示未评教课程列表
        uneval_list = data.get("unevaluatedCourses", [])
        if uneval_list:
            lines.append("  未评教课程：")
            for c in uneval_list:
                lines.append(f"    • {c.get('courseName', '')} | {c.get('teacherName', '')}")

        return "\n".join(lines)

    # ── 通知公告 ──────────────────────────────────────

    def get_notices(self, page: int = 1, page_size: int = 10) -> dict:
        """
        获取教务通知公告

        Args:
            page: 页码
            page_size: 每页条数
        """
        data = self._api_post("notice/notices.do", {
            "pageNumber": str(page),
            "pageSize": str(page_size),
        })
        if data.get("code") == "0":
            return data.get("datas", {})
        return {}

    def format_notices(self, data: dict) -> str:
        """格式化通知公告输出"""
        if not data:
            return "暂无通知公告"

        notices = data.get("rows", data.get("notices", []))
        if not notices:
            return "暂无通知公告"

        lines = ["📢 教务通知公告："]
        for n in notices[:10]:
            title = n.get("title", n.get("noticeTitle", ""))
            date = n.get("publishDate", n.get("createTime", ""))
            dept = n.get("departmentName", n.get("publisherName", ""))
            lines.append(f"  • [{date}] {title}")
            if dept:
                lines[-1] += f" — {dept}"

        total = data.get("total", len(notices))
        if total > 10:
            lines.append(f"  ... 共 {total} 条通知")
        return "\n".join(lines)

    # ── 学期周次 ──────────────────────────────────────

    def get_term_weeks(self, term_code: str = "") -> list:
        """
        获取学期周次信息

        Args:
            term_code: 学期代码
        """
        self._ensure_session()
        if not term_code:
            term_code = self._get_current_term_code()
        data = self._api_post("getTermWeeks.do", {"termCode": term_code})
        if data.get("code") == "0":
            return data.get("datas", [])
        return []

    def format_term_weeks(self, weeks: list, term_code: str = "") -> str:
        """格式化学期周次输出"""
        if not weeks:
            return f"学期 {term_code} 暂无周次数据"

        lines = [f"📅 学期周次（学期: {term_code}）："]
        for w in weeks:
            serial = w.get("serialNumber", "")
            start = w.get("startDate", "")
            end = w.get("endDate", "")
            is_current = " ◀ 当前周" if w.get("curWeek") else ""
            lines.append(f"  第{serial}周: {start} ~ {end}{is_current}")
        return "\n".join(lines)

    # ── 学业情况 ──────────────────────────────────────

    def get_academic_summary(self) -> dict:
        """查询学业情况汇总"""
        data = self._api_post("student/academicSummary.do")
        if data.get("code") == "0":
            return data.get("datas", {})
        return {}

    def format_academic_summary(self, data: dict) -> str:
        """格式化学业情况输出"""
        if not data:
            return "暂无学业情况数据"

        lines = ["📊 学业情况汇总："]
        field_map = {
            "totalCredit": "总学分要求",
            "gainedCredit": "已获学分",
            "gpa": "GPA",
            "rank": "年级排名",
            "totalStudents": "年级人数",
            "passedCourses": "已通过课程",
            "failedCourses": "未通过课程",
        }
        for key, label in field_map.items():
            val = data.get(key, "")
            if val:
                lines.append(f"  {label}: {val}")

        if len(lines) <= 2:
            for key, val in data.items():
                if val and key not in field_map:
                    lines.append(f"  {key}: {val}")

        return "\n".join(lines)

    # ── 教室查询 ──────────────────────────────────────

    def get_classroom_list(self, campus: str = "") -> list:
        """
        查询教室列表

        Args:
            campus: 校区筛选
        """
        params = {}
        if campus:
            params["campus"] = campus
        data = self._api_post("classroom/classroomList.do", params)
        if data.get("code") == "0":
            return data.get("datas", [])
        return []

    def format_classroom_list(self, rooms: list) -> str:
        """格式化教室列表输出"""
        if not rooms:
            return "暂无教室数据"

        lines = [f"🏫 教室列表（共 {len(rooms)} 个）："]
        by_campus = {}
        for r in rooms:
            campus = r.get("campusName", r.get("campus", "未知"))
            if campus not in by_campus:
                by_campus[campus] = []
            by_campus[campus].append(r)

        for campus, campus_rooms in by_campus.items():
            lines.append(f"\n  📍 {campus}：")
            for r in campus_rooms[:20]:
                name = r.get("roomName", r.get("classroomName", ""))
                capacity = r.get("capacity", r.get("seatCount", ""))
                cap_str = f" ({capacity}人)" if capacity else ""
                lines.append(f"    • {name}{cap_str}")
            if len(campus_rooms) > 20:
                lines.append(f"    ... 共 {len(campus_rooms)} 个教室")

        return "\n".join(lines)

    # ── 补考查询 ──────────────────────────────────────

    def get_retake_exams(self, term_code: str = "") -> list:
        """
        查询补考安排

        Args:
            term_code: 学期代码
        """
        self._ensure_session()
        if not term_code:
            term_code = self._get_current_term_code()
        data = self._api_post("student/retakeExams.do", {"termCode": term_code})
        if data.get("code") == "0":
            return data.get("datas", [])
        return []

    def format_retake_exams(self, exams: list, term_code: str = "") -> str:
        """格式化补考安排输出"""
        if not exams:
            return f"学期 {term_code} 暂无补考安排"

        lines = [f"🔄 补考安排（学期: {term_code}）："]
        for e in exams:
            lines.append(
                f"  • {e.get('courseName', '')} | {e.get('examTime', '')} | {e.get('examPlace', '')}"
            )
        return "\n".join(lines)

    # ── 成绩详情（所有学期） ──────────────────────────

    def get_all_scores(self) -> list:
        """查询所有学期成绩"""
        data = self._api_post("student/allScores.do")
        if data.get("code") == "0":
            return data.get("datas", [])
        return []

    def format_all_scores(self, scores: list) -> str:
        """格式化所有学期成绩输出"""
        if not scores:
            return "暂无成绩数据"

        # 按学期分组
        by_term = {}
        for s in scores:
            term = s.get("termCode", s.get("termName", "未知学期"))
            if term not in by_term:
                by_term[term] = []
            by_term[term].append(s)

        lines = ["📊 全部成绩："]
        for term, term_scores in by_term.items():
            passed = sum(1 for s in term_scores if s.get("passStatus"))
            total_credit = sum(s.get("credit", 0) for s in term_scores if s.get("passStatus"))
            lines.append(f"\n  📅 {term} ({passed}/{len(term_scores)} 门通过, {total_credit} 学分)：")
            for s in term_scores:
                status = "✅" if s.get("passStatus") else "❌"
                lines.append(
                    f"    {status} {s.get('courseName', '')} | {s.get('score', '-')} | "
                    f"{s.get('courseType', '')} | {s.get('credit', 0)}学分"
                )

        # 总计
        total_credit = sum(s.get("credit", 0) for s in scores if s.get("passStatus"))
        total_passed = sum(1 for s in scores if s.get("passStatus"))
        lines.append(f"\n  总计: {total_passed}/{len(scores)} 门通过, {total_credit} 学分")
        return "\n".join(lines)

    # ── 原辅助方法 ──────────────────────────────────────

    def _get_current_term_code(self) -> str:
        """自动推算当前学期代码"""
        now = datetime.now()
        year = now.year
        month = now.month
        if month >= 9:
            return f"{year}-{year + 1}-1"
        elif month >= 2:
            return f"{year - 1}-{year}-2"
        else:
            return f"{year - 1}-{year}-1"

    def _get_current_week(self) -> dict:
        """获取当前周次"""
        self._ensure_session()
        term_code = self._get_current_term_code()
        data = self._api_post("getTermWeeks.do", {"termCode": term_code})
        if data.get("code") == "0":
            weeks = data.get("datas", [])
            for i, w in enumerate(weeks):
                if w.get("curWeek"):
                    return {"week": w.get("serialNumber", i + 1), "term_code": term_code}
            # 默认返回第7周（大概中期）
            return {"week": 7, "term_code": term_code}
        return {"week": 7, "term_code": term_code}

    @staticmethod
    def _week_matches(week_str: str, target_week: int) -> bool:
        """
        判断目标周次是否在周次字符串中
        week_str 格式如: "111111111111111" (每bit表示一周)
        或者 "1-15" 这样的范围
        """
        if not week_str:
            return False

        # 二进制格式: 111111111111111
        if all(c in "01" for c in week_str):
            if target_week <= len(week_str):
                return week_str[target_week - 1] == "1"
            return False

        # 范围格式: "1-15" 或 "1-9,11-15"
        try:
            parts = week_str.split(",")
            for part in parts:
                part = part.strip()
                if "-" in part:
                    start, end = part.split("-")
                    if int(start.strip()) <= target_week <= int(end.strip()):
                        return True
                elif part.strip().isdigit():
                    if int(part.strip()) == target_week:
                        return True
        except (ValueError, IndexError):
            pass

        return False


def main():
    parser = argparse.ArgumentParser(description="北信科教管平台 API")
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # 课表
    schedule_parser = subparsers.add_parser("schedule", help="查询课表/选课批次")
    schedule_parser.add_argument("--xnxqdm", type=str, default="", help="学年学期代码 (如 2025-2026-2)")

    # 培养方案
    program_parser = subparsers.add_parser("program", help="查询培养方案/学业进度")

    # 待办
    todo_parser = subparsers.add_parser("todo", help="查询待办事项")
    todo_parser.add_argument("--type", type=str, default="student", help="用户类型 (student/teacher)")

    # 待办详情
    subparsers.add_parser("todo-details", help="查询待办详情")

    # 开课单位
    subparsers.add_parser("departments", help="查询开课单位")

    # 成绩
    scores_parser = subparsers.add_parser("scores", help="查询成绩")
    scores_parser.add_argument("--term", type=str, default="", help="学期代码 (如 2025-2026-1)")

    # 全部成绩
    subparsers.add_parser("all-scores", help="查询所有学期成绩")

    # 考试
    exams_parser = subparsers.add_parser("exams", help="查询考试安排")
    exams_parser.add_argument("--term", type=str, default="", help="学期代码 (如 2025-2026-2)")

    # 补考
    retake_parser = subparsers.add_parser("retake-exams", help="查询补考安排")
    retake_parser.add_argument("--term", type=str, default="", help="学期代码")

    # 空闲教室
    room_parser = subparsers.add_parser("rooms", help="查询空闲教室")
    room_parser.add_argument("--term", type=str, default="", help="学期代码")
    room_parser.add_argument("--campus", type=str, default="", help="校区 (沙河/小营)")
    room_parser.add_argument("--week", type=int, default=0, help="周次 (0=当前周)")
    room_parser.add_argument("--weekday", type=int, default=0, help="星期几 (1=周一, 0=今天)")
    room_parser.add_argument("--section", type=int, default=0, help="第几节 (0=全天)")

    # 个人信息
    subparsers.add_parser("info", help="查询学生个人信息")

    # 学籍信息
    subparsers.add_parser("status", help="查询学籍信息")

    # 已选课程
    selected_parser = subparsers.add_parser("selected-courses", help="查询已选课程")
    selected_parser.add_argument("--term", type=str, default="", help="学期代码")

    # 选课批次
    batch_parser = subparsers.add_parser("selection-batches", help="查询选课批次")
    batch_parser.add_argument("--term", type=str, default="", help="学期代码")

    # 评教状态
    eval_parser = subparsers.add_parser("evaluation", help="查询评教状态")
    eval_parser.add_argument("--term", type=str, default="", help="学期代码")

    # 通知公告
    notice_parser = subparsers.add_parser("notices", help="查询教务通知公告")
    notice_parser.add_argument("--page", type=int, default=1, help="页码")
    notice_parser.add_argument("--size", type=int, default=10, help="每页条数")

    # 学期周次
    weeks_parser = subparsers.add_parser("term-weeks", help="查询学期周次")
    weeks_parser.add_argument("--term", type=str, default="", help="学期代码")

    # 学业情况
    subparsers.add_parser("academic-summary", help="查询学业情况汇总")

    # 教室列表
    classroom_parser = subparsers.add_parser("classrooms", help="查询教室列表")
    classroom_parser.add_argument("--campus", type=str, default="", help="校区筛选")

    # 登出
    subparsers.add_parser("logout", help="获取登出URL")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    api = JWXTApi()

    if args.command == "schedule":
        result = api.get_schedule(xnxqdm=args.xnxqdm)
        print(api.format_schedule(result))

    elif args.command == "program":
        programs = api.get_educational_program()
        print(api.format_educational_program(programs))

    elif args.command == "todo":
        data = api.get_todo(user_type=args.type)
        print(api.format_todo(data))

    elif args.command == "todo-details":
        data = api.get_todo_details()
        print(api.format_todo_details(data))

    elif args.command == "departments":
        depts = api.get_departments()
        if depts:
            print("开课单位：")
            for d in depts:
                print(f"  • {d}")
        else:
            print("暂无开课单位数据")

    elif args.command == "scores":
        term = args.term or api._get_current_term_code()
        scores = api.get_scores(term_code=term)
        print(api.format_scores(scores, term))

    elif args.command == "all-scores":
        scores = api.get_all_scores()
        print(api.format_all_scores(scores))

    elif args.command == "exams":
        term = args.term or api._get_current_term_code()
        exams = api.get_exams(term_code=term)
        print(api.format_exams(exams, term))

    elif args.command == "retake-exams":
        term = args.term or api._get_current_term_code()
        exams = api.get_retake_exams(term_code=term)
        print(api.format_retake_exams(exams, term))

    elif args.command == "rooms":
        campus_map = {"沙河": "10", "小营": "小营"}
        campus_id = campus_map.get(args.campus, args.campus)
        result = api.get_empty_classrooms(
            term_code=args.term,
            campus_id=campus_id,
            week=args.week,
            weekday=args.weekday,
            section=args.section,
        )
        print(api.format_empty_classrooms(result))

    elif args.command == "info":
        info = api.get_student_info()
        print(api.format_student_info(info))

    elif args.command == "status":
        info = api.get_student_status()
        print(api.format_student_status(info))

    elif args.command == "selected-courses":
        term = args.term or api._get_current_term_code()
        courses = api.get_selected_courses(term_code=term)
        print(api.format_selected_courses(courses, term))

    elif args.command == "selection-batches":
        term = args.term or api._get_current_term_code()
        batches = api.get_course_selection_batches(term_code=term)
        print(api.format_course_selection_batches(batches, term))

    elif args.command == "evaluation":
        term = args.term or api._get_current_term_code()
        data = api.get_evaluation_status(term_code=term)
        print(api.format_evaluation_status(data, term))

    elif args.command == "notices":
        data = api.get_notices(page=args.page, page_size=args.size)
        print(api.format_notices(data))

    elif args.command == "term-weeks":
        term = args.term or api._get_current_term_code()
        weeks = api.get_term_weeks(term_code=term)
        print(api.format_term_weeks(weeks, term))

    elif args.command == "academic-summary":
        data = api.get_academic_summary()
        print(api.format_academic_summary(data))

    elif args.command == "classrooms":
        rooms = api.get_classroom_list(campus=args.campus)
        print(api.format_classroom_list(rooms))

    elif args.command == "logout":
        url = api.get_logout_url()
        print(f"登出URL: {url}")


if __name__ == "__main__":
    main()
