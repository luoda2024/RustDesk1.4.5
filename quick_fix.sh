#!/bin/bash
# RustDesk 构建快速修复脚本
echo "=== RustDesk 构建快速修复 ==="

# 检查并创建必要的目录
echo "1. 检查目录结构..."
mkdir -p flutter/android/app/src/main/jniLibs/arm64-v8a
mkdir -p flutter/android/app/src/main/jniLibs/armeabi-v7a

# 确保 key.properties 存在
echo "2. 检查 key.properties..."
if [ ! -f "flutter/android/key.properties" ]; then
    cat > flutter/android/key.properties << EOF
storePassword=android
keyPassword=android
keyAlias=androiddebugkey
storeFile=debug.keystore
EOF
    echo "已创建 key.properties"
else
    echo "key.properties 已存在"
fi

# 检查构建触发
echo "3. 更新构建触发时间..."
date "+# Trigger build at %Y年%m月%d日 %H:%M:%S" > .build-trigger

echo "=== 快速修复完成 ==="
echo "下一步: 安装必要的构建工具链"
