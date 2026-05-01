#!/bin/bash
# RustDesk LUODA 连接测试脚本
# 作者：小赫
# 版本：1.0

set -e

echo "=== RustDesk LUODA 连接测试 ==="
echo "测试时间: $(date)"
echo ""

# 测试服务器连接
test_servers=(
    "luoda-server-1.example.com:21116"
    "luoda-server-2.example.com:21116"
    "luoda-server-3.example.com:21116"
)

echo "1. 服务器连接测试"
echo "-----------------"
for server in "${test_servers[@]}"; do
    host=$(echo $server | cut -d: -f1)
    port=$(echo $server | cut -d: -f2)
    
    echo -n "测试 $host:$port ... "
    
    # 使用nc测试端口连通性
    if timeout 5 nc -z $host $port 2>/dev/null; then
        echo "✅ 连接成功"
    else
        echo "❌ 连接失败"
    fi
done

echo ""
echo "2. 网络延迟测试"
echo "-----------------"
for server in "${test_servers[@]}"; do
    host=$(echo $server | cut -d: -f1)
    
    echo -n "测试 $host 延迟 ... "
    ping_result=$(timeout 5 ping -c 3 $host 2>/dev/null | grep "rtt" || echo "无法测试")
    echo "$ping_result"
done

echo ""
echo "3. 带宽测试（简单版）"
echo "-----------------"
# 测试本地网络状态
echo -n "本地网络状态 ... "
if ip route | grep -q default; then
    echo "✅ 网络连接正常"
else
    echo "❌ 无网络连接"
fi

echo ""
echo "=== 测试完成 ==="