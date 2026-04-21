#!/usr/bin/env python3
"""通过 GitHub Device Flow 获取 token 并创建仓库+推送"""
import requests
import time
import subprocess
import sys

# Step 1: 启动 Device Flow
print("正在启动 GitHub 认证...")
resp = requests.post("https://github.com/login/device/code", data={
    "client_id": "Iv1.b507a08c87ecfe68",  # GitHub CLI 的 public client_id
    "scope": "repo"
})

if resp.status_code != 200:
    print(f"Device flow 启动失败: {resp.status_code} {resp.text}")
    sys.exit(1)

data = dict(x.split("=") for x in resp.text.split("&"))
device_code = data["device_code"]
user_code = data["user_code"]
verification_uri = data["verification_uri"]
interval = int(data.get("interval", "5"))

print(f"\n{'='*50}")
print(f"请在浏览器中打开: {verification_uri}")
print(f"并输入代码: {user_code}")
print(f"{'='*50}\n")

# Step 2: 轮询等待用户确认
print("等待认证...")
while True:
    time.sleep(interval)
    resp = requests.post("https://github.com/login/oauth/access_token", data={
        "client_id": "Iv1.b507a08c87ecfe68",
        "device_code": device_code,
        "grant_type": "urn:ietf:params:oauth:grant-type:device_code"
    }, headers={"Accept": "application/json"})
    
    result = resp.json()
    if "access_token" in result:
        token = result["access_token"]
        print("认证成功!")
        break
    elif result.get("error") == "authorization_pending":
        continue
    elif result.get("error") == "slow_down":
        interval += 5
        continue
    else:
        print(f"认证失败: {result}")
        sys.exit(1)

# Step 3: 创建仓库
print("正在创建仓库...")
headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
resp = requests.get("https://api.github.com/repos/wanfeng0330/openclaw-bistu", headers=headers)

if resp.status_code == 200:
    print("仓库已存在")
elif resp.status_code == 404:
    resp = requests.post("https://api.github.com/user/repos", headers=headers, json={
        "name": "openclaw-bistu",
        "description": "北京信息科技大学全能 AI 校园助手 | 基于 OpenClaw 框架",
        "private": False,
        "auto_init": False,
    })
    if resp.status_code == 201:
        print("仓库创建成功!")
    else:
        print(f"创建失败: {resp.status_code} {resp.text[:300]}")
        sys.exit(1)
else:
    print(f"检查失败: {resp.status_code}")

# Step 4: 设置远程并推送
clone_url = f"https://{token}@github.com/wanfeng0330/openclaw-bistu.git"

result = subprocess.run(
    ["git", "remote", "set-url", "origin", clone_url],
    capture_output=True, text=True, cwd="d:/openclaw-bistu"
)

result = subprocess.run(
    ["git", "push", "-u", "origin", "master"],
    capture_output=True, text=True, cwd="d:/openclaw-bistu"
)
if result.returncode == 0:
    print("推送成功!")
    print(f"仓库地址: https://github.com/wanfeng0330/openclaw-bistu")
else:
    print(f"推送输出: {result.stdout}")
    print(f"推送错误: {result.stderr}")

# 清理远程 URL 中的 token
subprocess.run(
    ["git", "remote", "set-url", "origin", "https://github.com/wanfeng0330/openclaw-bistu.git"],
    capture_output=True, text=True, cwd="d:/openclaw-bistu"
)
