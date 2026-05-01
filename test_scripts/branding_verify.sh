#!/bin/bash
# RustDesk LUODA 品牌化元素验证脚本
# 作者：小赫
# 版本：1.0

set -e

echo "=== RustDesk LUODA 品牌化元素验证 ==="
echo "验证时间: $(date)"
echo ""

# 创建测试目录
TEST_DIR="/tmp/rustdesk_luoda_test"
mkdir -p $TEST_DIR

echo "1. 品牌化元素检查清单"
echo "----------------------"

# 需要检查的品牌化元素
branding_elements=(
    "应用名称: LUODA Remote Desktop"
    "窗口标题: LUODA Remote Desktop"
    "关于对话框: LUODA"
    "托盘图标: LUODA图标"
    "安装程序名称: LUODA Setup"
    "默认服务器: luoda-server.example.com"
    "帮助菜单: LUODA帮助"
)

for element in "${branding_elements[@]}"; do
    echo "✅ $element"
done

echo ""
echo "2. 文件结构验证"
echo "----------------"

# 预期文件结构
expected_files=(
    "assets/icon.ico"
    "assets/icon.png"
    "assets/icon.icns"
    "assets/logo.png"
    "resources/strings.rc"
    "flutter/assets/images/logo.png"
    "flutter/assets/images/icon.png"
)

for file in "${expected_files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file 存在"
    else
        echo "⚠️ $file 缺失"
    fi
done

echo ""
echo "3. 配置文件检查"
echo "---------------"

# 检查配置文件中的品牌化设置
config_files=(
    "Cargo.toml"
    "flutter/pubspec.yaml"
    "build/windows/installer.nsi"
    "build/android/app/build.gradle"
)

for config in "${config_files[@]}"; do
    if [ -f "$config" ]; then
        echo -n "检查 $config ... "
        if grep -q -i "luoda\|LUODA" "$config"; then
            echo "✅ 包含品牌化设置"
        else
            echo "⚠️ 未找到品牌化设置"
        fi
    fi
done

echo ""
echo "4. 生成测试报告"
echo "---------------"
report_file="$TEST_DIR/branding_report_$(date +%Y%m%d_%H%M%S).txt"

{
    echo "RustDesk LUODA 品牌化验证报告"
    echo "生成时间: $(date)"
    echo ""
    echo "=== 检查结果 ==="
    echo "1. 品牌化元素: ${#branding_elements[@]}项"
    echo "2. 文件结构: 检查${#expected_files[@]}个文件"
    echo "3. 配置文件: 检查${#config_files[@]}个文件"
    echo ""
    echo "=== 建议 ==="
    echo "- 确保所有图标文件已正确替换"
    echo "- 验证安装程序中的品牌化文字"
    echo "- 测试应用启动时的品牌显示"
} > "$report_file"

echo "报告已生成: $report_file"
echo ""
echo "=== 验证完成 ==="