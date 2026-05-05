#!/bin/bash
# LUODA 快速修复脚本
# 处理最紧急的品牌化问题
# 作者: 小赫

set -e  # 遇到错误退出

echo "=== LUODA 品牌化快速修复 ==="
echo "开始时间: $(date)"
echo

# 1. 重命名配置文件
echo "1. 重命名配置文件..."
cd /home/luoda/rustdesk-custom/res

if [ -f "rustdesk.desktop" ]; then
    cp rustdesk.desktop luoda.desktop
    sed -i 's/LUODA/LUODA/g' luoda.desktop
    sed -i 's/rustdesk/luoda/g' luoda.desktop
    echo "  ✅ 创建 luoda.desktop"
fi

if [ -f "rustdesk-link.desktop" ]; then
    cp rustdesk-link.desktop luoda-link.desktop
    sed -i 's/LUODA/LUODA/g' luoda-link.desktop
    sed -i 's/rustdesk/luoda/g' luoda-link.desktop
    sed -i 's/x-scheme-handler\/rustdesk/x-scheme-handler\/luoda/g' luoda-link.desktop
    echo "  ✅ 创建 luoda-link.desktop"
fi

if [ -f "rustdesk.service" ]; then
    cp rustdesk.service luoda.service
    sed -i 's/LUODA/LUODA/g' luoda.service
    sed -i 's/rustdesk/luoda/g' luoda.service
    echo "  ✅ 创建 luoda.service"
fi

# 2. 修复构建脚本中的硬编码
echo
echo "2. 修复构建脚本..."
cd /home/luoda/rustdesk-custom

if [ -f "build.py" ]; then
    cp build.py build.py.bak
    sed -i 's/rustdesk <info@rustdesk.com>/LUODA Team <team@luoda.org>/g' build.py
    sed -i 's|https://rustdesk.com|https://luoda.org|g' build.py
    sed -i 's|/usr/share/rustdesk|/usr/share/luoda|g' build.py
    sed -i 's|/etc/rustdesk|/etc/luoda|g' build.py
    sed -i 's|apps/rustdesk.png|apps/luoda.png|g' build.py
    sed -i 's|apps/rustdesk.svg|apps/luoda.svg|g' build.py
    sed -i 's|rustdesk.desktop|luoda.desktop|g' build.py
    sed -i 's|rustdesk-link.desktop|luoda-link.desktop|g' build.py
    sed -i 's|rustdesk.service|luoda.service|g' build.py
    sed -i 's|rustdesk-%s.deb|luoda-%s.deb|g' build.py
    echo "  ✅ 修复 build.py"
fi

# 3. 修复便携版脚本
echo
echo "3. 修复便携版脚本..."
if [ -f "libs/portable/generate.py" ]; then
    cp libs/portable/generate.py libs/portable/generate.py.bak
    sed -i "s/'rustdesk'/'luoda'/g" libs/portable/generate.py
    sed -i 's/rustdesk.exe/luoda.exe/g' libs/portable/generate.py
    sed -i 's|../rustdesk/|../luoda/|g' libs/portable/generate.py
    sed -i 's|./rustdesk|./luoda|g' libs/portable/generate.py
    echo "  ✅ 修复 generate.py"
fi

# 4. 修复macOS构建脚本
echo
echo "4. 修复macOS构建脚本..."
if [ -f "res/osx-dist.sh" ]; then
    cp res/osx-dist.sh res/osx-dist.sh.bak
    sed -i 's/rustdesk-\$VERSION.dmg/luoda-\$VERSION.dmg/g' res/osx-dist.sh
    echo "  ✅ 修复 osx-dist.sh"
fi

# 5. 修复Windows安装脚本
echo
echo "5. 修复Windows安装脚本..."
if [ -f "res/msi/preprocess.py" ]; then
    cp res/msi/preprocess.py res/msi/preprocess.py.bak
    sed -i 's|https://github.com/rustdesk/rustdesk|https://github.com/luoda-org/luoda|g' res/msi/preprocess.py
    sed -i 's|../../rustdesk|../../luoda|g' res/msi/preprocess.py
    echo "  ✅ 修复 preprocess.py"
fi

# 6. 验证修复
echo
echo "6. 验证修复..."
echo "检查剩余的 rustdesk 引用:"
grep -r "rustdesk" --include="*.py" --include="*.sh" --include="*.desktop" --include="*.service" . 2>/dev/null | grep -v ".bak" | grep -v "rustdesk.com" | head -10

echo
echo "检查创建的 luoda 文件:"
ls -la res/*.desktop res/*.service 2>/dev/null || true

echo
echo "=== 快速修复完成 ==="
echo "已处理:"
echo "  - 配置文件重命名和更新"
echo "  - 构建脚本品牌化"
echo "  - 便携版脚本修复"
echo "  - macOS构建脚本修复"
echo "  - Windows安装脚本修复"
echo
echo "备份文件:"
find . -name "*.bak" -type f 2>/dev/null | head -5
echo
echo "下一步:"
echo "1. 运行完整修复脚本: python3 fix_branding.py --apply"
echo "2. 测试构建: cargo build --release"
echo "3. 验证系统集成"
echo
echo "结束时间: $(date)"