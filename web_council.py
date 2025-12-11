"""
AI Council Web Interface
Flask web app with HTML interface for the AI Council
"""

# ============================================================================
# 🔑 PASTE YOUR OPENROUTER API KEY HERE:
# ============================================================================
OPENROUTER_API_KEY = "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"
# Get your free API key at: https://openrouter.ai/keys
# ============================================================================

import os
import requests
import json
import time
from typing import List, Dict, Optional
from flask import Flask, render_template, request, jsonify
from openai import OpenAI

# Set up API configuration
os.environ["OPENAI_API_KEY"] = OPENROUTER_API_KEY
os.environ["OPENAI_API_BASE"] = "https://openrouter.ai/api/v1"

app = Flask(__name__)

# Models known to have issues - will be filtered out
BLACKLISTED_MODELS = [
    "deepseek/deepseek-chat-v3.1:free",  # Data policy error
    "moonshotai/kimi-k2:free",  # Data policy error
    "google/gemma-3n-e2b-it:free",  # Developer instruction not enabled
    "mistralai/mistral-small-3.2-24b-instruct:free",  # Rate limited
]

# WORKING FREE MODELS - Models that have proven reliable
FALLBACK_FREE_MODELS = [
    {
        "id": "meta-llama/llama-3.2-3b-instruct:free",
        "name": "Meta Llama 3.2 3B",
        "description": "Fast, efficient model from Meta",
        "provider": "Meta"
    },
    {
        "id": "google/gemma-2-9b-it:free",
        "name": "Google Gemma 2 9B",
        "description": "Google's open model",
        "provider": "Google"
    },
    {
        "id": "microsoft/phi-3-mini-128k-instruct:free",
        "name": "Microsoft Phi-3 Mini",
        "description": "Compact model from Microsoft",
        "provider": "Microsoft"
    },
    {
        "id": "qwen/qwen-2-7b-instruct:free",
        "name": "Qwen 2 7B",
        "description": "Alibaba's efficient model",
        "provider": "Alibaba"
    },
    {
        "id": "mistralai/mistral-7b-instruct:free",
        "name": "Mistral 7B",
        "description": "Popular open-source model",
        "provider": "Mistral AI"
    },
    {
        "id": "nousresearch/hermes-3-llama-3.1-405b:free",
        "name": "Hermes 3 Llama 405B",
        "description": "Advanced reasoning model",
        "provider": "Nous Research"
    },
    {
        "id": "huggingfaceh4/zephyr-7b-beta:free",
        "name": "Zephyr 7B Beta",
        "description": "Fine-tuned conversational model",
        "provider": "HuggingFace"
    },
    {
        "id": "meta-llama/llama-3.2-1b-instruct:free",
        "name": "Meta Llama 3.2 1B",
        "description": "Lightweight model from Meta",
        "provider": "Meta"
    },
    {
        "id": "google/gemma-7b-it:free",
        "name": "Google Gemma 7B",
        "description": "Google's instruction-tuned model",
        "provider": "Google"
    },
    {
        "id": "microsoft/phi-3-medium-128k-instruct:free",
        "name": "Microsoft Phi-3 Medium",
        "description": "Medium-sized model from Microsoft",
        "provider": "Microsoft"
    },
    {
        "id": "openchat/openchat-7b:free",
        "name": "OpenChat 7B",
        "description": "Open-source conversational AI",
        "provider": "OpenChat"
    }
]

