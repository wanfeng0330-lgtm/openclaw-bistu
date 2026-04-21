# 🤝 贡献指南

感谢你对 openclaw-bistu 的关注！欢迎提交 Issue 和 Pull Request。

## 如何贡献

### 1. Fork & Clone

```bash
git clone https://github.com/your-username/openclaw-bistu.git
cd openclaw-bistu
```

### 2. 创建分支

```bash
git checkout -b feature/your-feature-name
```

### 3. 开发 & 测试

```bash
# 安装依赖
pip install requests beautifulsoup4 python-pptx pdfplumber Pillow reportlab icalendar

# 运行测试
python3 scripts/jwxt_api.py --help
```

### 4. 提交代码

```bash
git add .
git commit -m "feat: 添加 XXX 功能"
git push origin feature/your-feature-name
```

### 5. 创建 Pull Request

在 GitHub 上提交 PR，描述你的修改内容。

## 开发规范

### 代码风格

- Python: 遵循 PEP 8
- 使用 `python3` 执行所有脚本
- 每个脚本支持 `--help` 参数
- 函数和类必须有 docstring

### 新增功能

1. 在 `scripts/` 下添加新的 Python 脚本
2. 在 `SKILL.md` 中添加对应的功能描述（含触发词和命令）
3. 在 `README.md` 中更新功能列表
4. 如需新配置项，更新 `config.example.json`

### SKILL.md 编写规范

每项功能遵循统一格式：

```markdown
### N. 功能名称
**触发**: "触发词1"、"触发词2"
\```bash
python3 scripts/xxx.py subcommand [参数]
\```
注意事项或使用说明
```

### 提交信息格式

- `feat: 新功能`
- `fix: 修复 Bug`
- `docs: 文档更新`
- `refactor: 重构`
- `chore: 杂项`

## 功能需求

当前急需贡献的领域：

| 优先级 | 功能 | 难度 | 说明 |
|--------|------|------|------|
| 🔴 高 | 教管平台 API 逆向 | ⭐⭐⭐ | 需要抓包分析 jwxt.bistu.edu.cn 的接口 |
| 🔴 高 | 学习通 API 完善 | ⭐⭐ | 补充签到、作业提交等功能 |
| 🟠 中 | 校友圈接入实现 | ⭐⭐⭐ | 微信小程序云开发 API 对接 |
| 🟠 中 | PPT 模板制作 | ⭐ | 制作北信科官方风格 PPT 模板 |
| 🟡 低 | 校园地图功能 | ⭐ | 静态地图数据 + 路线规划 |
| 🟡 低 | 校园网流量查询 | ⭐⭐ | 对接校园网自助服务平台 |

## 注意事项

- ⚠️ **不要提交 `config.json`**（含用户凭证）
- ⚠️ **遵守学校网络安全规定**，不做恶意请求
- ⚠️ **尊重他人隐私**，不采集或存储他人信息
- ⚠️ 所有 API 请求需要合理控制频率，避免给学校服务器造成压力

## 联系方式

- GitHub Issues: https://github.com/your-username/openclaw-bistu/issues
- 校友圈 BISTU 论坛: 微信小程序搜索"信息科大校友汇"
