#!/usr/bin/env python3
"""
GPA 计算器
支持标准 4.0 制和北信科自定义绩点算法
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


def calc_gpa_standard(score: float) -> float:
    """标准 4.0 绩点换算"""
    if score >= 90:
        return 4.0
    elif score >= 85:
        return 3.7
    elif score >= 82:
        return 3.3
    elif score >= 78:
        return 3.0
    elif score >= 75:
        return 2.7
    elif score >= 72:
        return 2.3
    elif score >= 68:
        return 2.0
    elif score >= 64:
        return 1.5
    elif score >= 60:
        return 1.0
    else:
        return 0.0


def calc_gpa_bistu(score: float) -> float:
    """
    北信科自定义绩点算法
    绩点 = (分数 - 50) / 10
    """
    if score < 60:
        return 0.0
    return min((score - 50) / 10, 4.0)


def calculate_weighted_gpa(courses: list, method: str = "bistu") -> dict:
    """
    计算加权 GPA

    Args:
        courses: 课程列表 [{"name": "", "score": 0, "credit": 0}]
        method: 计算方法 "standard" 或 "bistu"

    Returns:
        {"gpa": float, "total_credits": float, "weighted_score": float, "details": list}
    """
    calc_fn = calc_gpa_standard if method == "standard" else calc_gpa_bistu

    total_credits = 0
    total_weighted_gpa = 0
    total_weighted_score = 0
    details = []

    for c in courses:
        name = c.get("name", "未知")
        score = float(c.get("score", 0))
        credit = float(c.get("credit", 0))

        if credit <= 0:
            continue

        gp = calc_fn(score)
        total_credits += credit
        total_weighted_gpa += gp * credit
        total_weighted_score += score * credit

        details.append({
            "name": name,
            "score": score,
            "credit": credit,
            "gpa": round(gp, 2),
            "weighted": round(gp * credit, 2),
        })

    gpa = total_weighted_gpa / total_credits if total_credits > 0 else 0
    avg_score = total_weighted_score / total_credits if total_credits > 0 else 0

    return {
        "gpa": round(gpa, 2),
        "total_credits": total_credits,
        "avg_score": round(avg_score, 2),
        "details": details,
    }


def format_result(result: dict) -> str:
    """格式化 GPA 计算结果"""
    lines = ["📊 GPA 计算结果："]
    lines.append(f"  加权 GPA: {result['gpa']}")
    lines.append(f"  总学分: {result['total_credits']}")
    lines.append(f"  加权平均分: {result['avg_score']}")
    lines.append(f"\n  课程明细：")
    for d in result["details"]:
        lines.append(
            f"  • {d['name']} | 成绩: {d['score']} | 学分: {d['credit']} | "
            f"绩点: {d['gpa']} | 加权: {d['weighted']}"
        )
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="GPA 计算器")
    parser.add_argument("--method", type=str, default="bistu", choices=["standard", "bistu"],
                        help="计算方法")
    parser.add_argument("--courses", type=str, help="课程 JSON 文件路径")
    parser.add_argument("--interactive", action="store_true", help="交互式输入")

    args = parser.parse_args()

    courses = []

    if args.interactive:
        print("📝 交互式 GPA 计算（输入 q 结束）")
        while True:
            name = input("课程名称 (q 结束): ").strip()
            if name.lower() == "q":
                break
            try:
                score = float(input("成绩: ").strip())
                credit = float(input("学分: ").strip())
                courses.append({"name": name, "score": score, "credit": credit})
            except ValueError:
                print("❌ 请输入有效的数字")
                continue

    elif args.courses:
        with open(args.courses, "r", encoding="utf-8") as f:
            courses = json.load(f)
    else:
        # 示例数据
        print("⚠️ 未提供课程数据，使用示例数据")
        courses = [
            {"name": "高等数学", "score": 85, "credit": 5},
            {"name": "线性代数", "score": 78, "credit": 3},
            {"name": "大学物理", "score": 92, "credit": 4},
            {"name": "程序设计", "score": 88, "credit": 3},
            {"name": "英语", "score": 75, "credit": 2},
        ]

    result = calculate_weighted_gpa(courses, method=args.method)
    print(format_result(result))


if __name__ == "__main__":
    main()
