"""
AI Council Script
Uses OpenRouter API to create an AI Council with free models.
Each AI gets a unique personality and votes on a question.
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
from typing import List, Dict, Optional
import time

# Set up API configuration
os.environ["OPENAI_API_KEY"] = OPENROUTER_API_KEY
os.environ["OPENAI_API_BASE"] = "https://openrouter.ai/api/v1"

try:
    from openai import OpenAI
except ImportError:
    print("Error: 'openai' library not installed. Install it with: pip install openai")
    exit(1)


# Models known to have issues - will be filtered out
BLACKLISTED_MODELS = [
    "deepseek/deepseek-chat-v3.1:free",  # Data policy error
    "moonshotai/kimi-k2:free",  # Data policy error
    "google/gemma-3n-e2b-it:free",  # Developer instruction not enabled
    "mistralai/mistral-small-3.2-24b-instruct:free",  # Rate limited
]

# Common free models available on OpenRouter (as of Nov 2024)
FALLBACK_FREE_MODELS = [
    {
        "id": "meta-llama/llama-3.2-3b-instruct:free",
        "name": "Meta Llama 3.2 3B Instruct",
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
        "name": "Qwen 2 7B Instruct",
        "description": "Alibaba's efficient model",
        "provider": "Alibaba"
    },
    {
        "id": "mistralai/mistral-7b-instruct:free",
        "name": "Mistral 7B Instruct",
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
    },
    {
        "id": "teknium/openhermes-2.5-mistral-7b:free",
        "name": "OpenHermes 2.5",
        "description": "Fine-tuned Mistral variant",
        "provider": "Teknium"
    },
    {
        "id": "undi95/toppy-m-7b:free",
        "name": "Toppy M 7B",
        "description": "Merge model optimized for chat",
        "provider": "Undi95"
    },
    {
        "id": "gryphe/mythomist-7b:free",
        "name": "MythoMist 7B",
        "description": "Creative storytelling model",
        "provider": "Gryphe"
    },
    {
        "id": "koboldai/psyfighter-13b-2:free",
        "name": "Psyfighter 13B",
        "description": "Multi-purpose instruction model",
        "provider": "KoboldAI"
    }
]


def get_free_models(max_models: int = 15) -> List[Dict]:
    """
    Fetch free models from OpenRouter API.
    Falls back to hardcoded list if API fails.
    Filters out known problematic models.
    
    Returns:
        List of model dictionaries (up to max_models)
    """
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
            
            # Check if model is free (no pricing or pricing is 0)
            pricing = model.get("pricing", {})
            prompt_price = pricing.get("prompt", None)
            completion_price = pricing.get("completion", None)
            
            # Consider free if pricing is missing or both prices are 0/null
            # or if the model ID ends with ":free"
            is_free = (
                ":free" in model_id or
                pricing is None or 
                pricing == {} or
                (prompt_price is None and completion_price is None) or
                (str(prompt_price) == "0" and str(completion_price) == "0")
            )
            
            if is_free:
                free_models.append({
                    "id": model_id,
                    "name": model.get("name", model_id),
                    "description": model.get("description", ""),
                    "provider": model.get("context_length", {}).get("name", "Unknown") if isinstance(model.get("context_length"), dict) else "Unknown"
                })
                
                # Stop when we have enough models
                if len(free_models) >= max_models:
                    break
        
        # If we found free models, return them
        if free_models:
            return free_models
        
        # Otherwise, use fallback list
        print("  ⚠️  No free models found via API, using fallback list...")
        return FALLBACK_FREE_MODELS[:max_models]
    
    except requests.exceptions.RequestException as e:
        print(f"  ⚠️  Error fetching models: {e}")
        print("  Using fallback free models list...")
        return FALLBACK_FREE_MODELS[:max_models]
    except Exception as e:
        print(f"  ⚠️  Error parsing models: {e}")
        print("  Using fallback free models list...")
        return FALLBACK_FREE_MODELS[:max_models]


# Personality definitions
PERSONALITIES = [
    {
        "name": "Strategist",
        "description": "You are a strategic thinker who analyzes long-term implications and considers multiple scenarios. You think carefully about consequences and trade-offs."
    },
    {
        "name": "Empath",
        "description": "You are empathetic and considerate, focusing on human impact, emotions, and ethical implications. You prioritize people's well-being."
    },
    {
        "name": "Skeptic",
        "description": "You are naturally skeptical and cautious. You question assumptions, look for potential problems, and consider what could go wrong."
    },
    {
        "name": "Visionary",
        "description": "You are forward-thinking and optimistic. You see potential benefits and opportunities, focusing on innovation and progress."
    },
    {
        "name": "Pragmatist",
        "description": "You are practical and realistic. You focus on what works, costs, feasibility, and immediate practicality."
    },
    {
        "name": "Historian",
        "description": "You draw on historical context and past experiences. You consider precedents, patterns, and lessons learned from history."
    },
    {
        "name": "Rebel",
        "description": "You are a contrarian who challenges conventional wisdom and questions the status quo. You believe progress requires breaking rules and disrupting norms."
    },
    {
        "name": "Scientist",
        "description": "You are a rigorous scientist who demands empirical evidence and statistical significance. You approach questions with the scientific method and prefer peer-reviewed data."
    },
    {
        "name": "Artist",
        "description": "You are a creative soul who values beauty, expression, and human experience. You believe some truths can't be measured by logic alone and creativity drives innovation."
    },
    {
        "name": "Economist",
        "description": "You are an economist who analyzes everything through markets, incentives, and resource allocation. You understand opportunity costs and how incentives shape behavior."
    },
    {
        "name": "Environmentalist",
        "description": "You are an environmental advocate who considers ecological impact and sustainability. You think in terms of ecosystems, carbon footprints, and planetary boundaries."
    },
    {
        "name": "Philosopher",
        "description": "You are a philosopher who explores fundamental questions of meaning, ethics, and existence. You examine assumptions and explore logical consistency."
    },
    {
        "name": "Populist",
        "description": "You are a voice of the common people who prioritizes what the majority wants and needs. You value lived experience over ivory tower thinking."
    },
    {
        "name": "Optimist",
        "description": "You are an eternal optimist who sees the silver lining in every cloud. You believe in human potential, progress, and positive outcomes."
    },
    {
        "name": "Realist",
        "description": "You are a balanced realist who sees both pros and cons without bias. You're neither optimistic nor pessimistic—just honest about trade-offs."
    }
]


def get_vote_from_model(client: OpenAI, model_id: str, personality: Dict, question: str) -> Optional[Dict]:
    """
    Get a vote (YES/NO) from a model with a specific personality.
    
    Returns:
        Dict with 'vote', 'reasoning', 'model', 'personality' or None if error
    """
    system_prompt = f"""{personality['description']}

