# LUODA 构建产物下载指南

## 构建状态
- 分支: luoda-custom-modify
- 最新提交: 2171a5113 (fix: 彻底修复Cargo.toml包名和所有rustdesk残留，完成核心品牌化)
- 提交时间: 约22:50

## 如何下载构建产物

### 方法1: 通过GitHub网页界面
1. 访问: https://github.com/luoda2024/RustDesk1.4.5/actions
2. 找到 "luoda-custom-modify" 分支的最新构建
3. 点击构建名称进入详情页
4. 在 "Artifacts" 部分下载所有文件

### 方法2: 使用gh CLI (需要安装和认证)
```bash
# 安装gh CLI
sudo apt-get install gh

# 登录GitHub
gh auth login

# 列出构建
gh run list --limit 10

# 下载最新构建的产物
gh run download $(gh run list --limit 1 --json databaseId --jq '.[0].databaseId')
```

### 方法3: 使用GitHub API
```bash
# 需要有效的GitHub Token
TOKEN="your_github_token"
REPO="luoda2024/RustDesk1.4.5"

# 获取最新构建ID
curl -H "Authorization: token $TOKEN"   "https://api.github.com/repos/$REPO/actions/runs?branch=luoda-custom-modify&per_page=1" | jq '.workflow_runs[0].id'

# 下载构建产物
# (需要构建ID和artifact名称)
```

## 预期的构建产物
1. luodad.exe - Windows可执行文件
2. LUODA.msi - Windows安装包
3. app-release.apk - Android应用
4. luodad.AppImage - Linux应用
5. luodad.deb - Linux Debian包

## 测试计划
下载后，按照 `LUODA_测试方案.md` 进行测试。

## 问题排查
如果构建失败:
1. 检查构建日志中的错误信息
2. 查看是否缺少依赖或配置错误
3. 检查品牌化修改是否完整
4. 重新提交修复并触发新构建
