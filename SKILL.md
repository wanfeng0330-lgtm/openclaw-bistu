---
name: bistu-campus
version: 2.0.0
license: MIT
description: |
  北京信息科技大学全能校园助手。覆盖教务管理、一网通办、学习通、校园生活等 21 项功能，专为北信科学子打造。
  触发场景:
  (1) 用户询问课程表、本周课程安排
  (2) 用户查询培养方案、学业进度
  (3) 用户查看待办事项、DDL
  (4) 用户查询成绩、考试安排
  (5) 用户查询空闲教室、自习室
  (6) 用户询问选课建议、课程评价
  (7) 用户查询校历、教学周、放假安排
  (8) 用户需要办理校园事务、查询一网通办
  (9) 用户查看学习通课程、作业、签到
  (10) 用户需要生成北信科 PPT
  (11) 用户查询食堂、校园生活信息
  (12) 用户需要换源、正版软件、在线工具
  触发词: 课表, 课程, 成绩, GPA, 待办, DDL, 作业, 选课, 校历, 教学周, 一网通办, 办事, 学习通, 签到, PPT, 食堂, 图书馆, 空闲教室, 自习, 考试, chaoxing
---

# BISTU Campus — 北京信息科技大学全能校园助手

## 刚需功能（每周都用）

### 1. 课表查询
**触发**: "课表"、"课程安排"、"这学期有什么课"
```bash
python3 scripts/jwxt_api.py schedule [--xnxqdm 2025-2026-2]
```
默认自动推算当前学期。`--xnxqdm` 可指定学年学期代码（如 `2025-2026-2`）。

### 2. 培养方案 + 学业进度
**触发**: "培养方案"、"学分"、"还差多少学分"、"学业进度"
```bash
python3 scripts/jwxt_api.py program
```
展示当前培养方案的总学分、已获学分、完成百分比。

### 3. 成绩查询
**触发**: "成绩"、"查分"、"这学期考了多少"
```bash
python3 scripts/jwxt_api.py scores [--term 2025-2026-1]
```
查询指定学期的成绩，包含课程名、分数、课程类型、学分、是否通过。默认查询当前学期。

### 4. 考试安排
**触发**: "考试"、"什么时候考试"、"考试安排"
```bash
python3 scripts/jwxt_api.py exams [--term 2025-2026-2]
```
查询考试时间、地点、座位号、考试状态。

### 5. 学习通课程管理
**触发**: "学习通"、"超星"、"chaoxing"、"学习通作业"
```bash
python3 scripts/chaoxing_api.py courses
python3 scripts/chaoxing_api.py tasks [--course COURSE_NAME]
python3 scripts/chaoxing_api.py checkin [--course COURSE_NAME]
```
- `courses`: 列出所有学习通课程
- `tasks`: 查看未完成作业/活动（通过 activelist API，筛选未参与且未过期的活动）
- `checkin`: 查看待签到课程（需在手机端完成签到）

### 6. 待办事项
**触发**: "待办"、"DDL"、"作业截止"、"还有什么没做"
```bash
python3 scripts/jwxt_api.py todo [--type student]
python3 scripts/jwxt_api.py todo-details
```
聚合教务平台待办事项。

---

## 高频功能（每月多次）

### 7. 空闲教室查询
**触发**: "空闲教室"、"自习室"、"哪里可以自习"
```bash
python3 scripts/jwxt_api.py rooms [--campus 小营] [--week 8] [--weekday 2] [--section 3]
```
- 基于课表数据推断空闲教室
- `--campus`: 校区筛选（沙河/小营）
- `--week`: 周次（0=当前周）
- `--weekday`: 星期几（1=周一，0=今天）
- `--section`: 第几节（0=全天）
- 按上午/下午/晚上分段显示空闲时段

### 8. 校历 + 教学周
**触发**: "校历"、"第几周"、"什么时候放假"、"考试周"
```bash
python3 scripts/campus_life.py calendar
python3 scripts/campus_life.py week
```
自动计算当前教学周，展示学期重要时间节点。

### 9. 一网通办
**触发**: "一网通办"、"办事"、"怎么办"、"服务"
```bash
python3 scripts/ywtb_api.py info
python3 scripts/ywtb_api.py apps
python3 scripts/ywtb_api.py services
python3 scripts/ywtb_api.py search KEYWORD
```
- `info`: 站点信息
- `apps`: 应用列表
- `services`: 服务分类
- `search`: 搜索服务/应用