# Personality definitions - 15 distinct council members
PERSONALITIES = [
    {
        "name": "The Strategist",
        "emoji": "🎯",
        "description": "You are Marcus, a master strategist and game theorist. You analyze decisions through the lens of long-term consequences, competitive advantages, and multiple scenario planning. You think three steps ahead and consider how choices cascade into future outcomes. You're calculating but not cold, always weighing risk versus reward.",
        "color": "#3b82f6"
    },
    {
        "name": "The Empath",
        "emoji": "❤️",
        "description": "You are Sofia, a deeply empathetic counselor who prioritizes human wellbeing and emotional intelligence. You consider how decisions affect people's feelings, relationships, mental health, and sense of belonging. You advocate for compassion, inclusivity, and psychological safety. You believe the right choice is the one that causes the least harm and the most healing.",
        "color": "#ec4899"
    },
    {
        "name": "The Skeptic",
        "emoji": "🤔",
        "description": "You are Dr. Chen, a critical thinker and devil's advocate. You instinctively question assumptions, poke holes in arguments, and surface hidden risks. You're the voice of caution who asks 'What could go wrong?' and 'Are we sure about this?' You value evidence over enthusiasm and prefer proven methods over trendy innovations.",
        "color": "#f59e0b"
    },
    {
        "name": "The Visionary",
        "emoji": "🚀",
        "description": "You are Nova, an optimistic futurist who sees potential and possibilities everywhere. You're excited by innovation, progress, and bold ideas. You believe in taking calculated risks to achieve breakthroughs. You think exponentially rather than incrementally and champion paradigm shifts over incremental improvements. You inspire others to dream bigger.",
        "color": "#8b5cf6"
    },
    {
        "name": "The Pragmatist",
        "emoji": "⚙️",
        "description": "You are James, a no-nonsense engineer who focuses on what actually works in the real world. You care about feasibility, budget constraints, time limits, and practical implementation. You cut through idealism with questions like 'How much will this cost?' and 'Can we actually build this?' You value working solutions over perfect theories.",
        "color": "#10b981"
    },
    {
        "name": "The Historian",
        "emoji": "📚",
        "description": "You are Professor Williams, a scholar who draws wisdom from the past. You recognize patterns, learn from previous failures and successes, and understand that 'those who don't learn from history are doomed to repeat it.' You provide context by citing precedents, analogies, and lessons learned. You're the institutional memory of the council.",
        "color": "#ef4444"
    },
    {
        "name": "The Rebel",
        "emoji": "⚡",
        "description": "You are Kai, a contrarian and disruptor who challenges conventional wisdom. You question why things are done the way they've always been done. You're not satisfied with the status quo and actively seek alternative perspectives. You believe the majority is often wrong and that progress requires breaking rules. You're provocative but purposeful.",
        "color": "#f97316"
    },
    {
        "name": "The Scientist",
        "emoji": "🔬",
        "description": "You are Dr. Rivera, a rigorous scientist who demands empirical evidence and statistical significance. You approach every question with the scientific method: hypothesis, testing, data, and reproducibility. You're skeptical of anecdotes and prefer peer-reviewed studies. You believe truth emerges through systematic inquiry and controlled experiments.",
        "color": "#06b6d4"
    },
    {
        "name": "The Artist",
        "emoji": "🎨",
        "description": "You are Luna, a creative soul who values beauty, expression, and human experience. You see the world through aesthetics, emotions, and cultural significance. You believe some truths can't be measured by logic alone and that creativity drives innovation. You ask 'How does this make us feel?' and 'What story does this tell?'",
        "color": "#d946ef"
    },
    {
        "name": "The Economist",
        "emoji": "💰",
        "description": "You are Morgan, an economist who analyzes everything through markets, incentives, and resource allocation. You understand opportunity costs, supply and demand, and how incentives shape behavior. You believe economics explains human nature and that following the money reveals true motivations. Every decision is an investment with returns.",
        "color": "#eab308"
    },
    {
        "name": "The Environmentalist",
        "emoji": "🌍",
        "description": "You are Terra, an environmental advocate who considers ecological impact and sustainability. You think in terms of ecosystems, carbon footprints, and planetary boundaries. You believe we're stewards of Earth for future generations. You ask 'What's the environmental cost?' and 'Is this sustainable long-term?' Nature's health is humanity's health.",
        "color": "#22c55e"
    },
    {
        "name": "The Philosopher",
        "emoji": "🧠",
        "description": "You are Socrates, a philosopher who explores fundamental questions of meaning, ethics, and existence. You examine underlying assumptions, question definitions, and explore logical consistency. You believe asking the right questions matters more than quick answers. You challenge others to think deeper about 'Why?' and 'What does this really mean?'",
        "color": "#6366f1"
    },
    {
        "name": "The Populist",
        "emoji": "📣",
        "description": "You are Sam, a voice of the common people who prioritizes what the majority wants and needs. You believe democracy means listening to ordinary citizens, not just elites or experts. You're suspicious of ivory tower thinking and value lived experience. You ask 'What do regular people think?' and 'Who benefits from this?'",
        "color": "#f43f5e"
    },
    {
        "name": "The Optimist",
        "emoji": "☀️",
        "description": "You are Ray, an eternal optimist who sees the silver lining in every cloud. You believe in human potential, progress, and positive outcomes. While not naive, you choose hope over cynicism. You energize others with enthusiasm and believe optimism is a strategic choice. Problems are opportunities in disguise.",
        "color": "#fb923c"
    },
    {
        "name": "The Realist",
        "emoji": "⚖️",
        "description": "You are Jordan, a balanced realist who sees both pros and cons without bias toward either. You're neither optimistic nor pessimistic—just honest about trade-offs. You cut through rhetoric to examine facts, acknowledge complexity, and resist oversimplification. You believe every choice has costs and benefits that deserve equal consideration.",
        "color": "#64748b"
    }
]


