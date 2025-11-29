# LCA-LLM: 智能生命周期评估分析系统

<div align="center">

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

*基于大语言模型的智能化生命周期评估(LCA)分析平台*

[项目现状](#-项目现状) • [快速开始](#-快速开始) • [专家工作台](#-专家工作台) • [开发计划](#-开发计划) • [文档](#-文档)

</div>

## 🎯 项目概述

LCA-LLM是一个创新的生命周期评估分析系统，旨在通过大语言模型(LLM)实现完全自动化的PDF文档分析、LCI数据提取、LCA模型构建和pyLCA代码生成。

**当前状态：第一阶段 - LLM工具调用能力训练**

第一阶段的目标是让LLM学会灵活调用当前的工具，读取用户上传的文档并检索关键量化信息，为后续阶段的LCA模型蓝图构建、pyLCA代码生成等功能打下坚实基础。

### 项目愿景

- 🤖 **智能文档理解**: 基于微调LLM的深度PDF文档分析
- 🔍 **语义搜索**: 向量数据库驱动的智能信息检索  
- 🛠️ **工具调用**: LLM自主驱动的7工具链完整LCA分析流程
- 🗄️ **LCI数据库**: 直接访问标准生命周期清单数据
- 🏗️ **自动建模**: 基于提取数据自动构建LCA系统
- 💻 **对话界面**: 智能LCA分析助手，支持自然语言交互

## 📊 项目现状

### 🏗️ 第一阶段：LLM工具调用能力训练 (当前)

**核心目标**: 构建高质量训练数据集，让LLM学会智能使用工具链从PDF文档中提取LCA相关的量化信息。

#### ✅ 已完成功能

**🛠️ 核心工具链 (9个工具)**
- **🎯 define_lca_scope**: 定义LCA范围参数（功能单位、系统边界、影响类别）
- **🔄 record_process_flow**: 记录工艺流数据（输入/输出/排放，完备分类体系）
- **📝 record_parameter**: 从文档提取原始参数（三工具架构第一步）
- **🧮 record_calculation**: 执行纯数学运算（三工具架构第二步，Calculate & Verify工作流）
- **📊 get_session_summary**: 获取会话总结和数据完整性评估
- **📄 process_document**: PDF文档处理和表格感知分块
- **🔍 search_document**: 语义搜索文档内容（支持批量搜索 🆕）
- **🗃️ search_lci_database**: 搜索标准LCI数据库
- **🏗️ build_lca_system**: 构建完整LCA系统（第二阶段功能）

**📄 智能文档处理**
- **PDF解析**: 自动提取文本和表格内容
- **表格感知分块**: 使用pdfplumber识别表格，支持table_section策略和header repetition
- **语义向量化**: ChromaDB驱动的向量搜索，all-MiniLM-L6-v2嵌入模型
- **会话隔离**: 每个session独立的临时数据存储

**📊 专家决策追踪与学习**
- **完整决策链**: 通过link_to机制构建动作依赖关系，支持四种依赖场景
- **Pivot Query系统**: 独立记录搜索失败动作，捕获复杂负样本用于LLM学习
- **三工具架构**: Parameter → Calculation → Flow，清晰分离数据提取、计算和记录流程
  - **record_parameter**: 从文档提取原始参数值（需要上下文）
  - **record_calculation**: 执行纯数学运算（无需上下文，通过rationale建立数据依赖）
  - **record_process_flow**: 记录最终结果（可选上下文，Rule 4自动链接计算结果）
- **计算工具系统**: Calculate & Verify两步工作流，SafeCalculator安全执行数学表达式
- **MongoDB存储**: 统一lca_actions集合，完整记录专家决策过程和数据溯源

## 🚀 快速开始

### 环境要求

- **操作系统**: Linux (推荐 Ubuntu 20.04+)
- **Python**: 3.8+
- **内存**: 16GB+ RAM
- **存储**: 20GB+ 可用空间

### 安装步骤

1. **克隆项目**
```bash
git clone <repository-url>
cd LCA-LLM
```

2. **创建虚拟环境**
```bash
python -m venv lcaLLM
source lcaLLM/bin/activate
```

3. **安装依赖**
```bash
pip install -r requirements.txt
```

4. **启动MongoDB**
```bash
sudo systemctl start mongod
```

5. **启动服务**
```bash
./start_services.sh
```

### 访问界面

- **🎯 最终用户界面**: http://localhost:8051 (开发中 - 集成微调后的LLM)
- **👨‍🔬 专家标注工作台**: http://localhost:8504 (当前主要使用 - 数据集生成)
- **🧪 工具集成测试**: http://localhost:8503 (功能测试)
- **📋 API文档**: http://localhost:8000/docs
- **🗄️ MongoDB**: mongodb://localhost:27017

## 👨‍🔬 专家工作台

**专业的智能决策追踪平台，实现Expert Workbench Decision Logic Schema v1.3规范**

这是第一阶段的核心工作平台，不仅用于生成高质量的LLM训练数据，更实现了完整的专家决策逻辑追踪、智能特征提取和动作链管理。专家的每个决策都被完整记录，形成可追溯的决策链条。

### 🎯 启动工作台

```bash
# 启动专家标注工作台
./scripts/expert_workbench.sh

# 访问地址: http://localhost:8504
```

### 🏗️ 三栏式布局

```
┌────────────────────┬──────────────────────┬──────────────────┐
│ [A] 会话与实时摘要  │ [B] 文档与智能搜索    │ [C] 统一提取工具  │
│                    │                      │                  │
│ - 会话状态管理      │ - 文档上传处理        │ - LCA范围定义     │
│ - 实时数据摘要      │ - 智能语义搜索        │ - 工艺流程记录    │
│ - 提取操作日志      │ - 搜索结果展示        │ - 智能rationale   │
│ - 决策链追踪       │ - 上下文管理         │ - 动作链追踪      │
└────────────────────┴──────────────────────┴──────────────────┘
```

### ✨ 核心特性

**🔗 专家决策追踪**
- 递增action_id生成（ACT_0001, ACT_0002...）
- 完整决策链构建（link_to机制，支持四种依赖场景）
- 四种意图类型：select_best, refine_same, pivot_query, calculate
- Pivot Query独立记录：立即记录失败动作，构建失败-成功学习链
- Calculate & Verify工作流：两步计算验证，确保数据准确性

**💡 智能Rationale系统**
- refine_same自动模板生成
- 可选备注支持（|| note: 格式）
- 训练友好的正则解析

### 🔄 核心工作流程

1. **文档处理** (栏目B): 上传PDF文档，系统自动分析和向量化
2. **智能搜索** (栏目B): 语义搜索文档内容，找到相关信息片段  
3. **设置上下文** (栏目B): 选择文本片段作为数据提取的上下文
4. **数据提取** (栏目C): 选择合适工具提取LCA范围、工艺流程或计算数据
5. **计算验证** (栏目C): 使用Calculate & Verify工作流记录数学计算
6. **监控进度** (栏目A): 实时查看摘要、日志和会话状态


### 第一阶段架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ 专家标注工作台   │    │    FastAPI      │    │    MongoDB      │
│ (Port 8504)     │◄──►│    后端API      │◄──►│   训练数据      │
│ 数据集生成器     │    │   7工具链       │    │   持久存储      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │
         │                       ▼
         │              ┌─────────────────┐
         │              │    ChromaDB     │
         └─────────────►│  临时向量存储    │
                        │   (会话隔离)    │
                        └─────────────────┘
                        
┌─────────────────┐              ┌─────────────────┐
│   最终用户界面   │              │   数据导出脚本   │
│ (Port 8051)     │              │ (dataset_exporter)│
│   开发中...     │              │   开发中...     │
└─────────────────┘              └─────────────────┘
```

## 📚 文档

### 核心文档

- [⚡ 专家工作台快速开始](docs/Expert_Workbench_Quick_Start.md) - 5分钟快速上手指南
- [📖 专家工作台完整指南](docs/Expert_Workbench_Guide.md) - 详细的功能说明和使用方法
- [🔧 专家工作台技术指南](docs/Expert_Workbench_Technical_Guide.md) - 系统架构和技术实现
- [📊 Session Summary功能指南](docs/Session_Summary_Guide.md) - 会话总结和工作记忆系统（含Text格式优化）
- [🤖 LLM工具调用参考手册](docs/LLM_Tools_Reference.md) - LLM Agent的完整工具使用指南
- [🧮 计算工具使用指南](docs/Calculation_Tool_Guide.md) - Calculate & Verify工作流详解
- [🔍 批量搜索功能指南](docs/Batch_Search_Implementation.md) - 并行搜索多关键词功能 🆕
- [🛠️ 工具使用指南](docs/TOOLS_USAGE_GUIDE.md) - 各工具的详细使用方法  
- [🏗️ 系统架构文档](docs/system_architecture.md) - 技术架构详解

### 专业指南

- [🗄️ MongoDB连接池指南](docs/mongodb_connection_pool_guide.md) - 数据库连接管理和优化
- [🔧 ChromaDB会话隔离](docs/ChromaDB_Session_Isolation_Fix_Summary.md) - 会话数据隔离技术

## 🧪 开发和测试

### 测试界面

```bash
# 启动功能测试界面
./scripts/tools_integration_test_simple.sh

# 访问地址: http://localhost:8503
```

### 调试工具

```bash
# 测试API端点
python scripts/test_process_flow_api.py

# 测试表格感知分块
python scripts/test_table_aware_chunking.py

# 测试会话隔离
python scripts/test_session_isolation.py
```

## 🗺️ 开发计划

### 🏗️ 第一阶段 (当前) - LLM工具调用能力训练
- ✅ **核心工具链**: 9个工具完整实现
- ✅ **专家工作台**: 三栏式数据集生成器  
- ✅ **数据溯源**: search_context + selected_chunk
- ✅ **会话隔离**: ChromaDB临时存储机制
- ✅ **计算工具系统**: Calculate & Verify工作流，SafeCalculator安全执行
- ✅ **Session Summary优化**: Text格式 (节省80% tokens)
- ✅ **Summary Check记录**: 专家回顾动作追踪，支持SRL训练数据生成
- ✅ **文档上下文注入**: 自动提取标题增强LLM初始理解
- ✅ **Chunk ID统一**: 纯数字格式 (0, 1, 2...)
- ✅ **API标准化**: 统一连字符命名约定
- ✅ **批量搜索功能**: 单次调用并行搜索多关键词，智能去重，节省60% tokens 🆕
- ✅ **数据格式一致性**: search_query支持字符串/数组，确保训练数据与推理格式匹配 🆕
- 🔄 **数据导出脚本**: SRL训练数据生成 (开发中)
- 🔄 **LLM微调**: 工具调用能力训练 (计划中)

### 🤖 第二阶段 - LLM自动化分析
- 📋 **智能对话界面**: 最终用户界面 (Port 8051)
- 📋 **自动工具调用**: 微调后LLM驱动的分析流程
- 📋 **LCA模型构建**: 自动生成LCA系统蓝图
- 📋 **pyLCA代码生成**: 完整可执行的LCA分析代码

### 🚀 第三阶段 - 完整LCA平台
- 📋 **批量处理**: 大规模文档自动化分析
- 📋 **结果可视化**: LCA结果图表和报告生成
- 📋 **多语言支持**: 国际化LCA分析能力


## 🤝 贡献指南

欢迎提交Issue和Pull Request来帮助改进项目。当前重点关注：
- 专家工作台功能改进
- 训练数据质量提升  
- 工具链优化建议

## 📄 许可证

本项目采用MIT许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

---

<div align="center">

**LCA-LLM** - 基于大语言模型的智能生命周期评估分析系统

*第一阶段：让LLM学会智能使用工具链从PDF文档中提取LCA数据*

</div>
