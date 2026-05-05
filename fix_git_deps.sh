#!/bin/bash
# LUODA Git依赖修复脚本
# 作者: 小赫
# 修复所有git依赖，确保构建稳定

set -e

echo "=== LUODA Git依赖修复 ==="
echo "开始时间: $(date)"
echo

# 1. 备份原始文件
echo "1. 备份原始Cargo.toml文件..."
cp libs/hbb_common/Cargo.toml libs/hbb_common/Cargo.toml.bak
cp libs/scrap/Cargo.toml libs/scrap/Cargo.toml.bak
cp Cargo.toml Cargo.toml.bak

echo "✅ 备份完成"

# 2. 修复hbb_common中的git依赖
echo
echo "2. 修复hbb_common中的git依赖..."

# 临时注释掉git依赖，使用crates.io版本
sed -i 's|confy = { git = "https://github.com/rustdesk/confy" }|# confy = { git = "https://github.com/rustdesk/confy" }\nconfy = "0.6"|' libs/hbb_common/Cargo.toml

sed -i 's|tokio-socks = { git = "https://github.com/rustdesk/tokio-socks" }|# tokio-socks = { git = "https://github.com/rustdesk/tokio-socks" }\ntokio-socks = "0.9"|' libs/hbb_common/Cargo.toml

sed -i 's|sysinfo = { git = "https://github.com/rustdesk-org/sysinfo", branch = "rlim_max" }|# sysinfo = { git = "https://github.com/rustdesk-org/sysinfo", branch = "rlim_max" }\nsysinfo = "0.30"|' libs/hbb_common/Cargo.toml

sed -i 's|default_net = { git = "https://github.com/rustdesk/default_net" }|# default_net = { git = "https://github.com/rustdesk/default_net" }\ndefault_net = "0.14"|' libs/hbb_common/Cargo.toml

sed -i 's|machine-uid = { git = "https://github.com/rustdesk/machine-uid" }|# machine-uid = { git = "https://github.com/rustdesk/machine-uid" }\nmachine-uid = "0.2"|' libs/hbb_common/Cargo.toml

echo "✅ hbb_common依赖修复完成"

# 3. 修复scrap中的git依赖
echo
echo "3. 修复scrap中的git依赖..."

sed -i 's|webm = { git = "https://github.com/rustdesk/rust-webm" }|# webm = { git = "https://github.com/rustdesk/rust-webm" }\nwebm = "0.2"|' libs/scrap/Cargo.toml

sed -i 's|hwcodec = { git = "https://github.com/rustdesk/hwcodec", optional = true }|# hwcodec = { git = "https://github.com/rustdesk/hwcodec", optional = true }\nhwcodec = { version = "0.1", optional = true }|' libs/scrap/Cargo.toml

sed -i 's|nokhwa = { git = "https://github.com/rustdesk/nokhwa.git", branch = "fix_from_raw_parts", features = \["input-native"\] }|# nokhwa = { git = "https://github.com/rustdesk/nokhwa.git", branch = "fix_from_raw_parts", features = ["input-native"] }\nnokhwa = { version = "0.11", features = ["input-native"] }|' libs/scrap/Cargo.toml

echo "✅ scrap依赖修复完成"

# 4. 修复主Cargo.toml中的git依赖
echo
echo "4. 修复主Cargo.toml中的git依赖..."

# 修复cpal依赖
sed -i 's|cpal = { git = "https://github.com/rustdesk-org/cpal", branch = "osx-screencapturekit" }|# cpal = { git = "https://github.com/rustdesk-org/cpal", branch = "osx-screencapturekit" }\ncpal = "0.15"|' Cargo.toml

# 修复tray-icon依赖
sed -i 's|tray-icon = { git = "https://github.com/tauri-apps/tray-icon" }|# tray-icon = { git = "https://github.com/tauri-apps/tray-icon" }\ntray-icon = "0.10"|' Cargo.toml

echo "✅ 主Cargo.toml依赖修复完成"

# 5. 清理Cargo缓存
echo
echo "5. 清理Cargo缓存..."
cargo clean

echo "✅ 缓存清理完成"

# 6. 验证修复
echo
echo "6. 验证修复..."
echo "检查剩余的git依赖:"
grep -r "git = " libs/hbb_common/Cargo.toml libs/scrap/Cargo.toml Cargo.toml 2>/dev/null || echo "✅ 没有找到git依赖"

echo
echo "检查版本号:"
grep -E "(confy|tokio-socks|sysinfo|default_net|machine-uid|webm|hwcodec|nokhwa|cpal|tray-icon)" libs/hbb_common/Cargo.toml libs/scrap/Cargo.toml Cargo.toml 2>/dev/null | head -20

echo
echo "=== Git依赖修复完成 ==="
echo "已处理:"
echo "  - hbb_common: 5个git依赖替换为crates.io版本"
echo "  - scrap: 3个git依赖替换为crates.io版本"
echo "  - 主Cargo.toml: 2个git依赖替换为crates.io版本"
echo
echo "下一步:"
echo "1. 测试构建: cargo check --no-default-features"
echo "2. 完整构建: cargo build --release"
echo "3. 如果构建成功，恢复备份文件: cp *.bak *.toml"
echo
echo "结束时间: $(date)"