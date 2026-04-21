# openclaw-bistu

> 北京信息科技大学全能 AI 校园助手 | 基于 [OpenClaw](https://github.com/nicepkg/openclaw) 框架

覆盖教务管理、一网通办、学习通、校园生活等 **21 项功能**，专为北信科学子打造。

## 功能一览

### 刚需功能（每周都用）

| # | 功能 | 示例指令 |
|---|------|----------|
| 1 | 课表查询 | "这学期有什么课？" |
| 2 | 培养方案 + 学业进度 | "还差多少学分毕业？" |
| 3 | 成绩查询 | "上学期考了多少？" |
| 4 | 考试安排 | "什么时候考试？在哪考？" |
| 5 | 学习通课程管理 | "学习通上有什么作业没交？" |
| 6 | 待办事项 | "还有什么没做的？" |

### 高频功能（每月多次）

| # | 功能 | 示例指令 |
|---|------|----------|
| 7 | 空闲教室查询 | "今天哪里有空教室自习？" |
| 8 | 校历 + 教学周 | "今天第几周？什么时候放假？" |
| 9 | 一网通办 | "怎么办理学籍证明？" |
| 10 | 开课单位查询 | "哪些学院开这门课？" |

### 实用功能（需要时用）

| # | 功能 | 示例指令 |
|---|------|----------|
| 11 | 北信科 PPT 一键生成 | "帮我用北信科模板做个答辩 PPT" |
| 12 | GPA 计算 | "帮我算一下GPA" |
| 13 | 食堂推荐 | "今天吃什么？" |
| 14 | 图书馆查询 | "图书馆几点关门？" |
| 15 | 学习通签到助手 | "帮我看看有没有待签到的课" |
| 16 | 校园邮箱 | "有没有新邮件？" |

### 工具功能

| # | 功能 | 示例指令 |
|---|------|----------|
| 17 | 镜像换源 | "帮我把 pip 换成清华源" |
| 18 | 正版软件 | "学校有什么免费软件？" |
| 19 | 在线工具 | "有什么在线 LaTeX 工具？" |
| 20 | 往年资源 | "有高数往年题吗？" |

## 安装

```bash
# 克隆 skill 包
git clone https://github.com/wanfeng0330/openclaw-bistu.git

# 安装 Python 依赖
pip install requests beautifulsoup4 python-pptx icalendar
```

## 配置

```bash
cd openclaw-bistu
python3 scripts/setup.py
```

交互式向导会引导完成所有配置。也可手动编辑 `config.json`（从 `config.example.json` 复制）。

### 认证配置一览

| 服务 | 必填？ | 认证方式 | 配置字段 |
|------|--------|----------|----------|
| 教管平台 (jwxt) | 必填 | SSO 账号密码 | `bistu_sso.username` / `bistu_sso.password` |
| 一网通办 (my) | 可选 | SSO 凭证或独立登录 | 复用 SSO 凭证 |
| 学习通 (chaoxing) | 可选 | 手机号+密码 | `chaoxing.phone` / `chaoxing.password` |
| 校园邮箱 | 可选 | 邮箱账号+密码 | `bistu_email` / `bistu_email_password` |

### 统一身份认证

北京信息科技大学使用统一身份认证平台 (`wxjw.bistu.edu.cn/authserver/login`)：
- **账号密码登录** — 学号 + 密码
- 本 Skill 通过模拟 SSO 登录获取 Cookie 和 CSRF Token (_WEU)

## 技术架构

| 平台 | 地址 | 技术栈 | API 基础路径 |
|------|------|--------|-------------|
| SSO | wxjw.bistu.edu.cn | CAS 认证 | `/authserver/login` |
| 教管平台 | jwxt.bistu.edu.cn | 金智教育(正方) | `/jwapp/sys/homeapp/api/home/` |
| 一网通办 | my.bistu.edu.cn | Nuxt.js + REST | `/api/` |
| 学习通 | mooc1-1.chaoxing.com | 超星移动端 | `passport2-api.chaoxing.com` |

### 教管平台 CSRF 防护

教管平台使用金智教育微服务平台，需要以下安全措施：
1. SSO 登录获取 `_WEU` Cookie
2. 所有 API 请求必须携带 `X-Requested-With: XMLHttpRequest` Header
3. 所有 API 请求必须携带 `X-CSRF-TOKEN: <_WEU值>` Header

## 项目结构

```
openclaw-bistu/
├── README.md                    # 本文件
├── SKILL.md                     # OpenClaw Skill 定义文件
├── CONTRIBUTING.md              # 贡献指南
├── LICENSE                      # MIT 许可证
├── config.example.json          # 配置模板
├── config.json                  # 用户配置（已 .gitignore）
├── scripts/
│   ├── setup.py                 # 一键交互式配置向导
│   ├── bistu_sso.py             # 统一身份认证登录模块
│   ├── jwxt_api.py              # 教管平台 API（课表/成绩/考试/空闲教室/培养方案/待办）
│   ├── ywtb_api.py              # 一网通办 API（应用/服务/搜索）
│   ├── chaoxing_api.py          # 学习通 API（课程/作业/签到）
│   ├── campus_life.py           # 校园生活（校历/食堂/图书馆/邮箱）
│   ├── generate_ppt.py          # 北信科 PPT 一键生成
│   └── gpa_calculator.py        # GPA 计算器
├── templates/                   # PPT 模板目录
└── docs/
    ├── SSO_LOGIN.md             # SSO 登录详细说明
    └── CHAOXING_GUIDE.md        # 学习通接入指南
```

## 安全须知

| 注意事项 | 说明 |
|----------|------|
| `config.json` 不会被提交 | 已在 `.gitignore` 中排除 |
| 密码明文存储 | 请勿分享配置文件给他人 |
| Cookie 有效期 | SSO Cookie 有过期时间，需定期刷新 |
| 最小权限原则 | 只配置需要的服务，不用的留空 |
| 仅供学习交流 | 请遵守学校网络安全规定 |

## 致谢

- [OpenClaw](https://github.com/nicepkg/openclaw) — AI 助手框架
- [openclaw-sjtu](https://github.com/xhh678876/openclaw-sjtu) — 上海交大 Skill 包，本项目的灵感来源
- 北京信息科技大学信息中心 — 提供校园信息化平台

## 许可证

MIT License © BISTU Students
