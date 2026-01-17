# new_dict = {
#     "agents": [
#         {
#             "id": "coordinator_agent_1",
#             "role": "Coordinator Agent",
#             "goal": "Coordinate multiple agents to produce a final high-quality result",
#             "description": "Manages workflow, delegates tasks, and produces final output",
#             "model": "claude_sonnet",
#             "tools": ["python"],
#             "instruction": "You are the coordinator agent.\nYour responsibilities:\n- Understand the task\n- Delegate work to sub-agents\n- Combine responses\n- Produce final output\n",
#             "sub_agents": ["researcher_agent_1", "analyst_agent_1", "writer_agent_1"],
#         },
#         {
#             "id": "researcher_agent_1",
#             "role": "Research Assistant",
#             "goal": "Collect accurate and relevant information",
#             "model": "default_model",
#             "tools": ["deep-research", "web_search"],
#             "instruction": "Research the given topic thoroughly and extract key insights.\n",
#         },
#         {
#             "id": "analyst_agent_1",
#             "role": "Data Analyst",
#             "goal": "Analyze structured data and derive insights",
#             "tools": ["python"],
#             "instruction": "Analyze provided data and summarize trends.\n",
#         },
#         {
#             "id": "writer_agent_1",
#             "role": "Content Writer",
#             "goal": "Write a concise and clear explanation",
#             "tools": ["text-editor"],
#             "instruction": "Write a final summary based on provided context.\n",
#         },
#     ],
#     "workflow": {
#         "type": "sequential",
#         "steps": [
#             "coordinator_agent_1",
#             "researcher_agent_1",
#             "analyst_agent_1",
#             "writer_agent_1",
#         ],
#     },
#     "models": {
#         "default_model": {
#             "provider": "openai",
#             "model": "gpt-4.1",
#             "temperature": 0.3,
#             "max_tokens": 4096,
#         },
#         "claude_sonnet": {
#             "provider": "anthropic",
#             "model": "claude-sonnet-4-0",
#             "temperature": 0.2,
#             "max_tokens": 64000,
#         },
#     },
# }


new_dict2 = {
    "agents": [
        {
            "id": "researcher",
            "role": "Research Assistant",
            "goal": "Find key insights about electric vehicles",
            "description": "",
            "model": "gemini",
            "tools": [],
            "instruction": "",
            "sub_agents": [],
        },
        {
            "id": "writer",
            "role": "Content Writer",
            "goal": "Write a concise summary using the research",
            "description": "",
            "model": "gemini",
            "tools": [],
            "instruction": "",
            "sub_agents": [],
        },
    ],
    "workflow": {"type": "sequential", "steps": ["researcher", "writer"]},
    "models": {
        "gemini": {
            "provider": "google",
            "model": "gemini",
            "temperature": 0.7,
            "max_tokens": 8096,
        }
    },
}


new_dict3 = {
    "agents": [
        {
            "id": "backend",
            "role": "Backend Engineer",
            "goal": "Propose an API design",
            "description": "",
            "model": "gemini",
            "tools": [],
            "instruction": "",
            "sub_agents": [],
        },
        {
            "id": "frontend",
            "role": "Frontend Engineer",
            "goal": "Propose a UI layout",
            "description": "",
            "model": "gemini",
            "tools": [],
            "instruction": "",
            "sub_agents": [],
        },
        {
            "id": "reviewer",
            "role": "Tech Lead",
            "goal": "Review and consolidate proposals",
            "description": "",
            "model": "gemini",
            "tools": [],
            "instruction": "",
            "sub_agents": [],
        },
    ],
    "workflow": {
        "type": "parallel",
        "branches": ["backend", "frontend"],
        "then": "reviewer",
    },
    "models": {
        "gemini": {
            "provider": "google",
            "model": "gemini",
            "temperature": 0.7,
            "max_tokens": 8096,
        }
    },
}


new_dict4 = {
    "agents": [
        {
            "id": "analyst",
            "role": "Data Analyst",
            "goal": "Analyze CSV data and summarize trends",
            "description": "",
            "model": "gemini",
            "tools": ["python"],
            "instruction": "",
            "sub_agents": [],
        }
    ],
    "workflow": {"type": "sequential", "steps": ["analyst"]},
    "models": {
        "gemini": {
            "provider": "google",
            "model": "gemini",
            "temperature": 0.7,
            "max_tokens": 8096,
        }
    },
}

new_dict5 = {
    "agents": [
        {
            "id": "root",
            "role": "Agent",
            "goal": "",
            "description": "Main coordinator agent that delegates tasks and manages workflow",
            "model": "claude",
            "tools": [],
            "instruction": "You are the root coordinator agent. Your job is to:\n1. Understand user requests and break them down into manageable tasks\n2. Delegate appropriate tasks to your helper agent\n3. Coordinate responses and ensure tasks are completed properly\n4. Provide final responses to the user\nWhen you receive a request, analyze what needs to be done and decide whether to:\n- Handle it yourself if it's simple\n- Delegate to the helper agent if it requires specific assistance\n- Break complex requests into multiple sub-tasks",
            "sub_agents": ["helper"],
        },
        {
            "id": "helper",
            "role": "Agent",
            "goal": "",
            "description": "Assistant agent that helps with various tasks as directed by the root agent",
            "model": "claude",
            "tools": [],
            "instruction": "You are a helpful assistant agent. Your role is to:\n1. Complete specific tasks assigned by the root agent\n2. Provide detailed and accurate responses\n3. Ask for clarification if tasks are unclear\n4. Report back to the root agent with your results\n\nFocus on being thorough and helpful in whatever task you're given.",
            "sub_agents": [],
        },
    ],
    "workflow": {"type": "sequential", "steps": ["root", "helper"]},
    "models": {
        "claude": {
            "provider": "anthropic",
            "model": "claude-sonnet-4-0",
            "temperature": 0.7,
            "max_tokens": 64000,
        }
    },
}
