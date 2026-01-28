# AI Job Hunting Assistant - Workflow Diagram (Mermaid)

## 完整应用工作流程图

```mermaid
flowchart TD
    Start([用户开始]) --> Input[用户输入<br/>• Resume Text<br/>• JD Text<br/>• Project Materials]
    
    Input --> Agent1[Agent 1: 输入验证<br/>InputValidationAgent]
    
    Agent1 --> Valid{验证通过?}
    Valid -->|否| Fix[用户修复问题]
    Fix --> Agent1
    Valid -->|是| Agent2[Agent 2: JD 分析与匹配<br/>JDAnalysisAgent]
    
    Agent2 --> A2Output[输出:<br/>• job_role_team_analysis<br/>• ideal_candidate_profile<br/>• match_assessment<br/>• improvement_recommendations]
    
    A2Output --> Agent3[Agent 3: 项目包装<br/>ProjectPackagingAgent]
    
    Agent3 --> A3Output[输出:<br/>• selected_projects<br/>• 5-part framework<br/>• optimized_version]
    
    A3Output --> Agent4[Agent 4: 简历优化<br/>ResumeOptimizationAgent]
    
    Agent4 --> A4Output[输出:<br/>• experience_replacements<br/>• format_content_adjustments<br/>• project_classification]
    
    A4Output --> Feedback[用户反馈循环<br/>Accept/Reject/Modify]
    
    Feedback --> Service[Resume Optimization Service<br/>处理反馈并生成最终简历]
    
    Service --> Final[最终输出:<br/>• final_resume<br/>• classified_projects]
    
    Final --> Agent5[Agent 5: 面试准备<br/>InterviewPreparationAgent]
    
    Agent5 --> A5Output[输出:<br/>• Theme 1: 行为面试<br/>• Theme 2: 项目深度提问<br/>• Theme 3: 业务问题]
    
    A5Output --> Export[导出功能<br/>• PDF Resume<br/>• DOCX Resume]
    
    Export --> End([完成])
    
    style Start fill:#90EE90
    style End fill:#FFB6C1
    style Agent1 fill:#87CEEB
    style Agent2 fill:#87CEEB
    style Agent3 fill:#87CEEB
    style Agent4 fill:#87CEEB
    style Agent5 fill:#87CEEB
    style Valid fill:#FFD700
    style Feedback fill:#FFA500
    style Final fill:#98FB98
```

## 数据流图

```mermaid
graph LR
    subgraph Input["用户输入"]
        R[Resume]
        J[JD]
        P[Projects]
    end
    
    subgraph Agents["Agent 工作流"]
        A1[Agent 1<br/>Validation]
        A2[Agent 2<br/>Analysis]
        A3[Agent 3<br/>Packaging]
        A4[Agent 4<br/>Optimization]
        A5[Agent 5<br/>Interview Prep]
    end
    
    subgraph Services["服务层"]
        ROS[Resume<br/>Optimization<br/>Service]
        RE[Resume<br/>Export]
    end
    
    subgraph Output["最终输出"]
        FR[Final Resume]
        CP[Classified<br/>Projects]
        IP[Interview<br/>Prep Materials]
    end
    
    R --> A1
    J --> A1
    P --> A1
    
    A1 -->|valid| A2
    A2 --> A3
    A3 --> A4
    A4 --> ROS
    ROS --> A5
    A5 --> RE
    
    ROS --> FR
    ROS --> CP
    A5 --> IP
    
    RE --> FR
```

## Agent 详细流程