### 10. 开课单位查询
**触发**: "开课单位"、"哪个学院开的课"
```bash
python3 scripts/jwxt_api.py departments
```

---

## 实用功能（需要时用）

### 11. 北信科 PPT 一键生成
**触发**: "做PPT"、"PPT模板"、"生成PPT"
```bash
python3 scripts/generate_ppt.py --list-templates
python3 scripts/generate_ppt.py \
  --title "标题" \
  --markdown content.md \
  --template "PPT-浅蓝色.pptx" \
  --output output.pptx
```
模板目录: `templates/`，内置浅蓝色主题模板

### 12. GPA 计算
**触发**: "GPA"、"绩点"、"算GPA"
```bash
python3 scripts/gpa_calculator.py
```
支持标准 4.0 制和北信科自定义算法（绩点 = (分数-50)/10）。

### 13. 食堂推荐
**触发**: "吃什么"、"食堂"、"美食"
```bash
python3 scripts/campus_life.py canteen [--campus CAMPUS]
```
`--campus` 可选: 小营/清河/太行路。

### 14. 图书馆查询
**触发**: "图书馆"、"借书"、"开馆时间"
```bash
python3 scripts/campus_life.py library [--action info/search] [--keyword KEYWORD]
```

### 15. 学习通签到助手
**触发**: "签到"、"打卡"、"sign"
```bash
python3 scripts/chaoxing_api.py checkin --all
```
签到功能仅提供提醒和状态查询，实际签到需在手机端完成。

### 16. 校园邮箱
**触发**: "邮件"、"邮箱"、"有没有新邮件"
```bash
python3 scripts/campus_life.py email [--action list] [--limit 10]
```
通过 IMAP 协议读取校园邮箱。

---

## 工具功能（辅助工具）

### 17. 镜像换源
**触发**: "换源"、"pip源"、"清华源"
```bash
python3 scripts/campus_life.py mirror --tool pip/npm
```

### 18. 正版软件
**触发**: "正版软件"、"免费软件"、"Office"
```bash
python3 scripts/campus_life.py software
```

### 19. 在线工具
**触发**: "在线工具"、"LaTeX"、"工具"
```bash
python3 scripts/campus_life.py online-tools
```

### 20. 校园邮箱
**触发**: "邮件"、"收邮件"
```bash
python3 scripts/campus_life.py email --action list --limit 10
```

### 21. 往年资源
**触发**: "往年题"、"试卷"、"题库"
```bash
python3 scripts/campus_life.py past-exams --course 高等数学
```
功能开发中，推荐访问学校资源平台。

---

## 配置

配置文件: `config.json`（从 `config.example.json` 复制并填入凭证）

**统一身份认证 (SSO)**: https://wxjw.bistu.edu.cn/authserver/login
- 用户名为学号/教工号
- 支持: 账号密码登录
- 本 Skill 通过模拟 SSO 登录获取 Cookie + CSRF Token

**教管平台**: https://jwxt.bistu.edu.cn
- 基于 SSO Cookie + CSRF Token (_WEU) 访问
- API 基础路径: `/jwapp/sys/homeapp/api/home/`
- 需要 Header: `X-Requested-With: XMLHttpRequest` + `X-CSRF-TOKEN: <_WEU值>`

**一网通办**: https://my.bistu.edu.cn/fe/
- Nuxt.js 前端，REST API
- API 基础路径: `/api/`
- 公开接口无需认证，登录接口需要 RSA 加密密码

**学习通 (超星)**: https://mooc1-1.chaoxing.com
- 手机号 + 密码登录（移动端API，无验证码）
- API: `passport2-api.chaoxing.com/v11/loginregister`

所有脚本位于 `scripts/` 目录，用 `python3` 执行。

---

## 依赖安装

```bash
pip3 install requests beautifulsoup4 python-pptx icalendar
```

可选依赖（一网通办登录）:
```bash
pip3 install pycryptodome
```

---

## 注意事项

1. **SSO Cookie 有效期有限**，过期后需重新登录，脚本会自动处理
2. **教管平台需要 CSRF Token**，脚本会自动从 _WEU Cookie 提取
3. **学习通签到仅提供提醒功能**，请在手机端完成实际签到
4. **一网通办登录需要 RSA 加密**，安装 pycryptodome: `pip install pycryptodome`
5. **空闲教室基于课表数据推断**，非官方独立API，可能存在偏差
6. **遵守学校网络安全规定**，本工具仅供个人学习使用
