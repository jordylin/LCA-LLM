
---

## 📝 后续更新文件的标准流程

### 日常提交推送（推荐）

```bash
# 1. 查看修改
git status

# 2. 添加所有修改
git add -A

# 3. 提交（写清楚改了什么）
git commit -m "将框架换成Qwen适配框架；融合vLLM框架以加速推理过程；新增流式输出支持"

# 4. 推送到 GitHub
git push origin main
```

### 如果推送失败

```bash
# 先拉取远程更新
git pull origin main --rebase

# 如果有冲突，解决后继续
git add <冲突文件>
git rebase --continue

# 再推送
git push origin main
```

### 紧急情况（确定本地是对的）

```bash
# 强制推送（慎用！会覆盖远程）
git push origin main --force
```

### 💡 最佳实践

1. **每次改完就提交**：小步快跑
2. **提交信息要清楚**：说明改了什么
3. **推送前先 pull**：避免冲突
4. **不确定时先备份**：`git branch backup`

---
