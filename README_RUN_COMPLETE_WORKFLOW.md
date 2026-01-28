# 如何运行完整应用流程

## 📋 准备你的数据

要运行完整的应用流程，你需要准备以下数据：

1. **简历文本** (Resume Text)
2. **岗位描述** (JD Text)  
3. **项目材料** (Project Materials) - 可选但推荐

## 🚀 运行方式

### 方式 1: 使用文件（推荐）

1. 将你的数据保存为文件：

```bash
# 创建目录（如果不存在）
mkdir -p data/resumes data/jobs data/projects

# 将你的简历保存为
data/resumes/resume.txt

# 将JD保存为
data/jobs/jd.txt

# 将项目材料保存为（可选）
data/projects/projects.txt
```

2. 运行脚本：

```bash
python3 run_user_complete_workflow.py
```

### 方式 2: 交互式运行

直接运行脚本，然后按提示粘贴你的数据：

```bash
python3 run_user_complete_workflow.py
```

脚本会提示你：
- 粘贴简历文本
- 粘贴JD文本
- 粘贴项目材料（可选）

## 📤 输出文件

运行完成后，所有输出将保存在 `data/outputs/` 目录：

- `complete_output_[timestamp].json` - 所有 Agent 的完整输出
- `final_resume_[timestamp].txt` - 优化后的简历文本
- `final_resume_[timestamp].pdf` - 优化后的简历 PDF
- `final_resume_[timestamp].docx` - 优化后的简历 DOCX

## 📊 输出内容

完整的输出包括：

1. **Agent 1**: 输入验证结果
2. **Agent 2**: JD 分析、匹配度评分、理想候选人画像
3. **Agent 3**: 优化后的项目列表
4. **Agent 4**: 简历优化建议、最终简历、分类后的项目
5. **Agent 5**: 面试准备材料
   - 自我介绍
   - Storytelling 示例
   - Top 10 行为面试问题
   - Top 3 项目深度提问
   - 10 个业务相关问题

## ⚠️ 注意事项

- 运行完整流程需要 3-5 分钟（取决于 API 响应速度）
- 确保 `.env` 文件中配置了正确的 API key
- 如果某个 Agent 失败，脚本会停止并显示错误信息

## 🔍 查看输出

所有输出都以 JSON 格式保存，你可以：

1. 直接查看 JSON 文件
2. 使用 Python 脚本解析和展示
3. 查看 PDF/DOCX 格式的最终简历

---

**准备好数据后，运行 `python3 run_user_complete_workflow.py` 即可开始！**
