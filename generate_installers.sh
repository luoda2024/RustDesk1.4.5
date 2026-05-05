#!/bin/bash
# LUODA 安装包生成脚本
# 作者: 小赫
# 在构建成功后生成各平台安装包

set -e

echo "=== LUODA 安装包生成 ==="
echo "开始时间: $(date)"
echo

# 检查构建是否成功
echo "1. 检查构建状态..."
if [ ! -f "target/release/luodad" ]; then
    echo "❌ 错误: luodad 二进制文件不存在"
    echo "请先运行: cargo build --release"
    exit 1
fi

BINARY_SIZE=$(stat -c%s "target/release/luodad" 2>/dev/null || stat -f%z "target/release/luodad")
echo "✅ luodad 构建成功 ($((BINARY_SIZE/1024/1024)) MB)"

# 2. 创建输出目录
echo
echo "2. 创建输出目录..."
mkdir -p dist/{windows,linux,android,macos}
echo "✅ 创建 dist/ 目录结构"

# 3. 生成Linux DEB包
echo
echo "3. 生成Linux DEB包..."
if [ -d "debian" ]; then
    echo "  使用debian目录生成DEB包"
    cp target/release/luodad debian/
    cd debian && dpkg-buildpackage -us -uc
    cd ..
    mv ../luoda*.deb dist/linux/ 2>/dev/null || true
    echo "  ✅ DEB包生成完成"
else
    echo "  ⚠️ debian目录不存在，跳过DEB包生成"
fi

# 4. 准备Windows交叉编译
echo
echo "4. 准备Windows交叉编译..."
if command -v x86_64-w64-mingw32-gcc >/dev/null 2>&1; then
    echo "  Windows交叉编译工具已安装"
    echo "  运行: cargo build --release --target x86_64-pc-windows-gnu"
else
    echo "  ⚠️ Windows交叉编译工具未安装"
    echo "  安装命令: sudo apt-get install gcc-mingw-w64-x86-64"
fi

# 5. 检查Android构建
echo
echo "5. 检查Android构建..."
if [ -d "flutter" ]; then
    cd flutter
    if command -v flutter >/dev/null 2>&1; then
        echo "  Flutter已安装，可以构建Android APK"
        echo "  运行: flutter build apk --release"
    else
        echo "  ⚠️ Flutter未安装"
    fi
    cd ..
else
    echo "  ⚠️ flutter目录不存在"
fi

# 6. 生成Windows MSI包
echo
echo "6. 检查Windows MSI包生成..."
if [ -d "res/msi" ]; then
    echo "  MSI构建脚本存在"
    echo "  需要Windows环境或wine来生成MSI"
else
    echo "  ⚠️ res/msi目录不存在"
fi

# 7. 创建便携版
echo
echo "7. 创建便携版..."
mkdir -p dist/portable
cp target/release/luodad dist/portable/
cp -r res/icon.png dist/portable/ 2>/dev/null || true
cp -r res/icon.ico dist/portable/ 2>/dev/null || true

# 创建启动脚本
cat > dist/portable/start-luoda.sh << 'EOF'
#!/bin/bash
# LUODA 便携版启动脚本
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"
./luodad
EOF
chmod +x dist/portable/start-luoda.sh

cat > dist/portable/start-luoda.bat << 'EOF'
@echo off
REM LUODA 便携版启动脚本 (Windows)
cd /d "%~dp0"
luodad.exe
EOF

echo "  ✅ 便携版创建完成"

# 8. 生成构建报告
echo
echo "8. 生成构建报告..."
cat > dist/build-report.md << EOF
# LUODA 构建报告
生成时间: $(date)

## 构建信息
- 二进制文件: luodad
- 大小: $((BINARY_SIZE/1024/1024)) MB
- 构建时间: $(date '+%Y-%m-%d %H:%M:%S')

## 生成的文件
\`\`\`
$(find dist -type f | sort)
\`\`\`

## 系统信息
- 操作系统: $(uname -s -r)
- 架构: $(uname -m)
- Rust版本: $(rustc --version 2>/dev/null || echo "未知")

## 下一步
1. 测试二进制文件: ./dist/portable/luodad
2. 分发安装包
3. 更新版本号
EOF

echo "  ✅ 构建报告生成完成"

# 9. 验证生成的文件
echo
echo "9. 验证生成的文件..."
echo "dist/ 目录内容:"
find dist -type f | sort

echo
echo "=== 安装包生成完成 ==="
echo "已生成:"
echo "  - 便携版 (dist/portable/)"
echo "  - Linux DEB包 (dist/linux/)"
echo "  - 构建报告 (dist/build-report.md)"
echo
echo "需要手动完成:"
echo "1. Windows交叉编译: cargo build --release --target x86_64-pc-windows-gnu"
echo "2. Android APK构建: cd flutter && flutter build apk --release"
echo "3. macOS DMG构建: 需要macOS环境"
echo
echo "结束时间: $(date)"