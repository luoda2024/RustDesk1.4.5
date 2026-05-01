#!/bin/bash
# RustDesk 构建环境修复脚本
set -e

echo "=== RustDesk 构建环境修复 ==="
echo "开始修复构建环境..."

# 1. 安装基本构建工具
echo "1. 安装基本构建工具..."
apt-get update
apt-get install -y \
    build-essential \
    cmake \
    ninja-build \
    pkg-config \
    libssl-dev \
    libclang-dev \
    llvm \
    clang

# 2. 安装 Rust 工具链
echo "2. 安装 Rust 工具链..."
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
source $HOME/.cargo/env
rustup default stable
rustup target add x86_64-unknown-linux-gnu
rustup target add x86_64-pc-windows-gnu
rustup target add aarch64-linux-android
rustup target add armv7-linux-androideabi

# 3. 安装 vcpkg
echo "3. 安装 vcpkg..."
git clone https://github.com/microsoft/vcpkg.git /opt/vcpkg
cd /opt/vcpkg
./bootstrap-vcpkg.sh
echo 'export VCPKG_ROOT=/opt/vcpkg' >> $HOME/.bashrc
export VCPKG_ROOT=/opt/vcpkg

# 4. 安装 Android SDK/NDK (简化版本)
echo "4. 设置 Android 环境..."
mkdir -p $HOME/android
cd $HOME/android

# 下载命令行工具
if [ ! -f "commandlinetools-linux.zip" ]; then
    wget https://dl.google.com/android/repository/commandlinetools-linux-11076708_latest.zip -O commandlinetools-linux.zip
    unzip commandlinetools-linux.zip -d cmdline-tools
    mv cmdline-tools/cmdline-tools cmdline-tools/latest
fi

# 设置环境变量
echo 'export ANDROID_HOME=$HOME/android' >> $HOME/.bashrc
echo 'export ANDROID_SDK_ROOT=$HOME/android' >> $HOME/.bashrc
export ANDROID_HOME=$HOME/android
export ANDROID_SDK_ROOT=$HOME/android

# 5. 创建临时的 Android 签名密钥
echo "5. 创建临时 Android 签名密钥..."
cd /home/luoda/rustdesk-custom/flutter/android

# 创建 debug keystore
cat > key.properties << EOF
storePassword=android
keyPassword=android
keyAlias=androiddebugkey
storeFile=debug.keystore
EOF

echo "=== 环境修复完成 ==="
echo "请运行以下命令使环境生效:"
echo "source $HOME/.bashrc"
echo "source $HOME/.cargo/env"
