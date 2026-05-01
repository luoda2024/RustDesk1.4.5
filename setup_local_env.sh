#!/bin/bash
# 本地环境设置脚本
echo "设置本地构建环境..."

# 设置环境变量
export RUSTUP_HOME=$HOME/.rustup
export CARGO_HOME=$HOME/.cargo

# 尝试使用现有工具链
if [ -f "$HOME/.cargo/env" ]; then
    source $HOME/.cargo/env
    echo "已加载 Rust 环境"
else
    echo "警告: Rust 环境未安装"
fi

# 创建必要的目录
mkdir -p /home/luoda/rustdesk-custom/flutter/android/app/src/main/jniLibs/arm64-v8a
mkdir -p /home/luoda/rustdesk-custom/flutter/android/app/src/main/jniLibs/armeabi-v7a

echo "本地环境设置完成"
