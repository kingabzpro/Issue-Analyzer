# Issue Analyzer
AI-Powered GitHub Issue Analysis and Execution Planning

A sophisticated tool that leverages GPT-5.1 Codex, OpenAI Agents, GitHub CLI, and Firecrawl to automatically analyze GitHub issues and generate detailed execution plans for resolving them.

## Features

- **Intelligent Issue Analysis**: Automatically reads and understands GitHub issues using AI
- **Real-Time Streaming Output**: Watch the AI agent work in real-time with live progress updates
- **Tool Call Tracking**: See exactly which tools are being used and their progress
- **Reasoning Display**: Observe the agent's reasoning process as it analyzes the issue
- **Targeted Repository Exploration**: Smart analysis of relevant code files without scanning entire projects
- **External Documentation Research**: Integrated Firecrawl web scraping for framework/library documentation
- **Cost-Optimized Approach**: Selective file inspection to minimize API costs and maximize efficiency
- **Structured Execution Plans**: Generates comprehensive, actionable implementation plans
- **Professional Output**: Saves detailed analysis as markdown files with timestamps

## Architecture

The Issue Analyzer consists of several key components:

### Core Components
- **src/app.py**: Main application interface with CLI capabilities
- **src/agents_pkg/planner_agent.py**: AI agent that orchestrates the analysis process
- **src/tools/github_tools.py**: GitHub CLI integration tools
- **src/tools/firecrawl_tools.py**: Web scraping and documentation retrieval tools

### AI Agent System
The planner agent follows a sophisticated workflow:
1. Reads and analyzes the GitHub issue
2. Infers relevant project components and directories
3. Performs targeted repository file exploration
4. Selectively inspects key implementation files
5. Researches external documentation when needed
6. Generates comprehensive execution plans

The agent uses **real-time streaming** to provide immediate feedback:
- **Streaming Events**: Token-by-token text generation for instant results
- **Progress Tracking**: Numbered tool calls show execution order
- **Reasoning Visibility**: See the agent's decision-making process
- **Live Updates**: All output streams in real-time without waiting for completion

## Installation

### Prerequisites
- Python 3.8+
- GitHub CLI (gh)
- OpenAI API key
- Firecrawl API access

### Setup
1. Clone the repository:
```bash
git clone https://github.com/kingabzpro/Issue-Analyzer.git
cd Issue-Analyzer
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
export OPENAI_API_KEY="your_openai_api_key"
export FIRECRAWL_API_KEY="your_firecrawl_api_key"
```

## Usage

### Command Line Interface
```bash
python src/app.py --repo owner/repository --issue 123
```

### Interactive Mode
```bash
python src/app.py
```
Then enter the repository and issue number when prompted.

### Example
```bash
python src/app.py --repo openai/openai-agents-python --issue 456
```

### Real-Time Output

The tool provides real-time streaming output showing:
- **💭 Reasoning**: The agent's thought process as it analyzes the issue
- **🔧 Calling**: Tool calls with arguments (e.g., `get_github_issue → repo#issue`)
- **Live Text Streaming**: Token-by-token generation of the execution plan
- **Tool Summary**: Complete list of all tools used during analysis

Example output:
```
🔍 Analyzing owner/repo#123...

💭 Reasoning: I need to understand the issue first...

[1] 🔧 Calling: get_github_issue → owner/repo#123...

💭 Reasoning: Based on the issue, I should explore the src/ directory...

[2] 🔧 Calling: list_repo_files_gh → ext=['.py'], paths=['src/']...

[3] 🔧 Calling: get_repo_file_gh → src/main.py...

[Execution plan text streams here in real-time...]

---
📊 Tools used (5): get_github_issue, list_repo_files_gh, get_repo_file_gh, firecrawl_search, firecrawl_scrape
```

## Output

The tool generates comprehensive execution plans including:
- **Issue Summary**: Clear understanding of the problem
- **Project Context**: Where the issue fits in the architecture
- **Key Files**: Specific files and components that need modification
- **Step-by-Step Plan**: Detailed implementation steps
- **Testing Strategy**: Unit, integration, and manual testing approaches
- **Risk Assessment**: Edge cases, potential issues, and open questions

### Output Format

Results are saved to `output/execution_plan_{repo}_{issue}_{timestamp}.md`

The console output includes:
- Real-time streaming of the execution plan as it's generated
- Tool call progress with numbered tracking
- Reasoning steps showing the agent's thought process
- Summary of all tools used during analysis

## Development

### Project Structure
```
src/
├── app.py                 # Main application entry point
├── agents_pkg/
│   ├── __init__.py
│   └── planner_agent.py   # AI planning agent
└── tools/
    ├── firecrawl_tools.py # Web scraping tools
    └── github_tools.py    # GitHub CLI integration
```

### Key Technologies
- **OpenAI Agents**: AI-powered workflow orchestration with streaming support
- **GPT-5.1 Codex**: Advanced code analysis and generation
- **GitHub CLI**: Repository access and file operations
- **Firecrawl**: Web scraping and documentation retrieval
- **Real-Time Streaming**: Live event streaming for immediate feedback

### Recent Improvements
- ✅ Real-time streaming output with token-by-token generation
- ✅ Tool call progress tracking with numbered display
- ✅ Reasoning visibility to see agent decision-making
- ✅ Improved error handling and fallback mechanisms
- ✅ Cleaner, more informative console output
