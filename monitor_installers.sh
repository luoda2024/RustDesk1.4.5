#!/bin/bash
# LUODA 构建安装程序监控脚本
# 专注于检查安装程序生成情况

echo "=== LUODA 安装程序构建监控 ==="
echo "监控时间: $(date '+%Y-%m-%d %H:%M:%S')"

# 关键文件检查
echo ""
echo "## 1. 关键配置文件检查"
CHECK_FILES=(
    "Cargo.toml"
    "flutter/windows/CMakeLists.txt"
    "flutter/windows/runner/Runner.wxs"
    "flutter/linux/CMakeLists.txt"
)

for file in "${CHECK_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file: 存在"
        # 检查关键配置
        case "$file" in
            "Cargo.toml")
                if grep -q 'name = "luoda"' "$file"; then
                    echo "   包名正确: luoda"
                else
                    echo "   ⚠️ 包名可能不正确"
                fi
                ;;
            "flutter/windows/CMakeLists.txt")
                if grep -q 'project(luodad' "$file"; then
                    echo "   Windows项目名正确: luodad"
                else
                    echo "   ⚠️ Windows项目名可能不正确"
                fi
                ;;
            "flutter/windows/runner/Runner.wxs")
                if grep -q 'Name="LUODA"' "$file"; then
                    echo "   MSI安装程序名称正确: LUODA"
                else
                    echo "   ⚠️ MSI安装程序名称可能不正确"
                fi
                ;;
        esac
    else
        echo "❌ $file: 不存在"
    fi
done

# 检查构建产物期望
echo ""
echo "## 2. 期望的安装程序文件"
EXPECTED_INSTALLERS=(
    "luodad.exe - Windows可执行文件"
    "LUODA.msi - Windows安装包"
    "luodad.AppImage - Linux应用"
    "luodad.deb - Linux安装包"
)

for installer in "${EXPECTED_INSTALLERS[@]}"; do
    echo "   📦 $installer"
done

# 构建状态判断
echo ""
echo "## 3. 构建状态分析"
echo "基于提交时间分析:"
echo "   最新提交: a053146e3 (23:46提交)"
echo "   构建时长: 约30分钟"
echo "   预计完成: 00:16左右"

echo ""
echo "## 4. 下一步建议"
echo "1. 访问 https://github.com/luoda2024/RustDesk1.4.5/actions"
echo "2. 查看 'luoda-custom-modify' 分支的最新构建"
echo "3. 如果构建成功，下载所有安装程序文件"
echo "4. 重点关注: LUODA.msi (Windows安装程序)"

echo ""
echo "=== 监控完成 ==="
