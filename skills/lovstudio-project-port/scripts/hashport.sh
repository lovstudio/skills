#!/bin/bash
# 基于项目名生成稳定端口号
# Usage: hashport.sh [project-name]
# 如不指定项目名，使用当前目录名

name="${1:-$(basename "$PWD")}"

# 计算哈希值
hash=0
for ((i=0; i<${#name}; i++)); do
    char="${name:$i:1}"
    ord=$(printf '%d' "'$char")
    hash=$((hash + ord * (i + 1)))
done

# 生成端口 (范围 3000-8999)
port=$((3000 + (hash % 6000)))

# 检查端口状态
if command -v lsof &>/dev/null && lsof -i :"$port" &>/dev/null; then
    proc=$(lsof -i :"$port" | awk 'NR==2 {print $1}')
    echo "$port  ← $name (occupied by $proc)" >&2
else
    echo "$port  ← $name" >&2
fi

echo "$port"
