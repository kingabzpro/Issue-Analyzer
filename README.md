# Issue Analyzer
AI-Powered GitHub Issue Analysis and Execution Planning

A sophisticated tool that leverages GPT-5.1 Codex, OpenAI Agents, GitHub CLI, and Firecrawl to automatically analyze GitHub issues and generate detailed execution plans for resolving them.

## Features

- **Intelligent Issue Analysis**: Automatically reads and understands GitHub issues using AI
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

## Output

The tool generates comprehensive execution plans including:
- **Issue Summary**: Clear understanding of the problem
- **Project Context**: Where the issue fits in the architecture
- **Key Files**: Specific files and components that need modification
- **Step-by-Step Plan**: Detailed implementation steps
- **Testing Strategy**: Unit, integration, and manual testing approaches
- **Risk Assessment**: Edge cases, potential issues, and open questions

Results are saved to `output/execution_plan_{repo}_{issue}_{timestamp}.md`

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
- **OpenAI Agents**: AI-powered workflow orchestration
- **GPT-5.1 Codex**: Advanced code analysis and generation
- **GitHub CLI**: Repository access and file operations
- **Firecrawl**: Web scraping and documentation retrieval

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