def get_free_models(max_models: int = 15) -> List[Dict]:
    """Fetch free models from OpenRouter API or use fallback. Filters out known problematic models."""
    try:
        response = requests.get("https://openrouter.ai/api/v1/models", timeout=10)
        response.raise_for_status()
        data = response.json()
        
        free_models = []
        for model in data.get("data", []):
            model_id = model.get("id", "")
            
            # Skip blacklisted models
            if model_id in BLACKLISTED_MODELS:
                continue
            
            pricing = model.get("pricing", {})
            prompt_price = pricing.get("prompt", None)
            completion_price = pricing.get("completion", None)
            
            is_free = (
                ":free" in model_id or
                pricing is None or pricing == {} or
                (prompt_price is None and completion_price is None) or
                (str(prompt_price) == "0" and str(completion_price) == "0")
            )
            
            if is_free:
                free_models.append({
                    "id": model_id,
                    "name": model.get("name", model_id),
                    "description": model.get("description", ""),
                    "provider": "Unknown"
                })
                
                if len(free_models) >= max_models:
                    break
        
        if free_models:
            return free_models
        
        return FALLBACK_FREE_MODELS[:max_models]
    
    except Exception as e:
        print(f"Using fallback models: {e}")
        return FALLBACK_FREE_MODELS[:max_models]


def extract_answer_options(client: OpenAI, question: str) -> Dict:
    """
    Use AI moderator to determine what answer options are valid for the question.
    """
    moderator_prompt = """You are a moderator AI that extracts choices from questions. Your job is to identify the EXACT options the user is asking about.

Examples:
Question: "Should I study or watch TV?"
TYPE: CHOICE
OPTIONS: Study, Watch TV

Question: "Should we use AI for moderation?"
TYPE: BINARY
OPTIONS: YES, NO

Question: "Which is better: Python, JavaScript, or Rust?"
TYPE: CHOICE
OPTIONS: Python, JavaScript, Rust

Question: "Blue or red?"
TYPE: CHOICE
OPTIONS: Blue, Red

Extract the EXACT choices from the question. Keep options short and clear (1-3 words each).
If it's not a clear choice question, use YES/NO.
Always respond in this format:
TYPE: [BINARY or CHOICE]
OPTIONS: [option1, option2, ...]"""

    try:
        response = client.chat.completions.create(
            model="meta-llama/llama-3.2-3b-instruct:free",
            messages=[
                {"role": "system", "content": moderator_prompt},
                {"role": "user", "content": f"Question: {question}"}
            ],
            max_tokens=100,
            temperature=0.1
        )
        
        content = response.choices[0].message.content.strip()
        
        # Parse the response
        answer_type = "BINARY"
        options = ["YES", "NO"]
        
        if "TYPE:" in content:
            type_line = [line for line in content.split("\n") if "TYPE:" in line][0]
            answer_type = type_line.split("TYPE:")[1].strip()
        
        if "OPTIONS:" in content:
            options_line = [line for line in content.split("\n") if "OPTIONS:" in line][0]
            options_str = options_line.split("OPTIONS:")[1].strip()
            options = [opt.strip() for opt in options_str.split(",")]
        
        return {
            "type": answer_type,
            "options": options,
            "raw_response": content
        }
    
    except Exception as e:
        print(f"Moderator error: {e}")
        return {
            "type": "BINARY",
            "options": ["YES", "NO"],
            "raw_response": "Error analyzing question"
        }


