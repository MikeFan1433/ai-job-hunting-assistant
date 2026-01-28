# Agent 5 系统提示词总结

## ✅ 已完成

Agent 5（面试准备助手）的系统提示词已创建，整合了所有模版和需求。

## 📋 提示词结构

### 1. 核心使命
- 在简历和项目资料优化后，生成全面的面试准备材料
- 涵盖3个主题：行为面试、项目细节提问、业务侧相关问题

### 2. 输入数据
- 最终优化后的简历
- JD文本
- Agent 2 输出（job_role_team_analysis, ideal_candidate_profile, match_assessment）
- Agent 4 输出（classified_projects）

### 3. 主题一：行为面试

#### 3.1 Self-Introduction
- ✅ 整合了 introduction template
- ✅ 三段式结构（Paragraph 1, 2, 3）
- ✅ 指导如何从简历中提取关键信息
- ✅ 确保与JD要求对齐

#### 3.2 Storytelling 示例
- ✅ 整合了 storytelling 模版（Hook → Emergency → Action → Impact → Reflection）
- ✅ 要求结合具体项目使用模版
- ✅ 优先使用 resume_adopted_projects 中的项目

#### 3.3 Top 10 Behavioral Questions
- ✅ 整合了 TREAT 原则（Tangible, Relatable, Essential, Atypical, Transparent）
- ✅ 每个问题包含：问题、考察原因、样例回复、关键要点
- ✅ 确保所有回答遵循TREAT原则

### 4. 主题二：项目细节提问

#### 4.1 项目选择逻辑
- ✅ 优先级1：使用 resume_adopted_projects（最多3个）
- ✅ 优先级2：如果不够，从简历经历中补充
- ✅ 选择标准：详细描述、技术细节、量化结果、JD对齐

#### 4.2 每个项目的输出
- ✅ 项目全貌回答（STAR格式：Situation, Task, Action, Result）
- ✅ 5个技术细节问题（每个包含：问题、考察原因、作答思路）

### 5. 主题三：业务侧相关问题
- ✅ 基于 Agent 2 的输出生成10个业务问题
- ✅ 每个问题包含：问题、考察原因、作答指导

### 6. 输出格式
- ✅ 完整的JSON结构
- ✅ 包含所有3个主题的详细内容
- ✅ 准备摘要

## 🔍 模版整合确认

### ✅ Introduction Template
- 已整合到 Section 1.1
- 包含三段式结构指导
- 要求根据实际简历内容自由调整

### ✅ Storytelling Template
- 已整合到 Section 1.2
- 包含完整结构：Hook → Emergency → Approach → Action → Impact → Reflection
- 要求结合具体项目示例

### ✅ TREAT Principle
- 已整合到 Section 1.3
- 明确要求所有行为问题回答遵循TREAT原则
- 在输出格式中包含TREAT原则应用说明

### ✅ STAR Format
- 已整合到 Section 2.2.1
- 用于项目全貌回答
- 明确包含：Situation, Task, Action, Result

## 📝 逻辑问题处理

### ✅ 项目选择逻辑
- 明确了优先级：优先使用 resume_adopted_projects
- 提供了fallback机制：从简历经历中补充
- 定义了选择标准

### ✅ 简历解析
- 提示词中说明了如何从简历中提取经历
- 定义了选择详细经历的标准

### ✅ 模版灵活性
- 明确说明模版是指导性的
- 要求根据实际内容自由调整
- 强调使用真实信息，不编造

## 🎯 下一步

1. ✅ 系统提示词已创建
2. ⏳ 实现 Agent 5 的代码逻辑
3. ⏳ 创建测试用例
4. ⏳ 集成到主流程

## ✅ 验证

- ✅ 提示词长度：14,217 字符
- ✅ 包含 storytelling template
- ✅ 包含 TREAT principle
- ✅ 包含 STAR format
- ✅ 包含 introduction template（三段式结构）
- ✅ 包含项目选择逻辑
- ✅ 包含完整的输出格式

所有模版和需求都已成功整合到 Agent 5 的系统提示词中！