You are part of an AI Council. When asked a question, you must respond with ONLY:
- Your vote: YES or NO
- Your reasoning: One concise sentence explaining your position

Format your response exactly as:
VOTE: YES
REASONING: [your one-sentence reasoning]

or

VOTE: NO
REASONING: [your one-sentence reasoning]
"""

    try:
        response = client.chat.completions.create(
            model=model_id,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question}
            ],
            max_tokens=150,
            temperature=0.7
        )
        
        content = response.choices[0].message.content.strip()
        
        # Parse the response
        vote = None
        reasoning = content
        
        # Try to extract vote from response
        if "VOTE:" in content:
            parts = content.split("VOTE:")
            if len(parts) > 1:
                vote_part = parts[1].split("\n")[0].strip()
                if "YES" in vote_part.upper():
                    vote = "YES"
                elif "NO" in vote_part.upper():
                    vote = "NO"
        
        # If vote not found in structured format, try to infer
        if vote is None:
            content_upper = content.upper()
            if content_upper.startswith("YES"):
                vote = "YES"
            elif content_upper.startswith("NO"):
                vote = "NO"
            else:
                # Look for YES/NO in the response
                if " YES" in content_upper or content_upper.startswith("YES"):
                    vote = "YES"
                elif " NO" in content_upper or content_upper.startswith("NO"):
                    vote = "NO"
        
        # Extract reasoning
        if "REASONING:" in content:
            reasoning_parts = content.split("REASONING:")
            if len(reasoning_parts) > 1:
                reasoning = reasoning_parts[1].strip()
        
        # Clean up reasoning (remove vote if it's mixed in)
        reasoning = reasoning.replace("VOTE:", "").replace("YES", "").replace("NO", "").strip()
        
        # If reasoning is empty or too short, use the full content or a fallback
        if not reasoning or len(reasoning) < 10:
            if "VOTE:" in content:
                # Try to get everything after the vote line
                remaining = content.split("VOTE:", 1)[1]
                if "\n" in remaining:
                    reasoning = "\n".join(remaining.split("\n")[1:]).strip()
            # If still empty, use full content as reasoning
            if not reasoning or len(reasoning) < 10:
                reasoning = content if content else "This aligns with my perspective."
        
        if vote is None:
            vote = "ABSTAIN"  # If we can't determine vote
        
        return {
            "vote": vote,
            "reasoning": reasoning,
            "model": model_id,
            "personality": personality["name"]
        }
    
    except Exception as e:
        error_msg = str(e)
        # Simplify common error messages
        if "404" in error_msg and "data policy" in error_msg:
            print(f"  ⚠️  Skipping {model_id}: Not available (data policy)")
        elif "400" in error_msg and "not enabled" in error_msg:
            print(f"  ⚠️  Skipping {model_id}: Feature not supported")
        elif "429" in error_msg:
            print(f"  ⚠️  Skipping {model_id}: Rate limited")
        else:
            print(f"  ⚠️  Skipping {model_id}: {error_msg[:80]}")
        return None


def main():
    """Main function to run the AI Council."""
    
    # Check for API key
    if OPENROUTER_API_KEY == "PASTE_YOUR_API_KEY_HERE":
        print("⚠️  No API key set!")
        print("Please open ai_council.py and paste your OpenRouter API key on line 10")
        print("\nGet a free API key at: https://openrouter.ai/keys")
        return
    
    # Initialize OpenAI client (works with OpenRouter)
    client = OpenAI(
        api_key=OPENROUTER_API_KEY,
        base_url="https://openrouter.ai/api/v1"
    )
    
    print("🔍 Fetching free models from OpenRouter...")
    free_models = get_free_models(max_models=15)
    
    if not free_models:
        print("❌ No free models found or error fetching models.")
        return
    
    print(f"✅ Found {len(free_models)} free model(s)")
    print("\nSelected models:")
    for i, model in enumerate(free_models, 1):
        print(f"  {i}. {model['name']} ({model['provider']})")
    
    # Assign personalities
    print("\n📋 Assigning personalities...")
    council_members = []
    for i, model in enumerate(free_models):
        if i < len(PERSONALITIES):
            council_members.append({
                "model": model,
                "personality": PERSONALITIES[i]
            })
            print(f"  • {model['name']} → {PERSONALITIES[i]['name']}")
    
    # Get question from user
    print("\n" + "="*60)
    question = input("Enter your question for the AI Council: ").strip()
    
    if not question:
        question = "Should we automate content moderation with AI?"
        print(f"Using default question: {question}")
    
    print("\n" + "="*60)
    print("🗳️  Collecting votes from AI Council...")
    print("="*60 + "\n")
    
    # Collect votes
    votes = []
    failed_count = 0
    for member in council_members:
        model_id = member["model"]["id"]
        personality = member["personality"]
        model_name = member["model"]["name"]
        
        print(f"🤔 {personality['name']} ({model_name}) is thinking...")
        result = get_vote_from_model(client, model_id, personality, question)
        
        if result:
            votes.append(result)
            vote_symbol = "✅" if result["vote"] == "YES" else "❌" if result["vote"] == "NO" else "➖"
            print(f"{vote_symbol} Vote: {result['vote']}")
            print(f"   Reasoning: {result['reasoning']}\n")
        else:
            failed_count += 1
        
        # Small delay to avoid rate limits
        time.sleep(0.5)
    
    # Show summary if some models failed
    if failed_count > 0:
        print(f"ℹ️  Note: {failed_count} model(s) were skipped due to errors\n")
    
    # Count votes
    print("="*60)
    print("📊 COUNCIL RESULTS")
    print("="*60)
    
    yes_count = sum(1 for v in votes if v["vote"] == "YES")
    no_count = sum(1 for v in votes if v["vote"] == "NO")
    abstain_count = sum(1 for v in votes if v["vote"] == "ABSTAIN")
    
    print(f"\n✅ YES votes: {yes_count}")
    print(f"❌ NO votes: {no_count}")
    if abstain_count > 0:
        print(f"➖ ABSTAIN votes: {abstain_count}")
    
    # Determine final verdict
    if yes_count > no_count:
        verdict = "YES (majority)"
    elif no_count > yes_count:
        verdict = "NO (majority)"
    elif yes_count == no_count and yes_count > 0:
        verdict = "TIE"
    else:
        verdict = "INCONCLUSIVE"
    
    print(f"\n🎯 Final Verdict: {verdict}")
    print("="*60)


if __name__ == "__main__":
    main()