def get_vote_from_model(client: OpenAI, model_id: str, personality: Dict, question: str, answer_context: Dict) -> Optional[Dict]:
    """Get a vote from a model with specific personality."""
    
    # Build list of valid options
    options_list = answer_context['options']
    options_str = ' or '.join([f'"{opt}"' for opt in options_list])
    
    system_prompt = f"""{personality['description']}

You are part of an AI Council voting on a question.

CRITICAL: You must pick EXACTLY ONE of these options: {options_str}

Do not create your own answer. Do not modify the options. Pick one of the given options EXACTLY as written.

Respond in this format:
ANSWER: [pick one option exactly]
REASONING: [one sentence explaining why you chose this option]

Example:
ANSWER: {options_list[0]}
REASONING: This option aligns with my perspective because..."""

    try:
        response = client.chat.completions.create(
            model=model_id,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Question: {question}\n\nYou must choose ONLY from these options: {', '.join(options_list)}"}
            ],
            max_tokens=200,
            temperature=0.7
        )
        
        content = response.choices[0].message.content.strip()
        
        # Parse response
        answer = None
        reasoning = content
        
        # Extract answer
        if "ANSWER:" in content:
            parts = content.split("ANSWER:")
            if len(parts) > 1:
                answer_part = parts[1].split("\n")[0].strip()
                # Remove quotes if present
                answer = answer_part.strip('"').strip("'").strip()
        
        # Extract reasoning
        if "REASONING:" in content:
            reasoning_parts = content.split("REASONING:")
            if len(reasoning_parts) > 1:
                reasoning = reasoning_parts[1].strip()
        else:
            # If no explicit reasoning, use content after answer
            if "ANSWER:" in content and "\n" in content:
                lines = content.split("\n")
                reasoning = " ".join(lines[1:]).strip()
        
        # If reasoning is empty or too short, use the full content or a fallback
        if not reasoning or len(reasoning) < 10:
            if "ANSWER:" in content:
                # Try to get everything after the answer line
                remaining = content.split("ANSWER:", 1)[1]
                if "\n" in remaining:
                    reasoning = "\n".join(remaining.split("\n")[1:]).strip()
            # If still empty, use full content as reasoning
            if not reasoning or len(reasoning) < 10:
                reasoning = content if content else "This option aligns with my perspective."
        
        # If answer not found, try to match against valid options
        if not answer:
            answer_upper = content.upper()
            for option in options_list:
                if option.upper() in answer_upper:
                    answer = option
                    break
        
        # Last resort: use first option
        if not answer:
            answer = options_list[0]
        
        # Try to match answer to closest valid option (case-insensitive)
        matched_option = None
        answer_clean = answer.upper().strip()
        for option in options_list:
            if option.upper() in answer_clean or answer_clean in option.upper():
                matched_option = option
                break
        
        if matched_option:
            answer = matched_option
        
        return {
            "answer": answer,
            "reasoning": reasoning,
            "model": model_id,
            "personality": personality["name"],
            "emoji": personality["emoji"],
            "color": personality["color"]
        }
    
    except Exception as e:
        error_msg = str(e)
        # Simplify common error messages
        if "404" in error_msg and "data policy" in error_msg:
            print(f"⚠️  Skipping {model_id}: Not available (data policy)")
        elif "400" in error_msg and "not enabled" in error_msg:
            print(f"⚠️  Skipping {model_id}: Feature not supported")
        elif "429" in error_msg:
            print(f"⚠️  Skipping {model_id}: Rate limited")
        else:
            print(f"⚠️  Skipping {model_id}: {error_msg[:80]}")
        return None


# ============================================================================
# DEBATE SYSTEM - AI-to-AI Communication with Free Will
# ============================================================================

