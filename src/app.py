import argparse
import asyncio
import json
import os
import pathlib
import sys
import threading
import time
from datetime import datetime
from queue import Queue

# Set UTF-8 encoding for stdout to handle Unicode characters
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())

from agents import Runner, ItemHelpers
from openai.types.responses import ResponseTextDeltaEvent

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


async def main() -> None:
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

    # Create output directory and file path
    output_dir = pathlib.Path("output")
    output_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    markdown_file = output_dir / f"execution_plan_{repo.replace('/', '_')}_issue_{issue_number}_{timestamp}.md"
    
    print(f"\n🔍 Analyzing {repo}#{issue_number}...\n")
    
    async def run_agent_async():
        try:
            final_output = ""
            active_tools = {}  # Track active tool calls by ID
            tool_counter = 0
            completed_tools = []
            first_event_received = False
            
            # Run agent with streaming (run_streamed is synchronous, returns immediately)
            result = Runner.run_streamed(
                agent,
                input=user_prompt,
                context={"repo": repo, "issue_number": issue_number},
            )
            
            # Stream the events as they come in
            async for event in result.stream_events():
                # Handle raw response events (token-by-token streaming) - print immediately
                if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
                    if not first_event_received:
                        first_event_received = True
                    delta = event.data.delta
                    print(delta, end="", flush=True)
                    final_output += delta
                # Handle run item events (higher level updates)
                elif event.type == "run_item_stream_event":
                    # Debug: print event item type to see what we're getting
                    item_type = getattr(event.item, 'type', 'unknown')
                    
                    # Show reasoning events
                    if item_type == "reasoning_item":
                        # Try to get reasoning text from various possible locations
                        reasoning_text = None
                        
                        if hasattr(event.item, 'raw_item'):
                            raw = event.item.raw_item
                            # Try multiple attribute names
                            for attr_name in ['content', 'text', 'reasoning', 'message', 'delta']:
                                if hasattr(raw, attr_name):
                                    val = getattr(raw, attr_name)
                                    if val and str(val).strip() and str(val) != 'None':
                                        reasoning_text = str(val)
                                        break
                            
                            # If still not found, try to access as dict-like
                            if not reasoning_text:
                                try:
                                    if hasattr(raw, '__dict__'):
                                        for key, val in raw.__dict__.items():
                                            if val and str(val).strip() and str(val) != 'None' and key in ['content', 'text', 'reasoning', 'message', 'delta']:
                                                reasoning_text = str(val)
                                                break
                                except:
                                    pass
                        
                        # Also try direct attributes on event.item
                        if not reasoning_text:
                            for attr_name in ['content', 'text', 'reasoning', 'message']:
                                if hasattr(event.item, attr_name):
                                    val = getattr(event.item, attr_name)
                                    if val and str(val).strip() and str(val) != 'None':
                                        reasoning_text = str(val)
                                        break
                        
                        if reasoning_text and reasoning_text.strip():
                            # Show first line or first 100 chars
                            first_line = reasoning_text.split('\n')[0].strip()[:100]
                            if len(reasoning_text.split('\n')[0].strip()) > 100:
                                first_line += "..."
                            print(f"\n💭 Reasoning: {first_line}", flush=True)
                        else:
                            # Don't show "None" - just show that reasoning is happening
                            print(f"\n💭 Reasoning...", flush=True)
                    
                    elif item_type == "tool_call_item":
                        # Try multiple ways to get tool name and ID
                        tool_name = None
                        tool_id = None
                        
                        # First try raw_item which contains the actual tool call data
                        if hasattr(event.item, 'raw_item'):
                            raw = event.item.raw_item
                            # Try accessing tool_call through various paths
                            tool_call = None
                            if hasattr(raw, 'tool_call'):
                                tool_call = raw.tool_call
                            elif hasattr(raw, 'function_call'):
                                tool_call = raw.function_call
                            
                            if tool_call:
                                # Try to get name from tool_call
                                if hasattr(tool_call, 'name'):
                                    tool_name = tool_call.name
                                elif hasattr(tool_call, 'function') and hasattr(tool_call.function, 'name'):
                                    tool_name = tool_call.function.name
                                # Try to get ID
                                if hasattr(tool_call, 'id'):
                                    tool_id = tool_call.id
                                elif hasattr(tool_call, 'tool_call_id'):
                                    tool_id = tool_call.tool_call_id
                            
                            # Fallback: try direct attributes on raw
                            if not tool_name:
                                if hasattr(raw, 'name'):
                                    tool_name = getattr(raw, 'name')
                                elif hasattr(raw, 'function') and hasattr(raw.function, 'name'):
                                    tool_name = raw.function.name
                                # Try using getattr with different possible attribute names
                                for attr_name in ['tool_name', 'function_name', 'name']:
                                    if hasattr(raw, attr_name):
                                        tool_name = getattr(raw, attr_name, None)
                                        if tool_name:
                                            break
                        
                        # Fallback to direct attributes
                        if not tool_name and hasattr(event.item, 'tool_call'):
                            tool_call = event.item.tool_call
                            if hasattr(tool_call, 'name'):
                                tool_name = tool_call.name
                            if hasattr(tool_call, 'id'):
                                tool_id = tool_call.id
                            elif hasattr(tool_call, 'function') and hasattr(tool_call.function, 'name'):
                                tool_name = tool_call.function.name
                        if not tool_name and hasattr(event.item, 'name'):
                            tool_name = event.item.name
                        if not tool_name and hasattr(event.item, 'function'):
                            func = event.item.function
                            if hasattr(func, 'name'):
                                tool_name = func.name
                        
                        if tool_name:
                            tool_counter += 1
                            tool_id = tool_id or f"tool_{tool_counter}"
                            active_tools[tool_id] = tool_name
                            
                            # Get tool arguments if available
                            tool_args = ""
                            tool_call_obj = None
                            
                            # Try to get tool_call object from raw_item first
                            if hasattr(event.item, 'raw_item') and hasattr(event.item.raw_item, 'tool_call'):
                                tool_call_obj = event.item.raw_item.tool_call
                            elif hasattr(event.item, 'tool_call'):
                                tool_call_obj = event.item.tool_call
                            
                            if tool_call_obj and hasattr(tool_call_obj, 'arguments'):
                                try:
                                    args_dict = json.loads(tool_call_obj.arguments) if isinstance(tool_call_obj.arguments, str) else tool_call_obj.arguments
                                    if 'repo' in args_dict:
                                        tool_args = f" → {args_dict['repo']}"
                                        if 'issue_number' in args_dict:
                                            tool_args += f"#{args_dict['issue_number']}"
                                    elif 'path' in args_dict:
                                        tool_args = f" → {args_dict['path']}"
                                    elif 'query' in args_dict:
                                        q = str(args_dict['query'])
                                        tool_args = f" → {q[:40]}..." if len(q) > 40 else f" → {q}"
                                    elif 'url' in args_dict:
                                        tool_args = f" → {args_dict['url']}"
                                    elif 'extensions' in args_dict or 'path_prefixes' in args_dict:
                                        parts = []
                                        if 'extensions' in args_dict:
                                            parts.append(f"ext={args_dict['extensions']}")
                                        if 'path_prefixes' in args_dict:
                                            parts.append(f"paths={args_dict['path_prefixes']}")
                                        tool_args = f" → {', '.join(parts)}"
                                except:
                                    pass
                            
                            print(f"\n[{tool_counter}] 🔧 Calling: {tool_name}{tool_args}...", flush=True)
                            first_event_received = True
                        else:
                            # Still couldn't extract - try to inspect raw_item structure
                            if hasattr(event.item, 'raw_item'):
                                raw = event.item.raw_item
                                # Try to get tool name by inspecting raw_item attributes
                                try:
                                    raw_attrs = [attr for attr in dir(raw) if not attr.startswith('_')]
                                    # Look for attributes that might contain the tool name
                                    for attr in raw_attrs:
                                        try:
                                            val = getattr(raw, attr)
                                            if isinstance(val, str) and ('get_github' in val.lower() or 'list_repo' in val.lower() or 'firecrawl' in val.lower()):
                                                tool_name = val
                                                break
                                            # Check if it's a dict-like object with name
                                            if hasattr(val, 'name'):
                                                tool_name = val.name
                                                break
                                        except:
                                            continue
                                    
                                    if tool_name:
                                        tool_counter += 1
                                        tool_id = tool_id or f"tool_{tool_counter}"
                                        active_tools[tool_id] = tool_name
                                        print(f"\n[{tool_counter}] 🔧 Calling: {tool_name}...", flush=True)
                                        first_event_received = True
                                    else:
                                        # Print raw_item structure for debugging
                                        print(f"\n[DEBUG] raw_item attrs: {raw_attrs[:10]}", flush=True)
                                except Exception as e:
                                    print(f"\n[DEBUG] Error inspecting raw_item: {e}", flush=True)
                    elif item_type == "tool_call_output_item":
                        # Track completed tools but don't display (user only wants "Calling" messages)
                        tool_id = None
                        
                        # Try raw_item first
                        if hasattr(event.item, 'raw_item') and hasattr(event.item.raw_item, 'tool_call_id'):
                            tool_id = event.item.raw_item.tool_call_id
                        elif hasattr(event.item, 'tool_call_id'):
                            tool_id = event.item.tool_call_id
                        elif hasattr(event.item, 'raw_item') and hasattr(event.item.raw_item, 'tool_call'):
                            if hasattr(event.item.raw_item.tool_call, 'id'):
                                tool_id = event.item.raw_item.tool_call.id
                        elif hasattr(event.item, 'tool_call'):
                            if hasattr(event.item.tool_call, 'id'):
                                tool_id = event.item.tool_call.id
                            elif hasattr(event.item.tool_call, 'function') and hasattr(event.item.tool_call.function, 'name'):
                                # Try to match by name if ID not available
                                tool_name_match = event.item.tool_call.function.name
                                for tid, tname in active_tools.items():
                                    if tname == tool_name_match:
                                        tool_id = tid
                                        break
                        
                        if tool_id and tool_id in active_tools:
                            tool_name = active_tools.pop(tool_id)
                            completed_tools.append(tool_name)
                        elif active_tools:
                            # Fallback: use the first active tool
                            tool_id, tool_name = next(iter(active_tools.items()))
                            active_tools.pop(tool_id)
                            completed_tools.append(tool_name)
                    elif item_type == "message_output_item":
                        message_text = ItemHelpers.text_message_output(event.item)
                        if message_text and (not final_output or message_text not in final_output):
                            print(f"\n{message_text}", flush=True)
                            final_output += message_text
                    # Ignore other non-critical item types
                    elif item_type not in ['message_input_item', 'message_output_item']:
                        # Silently ignore other types
                        pass
            
            print()  # Add newline after streaming
            
            # Show summary of tools used
            if completed_tools:
                print(f"---\n\n📊 Tools used ({len(completed_tools)}): {', '.join(completed_tools)}", flush=True)
            
            # If no streaming events occurred, fall back to final output
            if not final_output:
                final_output = result.final_output
                if final_output:
                    print(final_output, flush=True)
                
            return final_output
                
        except Exception as e:
            print(f"⚠️  Error: {e}", flush=True)
            # Fallback to standard async run
            result = await Runner.run(
                agent,
                input=user_prompt,
                context={"repo": repo, "issue_number": issue_number},
            )
            print(result.final_output, flush=True)
            return result.final_output
    
    # Run the async function
    try:
        final_output = await run_agent_async()
    except Exception as e:
        print(f"⚠️  Error: {e}", flush=True)
        # Final fallback to standard sync run
        result = Runner.run_sync(
            agent,
            input=user_prompt,
            context={"repo": repo, "issue_number": issue_number},
        )
        print(result.final_output, flush=True)
        final_output = result.final_output

    # Save to markdown file   
    with open(markdown_file, 'w', encoding='utf-8') as f:
        f.write(f"# GitHub Issue Analysis: {repo}#{issue_number}\n\n")
        f.write(f"**Generated on:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**Repository:** {repo}\n")
        f.write(f"**Issue Number:** {issue_number}\n\n")
        f.write("---\n\n")
        f.write(final_output)
    
    print(f"---\n\n✅ Saved: {markdown_file}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
