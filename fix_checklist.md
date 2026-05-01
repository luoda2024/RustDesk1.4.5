# RustDesk → LUODA 修复清单

## 高优先级文件（立即修复）

### 1. Cargo.toml
- Line 2: `name = "rustdesk"` → `name = "luodad"`
- Line 4: `authors = ["rustdesk <info@rustdesk.com>"]` → `authors = ["LUODA Team <info@luoda.cn>"]`
- Line 7: `description = "RustDesk Remote Desktop"` → `description = "LUODA Remote Desktop"`
- Line 8: `default-run = "rustdesk"` → `default-run = "luodad"`
- Line 12: `name = "librustdesk"` → `name = "libluodad"`
- Line 16: `name = "rustdesk"` → `name = "luodad"`

### 2. 语言文件 (src/lang/*.rs)
需要替换所有语言文件中的用户可见文本：
- "RustDesk" → "LUODA"
- "rustdesk.com" → "luoda.cn"
- "RustDesk network" → "LUODA network"

### 3. 构建配置文件
- 检查所有 CMakeLists.txt 中的引用
- 更新 package.json 和 pubspec.yaml
- 验证构建输出名称

## 中优先级文件

### 4. Flutter UI 文件
- 检查 flutter/lib/ 目录下的所有 Dart 文件
- 替换用户界面中的品牌文本
- 更新帮助文本和提示信息

### 5. 文档文件
- README.md 和相关文档
- 帮助文件
- 许可证信息

## 低优先级文件

### 6. 代码注释和技术引用
- 保留技术性的变量名和函数名
- 更新代码注释中的品牌引用
- 清理无用的注释

## 验证步骤

1. **构建测试**
   - 运行 `cargo build --release`
   - 验证输出二进制名称
   - 检查构建日志

2. **功能测试**
   - 启动应用程序
   - 验证用户界面文本
   - 测试核心功能

3. **品牌验证**
   - 检查所有图标
   - 验证关于对话框
   - 确认帮助内容

## 回滚计划

如果修改导致问题：
1. 恢复备份文件
2. 重新构建测试
3. 分析问题原因
4. 分步重新修改
