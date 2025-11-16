import argparse
import os
import sys
import time
from datetime import datetime
import pathlib

# Set UTF-8 encoding for stdout to handle Unicode characters
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())

from agents import Runner

from agents_pkg.planner_agent import build_planner_agent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Issue Planner: GPT-5.1-Codex + OpenAI Agents + GitHub CLI + Firecrawl\n"
            "Fully online (no local filesystem) — generates an execution plan for a GitHub issue."
        )
    )
    parser.add_argument(
        "--repo",
        help="GitHub repo in 'owner/name' format (e.g. openai/openai-agents-python).",
    )
    parser.add_argument(
        "--issue",
        type=int,
        help="Issue number to plan for.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    repo = args.repo or input("GitHub repo (owner/name): ").strip()
    issue_number = args.issue or int(input("Issue number: ").strip())

    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is not set")

    agent = build_planner_agent()

    user_prompt = (
        f"You are helping me plan how to implement GitHub issue #{issue_number} "
        f"in repo '{repo}'.\n\n"
        "Be selective and cost-aware:\n"
        "1. Use get_github_issue(repo, issue_number) to understand the problem.\n"
        "2. Based on the issue text, first reason about which directories and components "
        "   are likely relevant.\n"
        "3. Call list_repo_files_gh(repo, extensions=['.py', '.ts', '.js', '.tsx', '.jsx'], "
        "   path_prefixes=[<your inferred prefixes>]) to only explore those areas.\n"
        "4. From those results, choose a small set of the most relevant files and call "
        "   get_repo_file_gh(repo, path=...) on them.\n"
        "5. Optionally, use firecrawl_search and firecrawl_scrape if you need external docs.\n"
        "6. Finally, generate the execution plan in the structured format from your instructions."
    )

    print(
        "\nOnline-only analysis: reading issue, targeted repo structure, and key files "
        "via GitHub CLI, plus Firecrawl research, to generate an execution plan with GPT-5.1-Codex...\n"
    )

    print("🔍 Starting analysis with interactive progress...")
    print(f"📍 Repository: {repo}")
    print(f"🔢 Issue Number: {issue_number}")
    print()
    
    # Show progress steps
    steps = [
        "📖 Reading GitHub issue details...",
        "🔍 Analyzing repository structure...",
        "📂 Exploring relevant code files...",
        "🌐 Searching for external documentation (if needed)...",
        "🧠 Processing information and reasoning...",
        "📝 Generating execution plan..."
    ]
    
    for i, step in enumerate(steps, 1):
        print(f"[{i}/{len(steps)}] {step}", end="", flush=True)
        
        # Add a small delay to simulate progress
        import time
        time.sleep(0.5)
        
        print(" ✅")
    
    print("\n🔄 Running AI analysis...")
    print("📝 Streaming response as it's generated...\n")
    
    # Create output directory and file path
    output_dir = pathlib.Path("output")
    output_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    markdown_file = output_dir / f"execution_plan_{repo.replace('/', '_')}_issue_{issue_number}_{timestamp}.md"
    
    # Simple sync run – no session/memory needed for this CLI
    result = Runner.run_sync(
        agent,
        input=user_prompt,
        context={"repo": repo, "issue_number": issue_number},
    )

    # Display and save the execution plan
    print("\n" + "="*50)
    print("📋 EXECUTION PLAN")
    print("="*50)
    
    # Stream the output
    output_lines = result.final_output.split('\n')
    for line in output_lines:
        print(line)
        time.sleep(0.02)  # Small delay for streaming effect
    
    print("="*50)
    print("✅ Analysis complete!")
    
    # Save to markdown file
    print(f"\n💾 Saving execution plan to: {markdown_file}")
    
    with open(markdown_file, 'w', encoding='utf-8') as f:
        f.write(f"# GitHub Issue Analysis: {repo}#{issue_number}\n\n")
        f.write(f"**Generated on:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**Repository:** {repo}\n")
        f.write(f"**Issue Number:** {issue_number}\n\n")
        f.write("---\n\n")
        f.write(result.final_output)
    
    print(f"✅ Execution plan saved to {markdown_file}")


if __name__ == "__main__":
    main()
