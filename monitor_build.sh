#!/bin/bash
# LUODA 构建监控脚本
# 每15分钟自动运行，监控构建状态并报告

set -e

echo "=========================================="
echo "LUODA 构建监控报告 - $(date '+%Y年%m月%d日 %H:%M:%S')"
echo "=========================================="

# 1. 检查最新提交
echo ""
echo "## 📊 提交状态"
LATEST_COMMIT=$(git log --oneline -1)
echo "最新提交: $LATEST_COMMIT"

COMMIT_TIME=$(git show -s --format=%ci HEAD)
echo "提交时间: $COMMIT_TIME"

# 2. 检查本地修改
echo ""
echo "## 📝 本地修改状态"
UNCOMMITTED=$(git status --short)
if [ -n "$UNCOMMITTED" ]; then
    echo "⚠️ 有未提交的修改:"
    echo "$UNCOMMITTED"
else
    echo "✅ 工作区干净"
fi

# 3. 检查远程分支状态
echo ""
echo "## 🔄 远程分支状态"
REMOTE_STATUS=$(git log --oneline origin/luoda-custom-modify..HEAD 2>/dev/null || echo "与远程同步")
if [ -n "$REMOTE_STATUS" ] && [ "$REMOTE_STATUS" != "与远程同步" ]; then
    echo "⚠️ 有未推送的提交:"
    echo "$REMOTE_STATUS"
else
    echo "✅ 与远程分支同步"
fi

# 4. 检查构建配置文件
echo ""
echo "## ⚙️ 构建配置检查"
CONFIG_FILES=(
    "Cargo.toml"
    "flutter/linux/CMakeLists.txt"
    "flutter/windows/CMakeLists.txt"
    "libs/hbb_common/src/config.rs"
)

for file in "${CONFIG_FILES[@]}"; do
    if [ -f "$file" ]; then
        if grep -q "luodad\|LUODA\|dicad.cn" "$file" 2>/dev/null; then
            echo "✅ $file - 品牌化配置正确"
        elif grep -q "rustdesk\|rustdesk.com" "$file" 2>/dev/null; then
            echo "❌ $file - 发现未替换的品牌内容"
        else
            echo "🔍 $file - 配置正常"
        fi
    else
        echo "⚠️ $file - 文件不存在"
    fi
done

# 5. 检查图标文件
echo ""
echo "## 🖼️ 图标文件检查"
ICON_FILES=(
    "res/icon.png"
    "res/icon.ico"
    "flutter/assets/logo.png"
    "flutter/assets/icon.png"
)

for icon in "${ICON_FILES[@]}"; do
    if [ -f "$icon" ]; then
        SIZE=$(stat -c%s "$icon" 2>/dev/null || stat -f%z "$icon" 2>/dev/null || echo "未知")
        echo "✅ $icon - 存在 ($((SIZE/1024)) KB)"
    else
        echo "❌ $icon - 文件缺失"
    fi
done

# 6. 预估构建状态
echo ""
echo "## ⏱️ 构建时间预估"
COMMIT_TIMESTAMP=$(git show -s --format=%ct HEAD)
CURRENT_TIMESTAMP=$(date +%s)
TIME_DIFF=$((CURRENT_TIMESTAMP - COMMIT_TIMESTAMP))

if [ $TIME_DIFF -lt 300 ]; then
    echo "🔄 构建可能刚刚开始 (${TIME_DIFF}秒前提交)"
    echo "预计完成: $(date -d "+30 minutes" '+%H:%M')"
elif [ $TIME_DIFF -lt 1800 ]; then
    echo "⏳ 构建进行中 (${TIME_DIFF}秒前提交)"
    REMAINING=$((1800 - TIME_DIFF))
    echo "预计剩余: $((REMAINING / 60))分钟"
else
    echo "✅ 构建应该已完成 (${TIME_DIFF}秒前提交)"
    echo "请检查 GitHub Actions 页面确认结果"
fi

# 7. 学习进度检查
echo ""
echo "## 📚 学习进度"
if [ -f "LEARNING_PLAN.md" ]; then
    LEARNING_LINES=$(wc -l < LEARNING_PLAN.md)
    echo "✅ 学习计划已创建 ($LEARNING_LINES 行)"
    echo "学习重点: LUODA 构建系统和错误处理"
else
    echo "⚠️ 学习计划未创建"
fi

# 8. 应急准备状态
echo ""
echo "## 🚨 应急准备"
SCRIPTS=(
    "check_build_env.sh"
    "fix_build_env.sh"
    "quick_fix.sh"
)

READY_COUNT=0
TOTAL_COUNT=${#SCRIPTS[@]}
for script in "${SCRIPTS[@]}"; do
    if [ -f "$script" ]; then
        READY_COUNT=$((READY_COUNT + 1))
    fi
done

if [ $READY_COUNT -eq $TOTAL_COUNT ]; then
    echo "✅ 应急脚本准备就绪 ($READY_COUNT/$TOTAL_COUNT)"
else
    echo "⚠️ 应急脚本不全 ($READY_COUNT/$TOTAL_COUNT)"
fi

echo ""
echo "=========================================="
echo "下一次监控: $(date -d "+15 minutes" '+%H:%M')"
echo "=========================================="

# 9. 建议下一步行动
echo ""
echo "## 💡 建议下一步行动"
if [ -n "$UNCOMMITTED" ]; then
    echo "1. 提交本地修改"
fi
if [ "$REMOTE_STATUS" != "与远程同步" ] && [ -n "$REMOTE_STATUS" ]; then
    echo "2. 推送提交到远程"
fi
echo "3. 继续学习 LUODA 网络协议"
echo "4. 准备测试环境"
echo "5. 监控 GitHub Actions 构建日志"