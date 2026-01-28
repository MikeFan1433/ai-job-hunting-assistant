# Agent 5 需求分析与逻辑检查

## 📋 需求总结

Agent 5（面试准备助手）需要在简历和项目资料都完成优化后，根据全部资料生成面试相关问题的建议。

### 输入数据
1. 修改后的简历（final_resume）
2. JD文本
3. Agent 2 输出：
   - `job_role_team_analysis`（工作场景、团队目标）
   - `ideal_candidate_profile`（候选人画像）
   - `match_assessment`（匹配度分析）
4. Agent 4 输出：
   - `classified_projects`（分类后的项目文本）
     - `resume_adopted_projects`（简历采纳的项目）
     - `resume_not_adopted_projects`（简历不采纳的项目）

### 输出内容（3个主题）

**主题一：行为面试**
1. Self-introduction（基于 introduction template）
2. Storytelling 回答模版（结合具体项目示例）
3. Top 10 behavioral questions（每个包含考察原因和样例回复）

**主题二：项目细节提问**
1. Top 3 项目选择（优先从 resume_adopted_projects，不够则从简历经历补充）
2. 每个项目：
   - 讲述项目全貌的样例回答（STAR法则，简短）
   - 5个技术细节问题（提问原因 + 作答思路）

**主题三：业务侧相关问题**
- 10个业务相关问题（基于 Agent 2 的匹配度分析、画像和工作场景）

---

## 🔍 逻辑问题分析

### ✅ 1. 项目文本来源 - 已解决
- **优先级明确**：优先使用 `resume_adopted_projects`
- **Fallback机制**：如果采纳项目少于3个，从简历经历中补充
- **实现方式**：Agent 5 需要能够解析简历，提取经历描述

### ⚠️ 2. 项目选择逻辑 - 需要明确
- **问题**：如何从简历经历中"挑选饱满的经历"？
- **建议**：
  - 优先选择有详细描述的经历（bullet points 数量多、包含技术细节）
  - 优先选择与JD要求相关的经历
  - 如果简历经历也不够，可以提示用户需要更多项目材料

### ✅ 3. 模版使用 - 已明确
- Introduction template：指导性模版，需要根据简历和JD自由调整
- Storytelling 模版：Hook → Emergency → Action → Impact → Reflection
- BQ template：TREAT原则（Tangible, Relatable, Essential, Atypical, Transparent）

### ✅ 4. 输出格式 - 需要结构化
- 需要JSON格式输出，包含3个主题的所有内容
- 每个部分都需要详细的样例和指导

---

## 🛠️ 技术实现建议

### 1. 项目选择逻辑
```python
def select_top_projects_for_interview():
    # 1. 优先使用 resume_adopted_projects（最多3个）
    # 2. 如果不够3个，从简历经历中补充
    # 3. 选择标准：
    #    - 经历描述详细（bullet points >= 3）
    #    - 包含技术细节
    #    - 与JD要求相关
```

### 2. 简历解析
- 需要解析简历文本，提取工作经历
- 识别每个经历的标题、公司、时间、描述

### 3. 模版应用
- Introduction template：需要提取简历中的关键信息（姓名、当前角色、公司、经验年限、核心技能、项目等）
- Storytelling 模版：需要结合具体项目的完整信息（从项目文本中提取）
- BQ template：确保所有行为问题回答都遵循TREAT原则

---

## ✅ 确认：需求逻辑合理

经过分析，需求逻辑是合理的，但需要注意：

1. **项目选择**：需要实现智能选择逻辑（优先采纳项目，不够则从简历补充）
2. **简历解析**：需要能够解析简历文本，提取经历
3. **模版灵活性**：模版是指导性的，需要根据具体内容自由调整

---

## 📝 下一步

1. 创建 Agent 5 的系统提示词
2. 实现 Agent 5 的代码逻辑
3. 创建测试用例