```mermaid
flowchart TB
    subgraph A1["Agent 1: 输入验证"]
        A1I[输入: Resume + Projects] --> A1V[验证完整性]
        A1V --> A1O[输出: is_valid + issues]
    end
    
    subgraph A2["Agent 2: JD 分析"]
        A2I[输入: JD + Resume + Projects] --> A2A[JD 深度分析]
        A2A --> A2P[创建理想候选人画像]
        A2P --> A2M[匹配度评估 0-5分]
        A2M --> A2O[输出: analysis + recommendations]
    end
    
    subgraph A3["Agent 3: 项目包装"]
        A3I[输入: Projects + Agent2 Output] --> A3S[选择 Top 5 项目]
        A3S --> A3F[5-part 框架重构]
        A3F --> A3E[内容补充与优化]
        A3E --> A3O[输出: optimized_projects]
    end
    
    subgraph A4["Agent 4: 简历优化"]
        A4I[输入: Resume + Agent2/3 Output] --> A4R[经历替换分析]
        A4R --> A4F[格式内容调整]
        A4F --> A4C[项目分类]
        A4C --> A4O[输出: recommendations]
        A4O --> A4U[用户反馈]
        A4U --> A4G[生成最终简历]
    end
    
    subgraph A5["Agent 5: 面试准备"]
        A5I[输入: Final Resume + Agent2/4 Output] --> A5B[Theme 1: 行为面试]
        A5I --> A5P[Theme 2: 项目深度]
        A5I --> A5D[Theme 3: 业务问题]
        A5B --> A5O[输出: interview_prep]
        A5P --> A5O
        A5D --> A5O
    end
    
    A1O --> A2I
    A2O --> A3I
    A3O --> A4I
    A4G --> A5I
```

## 用户反馈循环

```mermaid
sequenceDiagram
    participant U as 用户
    participant A4 as Agent 4
    participant S as Resume Service
    participant A5 as Agent 5
    
    A4->>U: 显示优化建议
    U->>S: 提交反馈 (Accept/Reject/Modify)
    S->>S: 处理反馈
    S->>U: 显示更新后的简历
    U->>U: 确认修改
    U->>S: 确认最终简历
    S->>A5: 触发面试准备
    A5->>U: 返回面试材料
```

## 项目分类流程

```mermaid
flowchart LR
    A3[Agent 3<br/>Optimized Projects] --> A4[Agent 4<br/>Replacement Analysis]
    
    A4 --> Classify{项目分类}
    
    Classify -->|用于替换| Adopted[简历采纳项目<br/>resume_adopted_projects]
    Classify -->|不用于替换| NotAdopted[简历不采纳项目<br/>resume_not_adopted_projects]
    
    Adopted --> Resume[转换为简历经历]
    NotAdopted --> Interview[保留完整细节<br/>用于面试准备]
    
    Resume --> A5[Agent 5<br/>面试准备]
    Interview --> A5
```

## 面试准备主题结构

```mermaid
graph TD
    A5[Agent 5: Interview Prep] --> T1[Theme 1: 行为面试]
    A5 --> T2[Theme 2: 项目深度]
    A5 --> T3[Theme 3: 业务问题]
    
    T1 --> T1A[Self-Introduction<br/>3 paragraphs]
    T1 --> T1B[Storytelling<br/>Hook→Emergency→Action→Impact→Reflection]
    T1 --> T1C[Top 10 Behavioral Q&A<br/>TREAT Principle]
    
    T2 --> T2A[Top 3 Projects]
    T2 --> T2B[STAR Overview<br/>per project]
    T2 --> T2C[5 Technical Questions<br/>per project]
    
    T3 --> T3A[10 Business Questions<br/>Based on Agent 2 Analysis]
```

## 完整系统架构

```mermaid
graph TB
    subgraph Frontend["前端 (待实现)"]
        UI[User Interface]
    end
    
    subgraph Backend["后端 API"]
        API[FastAPI Endpoints]
    end
    
    subgraph Agents["Agent 层"]
        A1[Agent 1]
        A2[Agent 2]
        A3[Agent 3]
        A4[Agent 4]
        A5[Agent 5]
    end
    
    subgraph Services["服务层"]
        ROS[Resume Optimization<br/>Service]
        RE[Resume Export<br/>Service]
    end
    
    subgraph External["外部服务"]
        LLM[Student Portal API<br/>LLM Service]
    end
    
    UI --> API
    API --> A1
    API --> A2
    API --> A3
    API --> A4
    API --> A5
    API --> ROS
    API --> RE
    
    A1 --> LLM
    A2 --> LLM
    A3 --> LLM
    A4 --> LLM
    A5 --> LLM
    
    A4 --> ROS
    ROS --> A5
    ROS --> RE
```

---

**Note**: 这些 Mermaid 图表可以在支持 Mermaid 的 Markdown 查看器中渲染（如 GitHub, GitLab, VS Code with Mermaid extension 等）。