def get_opening_statement(client: OpenAI, model_id: str, personality: Dict, question: str, answer_context: Dict) -> Optional[Dict]:
    """Get opening statement from an AI in Round 1."""
    options_list = answer_context['options']
    options_str = ' or '.join([f'"{opt}"' for opt in options_list])
    
    system_prompt = f"""{personality['description']}

You are {personality['name']} in an AI Council debate. This is ROUND 1: Opening Statements.

Question: {question}
Valid options: {options_str}

Give your opening statement:
1. State your initial position (pick ONE option: {options_str})
2. Explain your reasoning in 2-3 sentences

Format:
POSITION: [your choice]
STATEMENT: [your 2-3 sentence argument]"""

    try:
        response = client.chat.completions.create(
            model=model_id,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Give your opening statement on: {question}"}
            ],
            max_tokens=250,
            temperature=0.8
        )
        
        content = response.choices[0].message.content.strip()
        
        # Parse position and statement
        position = None
        statement = content
        
        if "POSITION:" in content:
            parts = content.split("POSITION:")
            if len(parts) > 1:
                position_part = parts[1].split("\n")[0].strip().strip('"').strip("'")
                # Match to valid option
                for option in options_list:
                    if option.upper() in position_part.upper() or position_part.upper() in option.upper():
                        position = option
                        break
        
        if "STATEMENT:" in content:
            statement_parts = content.split("STATEMENT:")
            if len(statement_parts) > 1:
                statement = statement_parts[1].strip()
        
        # Fallback position matching
        if not position:
            for option in options_list:
                if option.upper() in content.upper():
                    position = option
                    break
            if not position:
                position = options_list[0]
        
        return {
            "position": position,
            "statement": statement,
            "model": model_id,
            "personality": personality["name"],
            "emoji": personality["emoji"],
            "color": personality["color"]
        }
    
    except Exception as e:
        print(f"Error in opening statement {model_id}: {e}")
        return None


def ai_decides_to_speak(client: OpenAI, model_id: str, personality: Dict, question: str, debate_log: List[Dict], round_num: int, my_position: str) -> Dict:
    """AI uses FREE WILL to decide whether to speak based on what others said."""
    
    # Build context of what others have said (including their REASONING)
    recent_statements = "\n".join([
        f"- {log['speaker']} chose '{log['position']}' because: {log['message']}"
        for log in debate_log[-12:]  # Last 12 messages
    ])
    
    system_prompt = f"""{personality['description']}

You are {personality['name']} in Round {round_num} of the debate.

Question: {question}
Your current position: {my_position}

What others have said and WHY they chose their positions:
{recent_statements}

FREE WILL DECISION: Should you intervene or stay silent?

READ what others said carefully and decide:
- If you DISAGREE with someone's reasoning → SPEAK to challenge them
- If you see a flaw in someone's logic → SPEAK to point it out
- If someone makes a point you want to support → SPEAK to reinforce it
- If you want to change your position based on good arguments → SPEAK to explain why
- If others already made your points well → SILENT (no need to repeat)
- If you have nothing new to add → SILENT

Be SELECTIVE. Only speak if you have something meaningful to contribute based on what you READ above.

Respond with ONLY:
DECISION: SPEAK
or
DECISION: SILENT"""

    try:
        response = client.chat.completions.create(
            model=model_id,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "Based on what you read, do you need to speak? SPEAK or SILENT?"}
            ],
            max_tokens=80,
            temperature=0.85
        )
        
        content = response.choices[0].message.content.strip().upper()
        
        # Parse decision
        if "SPEAK" in content and "SILENT" not in content:
            return {"decision": "SPEAK", "reason": "AI chose to intervene based on what they read"}
        else:
            return {"decision": "SILENT", "reason": "AI chose to observe - nothing new to add"}
    
    except Exception as e:
        print(f"Error in free will decision {model_id}: {e}")
        return {"decision": "SILENT", "reason": "Error occurred"}


