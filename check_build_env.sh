#!/bin/bash
# 构建环境检查脚本
echo "=== RustDesk 构建环境检查 ==="
echo "检查时间: $(date)"
echo ""

# 检查基本工具
echo "1. 检查基本工具:"
which make && make --version | head -1
which cmake && cmake --version | head -1
which git && git --version
which curl && curl --version | head -1
echo ""

# 检查 Rust 工具链
echo "2. 检查 Rust 工具链:"
if command -v rustc &> /dev/null; then
    rustc --version
    cargo --version
else
    echo "Rust 未安装"
fi
echo ""

# 检查 Flutter
echo "3. 检查 Flutter:"
if command -v flutter &> /dev/null; then
    flutter --version
else
    echo "Flutter 未安装"
fi
echo ""

# 检查 Android 工具链
echo "4. 检查 Android 工具链:"
if [ -n "$ANDROID_HOME" ]; then
    echo "ANDROID_HOME: $ANDROID_HOME"
else
    echo "ANDROID_HOME 未设置"
fi

if [ -n "$ANDROID_NDK_HOME" ]; then
    echo "ANDROID_NDK_HOME: $ANDROID_NDK_HOME"
else
    echo "ANDROID_NDK_HOME 未设置"
fi
echo ""

# 检查 vcpkg
echo "5. 检查 vcpkg:"
if [ -n "$VCPKG_ROOT" ]; then
    echo "VCPKG_ROOT: $VCPKG_ROOT"
    if [ -f "$VCPKG_ROOT/vcpkg" ]; then
        echo "vcpkg 可执行文件存在"
    else
        echo "vcpkg 可执行文件不存在"
    fi
else
    echo "VCPKG_ROOT 未设置"
fi
echo ""

echo "=== 环境检查完成 ==="
