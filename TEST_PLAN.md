# LUODA 品牌化构建测试方案
# 测试时间：2026年5月1日 23:30开始

## 测试目标
验证 RustDesk 1.4.5 品牌化为 LUODA 的完整性和功能性

## 测试环境准备

### 1. 下载构建产物
假设构建已完成，产物位于 GitHub Actions Artifacts 中：
- Windows: luodad.exe, LUODA.msi
- Android: app-release.apk  
- Linux: luodad.AppImage, luodad.deb
- macOS: luodad.dmg (如支持)

### 2. 测试工具安装
```bash
# 安装必要工具
sudo apt-get update
sudo apt-get install -y unzip wget curl

# 安装 Android 测试工具（可选）
# sudo apt-get install -y android-tools-adb

# 安装 Windows 程序运行环境（可选）
# sudo apt-get install -y wine
```

## 测试用例

### 测试1：品牌化验证
- [ ] 可执行文件名称：luodad.exe (Windows), luodad (Linux)
- [ ] 应用程序名称：LUODA (非 RustDesk)
- [ ] 图标验证：所有图标显示为 LUODA 图标
- [ ] 关于页面：显示 Powered by LUODA
- [ ] 链接验证：所有链接指向 dicad.cn

### 测试2：Windows EXE 测试
- [ ] 运行测试：./luodad.exe 能否正常启动
- [ ] 图标显示：任务栏和窗口图标是否正确
- [ ] 服务器连接：默认连接 luoda.dicad.cn
- [ ] 功能测试：基本远程控制功能

### 测试3：Windows MSI 安装测试
- [ ] 安装测试：msiexec /i LUODA.msi
- [ ] 安装路径：Program Files\LUODA\
- [ ] 开始菜单：LUODA 快捷方式
- [ ] 卸载测试：完全卸载无残留

### 测试4：Android APK 测试
- [ ] 安装测试：adb install app-release.apk
- [ ] 应用名称：LUODA
- [ ] 图标验证：应用图标正确
- [ ] 权限申请：必要的权限申请正常

### 测试5：Linux 平台测试
- [ ] AppImage 运行：./luodad.AppImage --appimage-extract-and-run
- [ ] DEB 包安装：sudo dpkg -i luodad.deb
- [ ] 依赖检查：所有依赖满足
- [ ] 服务启动：systemctl 服务正常

## 测试步骤

### 步骤1：下载构建产物
```bash
# 创建测试目录
mkdir -p ~/luoda-test
cd ~/luoda-test

# 假设从 GitHub Actions 下载产物
# 实际需要从构建页面下载
```

### 步骤2：Windows 测试（使用 wine 或实际 Windows 环境）
```bash
# 使用 wine 测试 EXE
wine luodad.exe --version

# 检查输出中是否包含 LUODA
```

### 步骤3：品牌化内容验证
```bash
# 检查二进制文件中的字符串
strings luodad.exe | grep -i "luoda\|dicad"
strings luodad.exe | grep -i "rustdesk" && echo "发现残留!"

# 检查版本信息
wine luodad.exe --version
```

### 步骤4：功能快速测试
```bash
# 测试基本功能
# 1. 启动应用程序
# 2. 检查关于页面
# 3. 验证服务器配置
# 4. 测试连接功能
```

## 问题记录和修复

### 常见问题及解决方案
1. **构建失败**：检查 Cargo.toml 和依赖配置
2. **图标不显示**：验证图标文件路径和格式
3. **服务器连接失败**：检查 config.rs 中的服务器地址
4. **名称未完全替换**：运行批量替换脚本

### 应急修复流程
1. 记录问题现象
2. 分析问题原因
3. 准备修复补丁
4. 提交修复并触发新构建
5. 重新测试

## 测试时间安排
- 23:30-00:00: Windows 平台测试
- 00:00-00:30: 品牌化内容验证
- 00:30-01:00: 问题修复准备
- 01:00-02:00: 最终验证

## 成功标准
1. ✅ 所有平台构建成功
2. ✅ 品牌化内容完全替换
3. ✅ 基本功能正常
4. ✅ 无 RustDesk 残留
5. ✅ 服务器连接正常

## 测试报告模板
```
测试报告 - LUODA 品牌化构建
测试时间: [时间]
测试人员: 小赫（AI助手）

### 构建状态
- 构建结果: [成功/失败]
- 构建时间: [时间]

### 平台测试结果
- Windows EXE: [通过/失败]
- Windows MSI: [通过/失败]
- Android APK: [通过/失败]
- Linux: [通过/失败]

### 品牌化验证
- 名称替换: [通过/失败]
- 图标替换: [通过/失败]
- 链接替换: [通过/失败]
- 服务器配置: [通过/失败]

### 发现的问题
1. [问题描述]
2. [问题描述]

### 建议修复
1. [修复方案]
2. [修复方案]

### 总体评价
[评价内容]
```

---
**测试原则**：严谨、全面、高效。发现问题立即修复，确保今晚完成任务。