def get_debate_response(client: OpenAI, model_id: str, personality: Dict, question: str, answer_context: Dict, debate_log: List[Dict], round_num: int, current_position: str) -> Optional[Dict]:
    """Get AI's response during debate rounds (can change position)."""
    options_list = answer_context['options']
    
    # Build debate context
    recent_statements = "\n".join([
        f"- {log['speaker']} ({log['position']}): {log['message']}"
        for log in debate_log[-15:]  # Last 15 messages
    ])
    
    system_prompt = f"""{personality['description']}

You are {personality['name']} in Round {round_num}.
Your current position: {current_position}

Question: {question}
Valid options: {', '.join(options_list)}

What others have said:
{recent_statements}

You can now:
1. DEFEND your position with new arguments
2. CHALLENGE someone else's reasoning
3. CHANGE your position if convinced (explain why)
4. BUILD ON someone else's point

Format:
POSITION: [your current choice - can change if convinced]
MESSAGE: [your argument, challenge, or response - 2-3 sentences]"""

    try:
        response = client.chat.completions.create(
            model=model_id,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Respond to the debate (Round {round_num}):"}
            ],
            max_tokens=300,
            temperature=0.85
        )
        
        content = response.choices[0].message.content.strip()
        
        # Parse position and message
        new_position = current_position
        message = content
        
        if "POSITION:" in content:
            parts = content.split("POSITION:")
            if len(parts) > 1:
                position_part = parts[1].split("\n")[0].strip().strip('"').strip("'")
                for option in options_list:
                    if option.upper() in position_part.upper() or position_part.upper() in option.upper():
                        new_position = option
                        break
        
        if "MESSAGE:" in content:
            message_parts = content.split("MESSAGE:")
            if len(message_parts) > 1:
                message = message_parts[1].strip()
        
        position_changed = (new_position != current_position)
        
        return {
            "position": new_position,
            "message": message,
            "position_changed": position_changed,
            "model": model_id,
            "personality": personality["name"],
            "emoji": personality["emoji"],
            "color": personality["color"]
        }
    
    except Exception as e:
        print(f"Error in debate response {model_id}: {e}")
        return None


def run_debate(client: OpenAI, question: str, answer_context: Dict, council_members: List[Dict]) -> Dict:
    """Run multi-round debate with free will decisions."""
    debate_log = []
    positions = {}  # Track each AI's current position
    
    # ROUND 1: Opening Statements (everyone speaks)
    print("\n=== ROUND 1: Opening Statements ===")
    for member in council_members:
        result = get_opening_statement(
            client, 
            member["model"]["id"], 
            member["personality"], 
            question, 
            answer_context
        )
        if result:
            positions[member["personality"]["name"]] = result["position"]
            debate_log.append({
                "round": 1,
                "speaker": member["personality"]["name"],
                "emoji": member["personality"]["emoji"],
                "color": member["personality"]["color"],
                "position": result["position"],
                "message": result["statement"],
                "type": "opening",
                "position_changed": False
            })
            print(f"  {result['emoji']} {member['personality']['name']}: {result['position']}")
    
    # ROUND 2: Rebuttals & Debates (free will to speak)
    print("\n=== ROUND 2: Rebuttals & Debates ===")
    for member in council_members:
        # Skip if AI didn't participate in Round 1
        if member["personality"]["name"] not in positions:
            print(f"  ⏭️ {member['personality']['emoji']} {member['personality']['name']}: Skipped (failed in Round 1)")
            continue
        
        # AI decides whether to speak (based on what they READ from others)
        decision = ai_decides_to_speak(
            client,
            member["model"]["id"],
            member["personality"],
            question,
            debate_log,
            2,
            positions[member["personality"]["name"]]  # Their current position
        )
        
        if decision["decision"] == "SPEAK":
            result = get_debate_response(
                client,
                member["model"]["id"],
                member["personality"],
                question,
                answer_context,
                debate_log,
                2,
                positions[member["personality"]["name"]]
            )
            if result:
                positions[member["personality"]["name"]] = result["position"]
                debate_log.append({
                    "round": 2,
                    "speaker": member["personality"]["name"],
                    "emoji": member["personality"]["emoji"],
                    "color": member["personality"]["color"],
                    "position": result["position"],
                    "message": result["message"],
                    "type": "rebuttal",
                    "position_changed": result["position_changed"]
                })
                status = "🔄 CHANGED POSITION" if result["position_changed"] else "💬"
                print(f"  {status} {result['emoji']} {member['personality']['name']}: {result['position']}")
        else:
            debate_log.append({
                "round": 2,
                "speaker": member["personality"]["name"],
                "emoji": member["personality"]["emoji"],
                "color": member["personality"]["color"],
                "position": positions[member["personality"]["name"]],
                "message": "[Chose to observe silently]",
                "type": "silent",
                "position_changed": False
            })
            print(f"  😶 {member['personality']['emoji']} {member['personality']['name']}: Silent")
        time.sleep(0.3)
    
    # ROUND 3: Final Arguments (free will again)
    print("\n=== ROUND 3: Final Arguments ===")
    for member in council_members:
        # Skip if AI didn't participate in Round 1
        if member["personality"]["name"] not in positions:
            print(f"  ⏭️ {member['personality']['emoji']} {member['personality']['name']}: Skipped (failed in Round 1)")
            continue
        
        # AI decides whether to speak (based on the full debate so far)
        decision = ai_decides_to_speak(
            client,
            member["model"]["id"],
            member["personality"],
            question,
            debate_log,
            3,
            positions[member["personality"]["name"]]  # Their current position
        )
        
        if decision["decision"] == "SPEAK":
            result = get_debate_response(
                client,
                member["model"]["id"],
                member["personality"],
                question,
                answer_context,
                debate_log,
                3,
                positions[member["personality"]["name"]]
            )
            if result:
                positions[member["personality"]["name"]] = result["position"]
                debate_log.append({
                    "round": 3,
                    "speaker": member["personality"]["name"],
                    "emoji": member["personality"]["emoji"],
                    "color": member["personality"]["color"],
                    "position": result["position"],
                    "message": result["message"],
                    "type": "final",
                    "position_changed": result["position_changed"]
                })
                status = "🔄 CHANGED POSITION" if result["position_changed"] else "📣"
                print(f"  {status} {result['emoji']} {member['personality']['name']}: {result['position']}")
        else:
            debate_log.append({
                "round": 3,
                "speaker": member["personality"]["name"],
                "emoji": member["personality"]["emoji"],
                "color": member["personality"]["color"],
                "position": positions[member["personality"]["name"]],
                "message": "[Let their previous position stand]",
                "type": "silent",
                "position_changed": False
            })
            print(f"  😶 {member['personality']['emoji']} {member['personality']['name']}: Silent")
        time.sleep(0.3)
    
    return {
        "debate_log": debate_log,
        "final_positions": positions
    }


@app.route('/')
def index():
    """Serve the main HTML interface."""
    return render_template('index.html')


@app.route('/api/council', methods=['POST'])
def run_council():
    """API endpoint to run the AI council DEBATE (not just voting)."""
    data = request.json
    question = data.get('question', '')
    
    if not question:
        return jsonify({"error": "No question provided"}), 400
    
    if OPENROUTER_API_KEY == "PASTE_YOUR_API_KEY_HERE":
        return jsonify({"error": "No API key set"}), 400
    
    try:
        client = OpenAI(api_key=OPENROUTER_API_KEY, base_url="https://openrouter.ai/api/v1")
        
        # Step 1: Moderator determines answer type
        answer_context = extract_answer_options(client, question)
        
        # Step 2: Get free models and assign personalities (only working ones)
        free_models = get_free_models(max_models=11)
        
        council_members = []
        for i, model in enumerate(free_models):
            if i < len(PERSONALITIES):
                council_members.append({
                    "model": model,
                    "personality": PERSONALITIES[i]
                })
        
        # Step 3: RUN THE DEBATE (multi-round with free will)
        debate_results = run_debate(client, question, answer_context, council_members)
        
        # Step 4: Count final positions
        vote_counts = {}
        for position in debate_results["final_positions"].values():
            vote_counts[position] = vote_counts.get(position, 0) + 1
        
        # Find winner
        if vote_counts:
            winner = max(vote_counts.items(), key=lambda x: x[1])
            verdict = f"{winner[0]} ({winner[1]} votes)"
        else:
            verdict = "No consensus"
        
        # Analyze position changes
        position_changes = []
        for log in debate_results["debate_log"]:
            if log.get("position_changed", False):
                position_changes.append({
                    "speaker": log["speaker"],
                    "emoji": log["emoji"],
                    "round": log["round"]
                })
        
        return jsonify({
            "success": True,
            "question": question,
            "moderator": answer_context,
            "debate_log": debate_results["debate_log"],
            "final_positions": debate_results["final_positions"],
            "vote_counts": vote_counts,
            "verdict": verdict,
            "position_changes": position_changes
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    print("🌐 Starting AI Council Web Server...")
    print("📝 Open your browser to: http://localhost:5000")
    print("🔑 API Key:", "Set ✓" if OPENROUTER_API_KEY != "PASTE_YOUR_API_KEY_HERE" else "Not set ✗")
    app.run(debug=True, port=5000)

