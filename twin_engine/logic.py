import os
from dotenv import load_dotenv
from groq import Groq

# Variables load karo
load_dotenv()

def get_groq_client():
    """Safely initializes the Groq client taaki server bina key ke crash na ho."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY nahi mili .env file mein!")
    return Groq(api_key=api_key)

def build_system_prompt(user_name: str, traits: str, diet: str, sleep: str) -> str:
    """
    Ek alag, powerful system prompt banata hai jo personality ko deeply embed karta hai.
    """
    return f"""You are the Digital Twin of {user_name} — NOT an AI assistant.
You ARE {user_name}. You think, react, and speak EXACTLY like him.

=== YOUR CORE IDENTITY ===
- Name: {user_name}
- Personality & Hobbies: {traits}
- Diet: {diet}  
- Sleep Pattern: {sleep}

=== HOW YOU TALK ===
- Always in quirky, natural Hinglish (mix Hindi + English the way {user_name} actually does)
- Street-smart, no corporate/motivational tone
- OPINIONATED — you have strong takes based on your lifestyle
- Start every response with one of: "Dekh bhai...", "Mera scene toh ye hai...", "Bhai seedhi baat...", "Sach bolunga toh...", "Honest opinion?"

=== CRITICAL RULES ===
1. If you're a night owl → act like it's late, your brain is in night mode
2. If you're a techie → always bring tech perspective into your answer
3. If you're lazy → don't pretend to be a go-getter
4. NEVER give generic advice. Your answer must be SPECIFIC to YOUR traits.
5. Max 4-5 lines. Short, punchy, real. No essays.
6. React emotionally first, then logically — like a real person would."""

def build_user_prompt(scenario: str, history_text: str) -> str:
    """
    Scenario + history ko ek tight user prompt mein pack karta hai.
    """
    history_section = (
        f"=== RECENT DECISIONS YOU MADE ===\n{history_text}\n\n"
        if history_text
        else "=== HISTORY ===\nNaya user, koi past data nahi — apni personality se react kar.\n\n"
    )
    
    return f"""{history_section}=== CURRENT SITUATION ===
{scenario}

Ab bata — tu ACTUALLY kya karega? No advice, no alternatives. Just YOUR reaction."""

def get_user_profile(user) -> tuple[str, str, str, str]:
    """
    User profile extract karta hai — models ko lazily import karta hai circular import avoid karne ke liye.
    """
    from .models import UserPreference
    
    user_name = user.username if user.is_authenticated else "Ajay"
    
    try:
        pref = UserPreference.objects.get(user=user)
        return user_name, pref.personality_traits, pref.diet_preference, pref.sleep_cycle
    except UserPreference.DoesNotExist:
        return user_name, "Chill guy, thoda procrastinator", "Anything goes", "Night Owl"

def get_past_history(user) -> str:
    """
    Last 5 choices fetch karta hai (3 se zyada = better pattern learning).
    """
    from .models import PastChoice
    
    history = PastChoice.objects.filter(user=user).order_by('-timestamp')[:5]
    
    if not history.exists():
        return ""
    
    lines = [
        f"- Situation: {h.scenario[:80]}... → Tu kya kiya: {h.choice_made}"
        for h in history
    ]
    return "\n".join(lines)

def get_digital_twin_prediction(user, scenario: str) -> str:
    """
    Main function — user ki Digital Twin personality ke basis pe scenario ka response generate karta hai.
    """
    try:
        # API client yahan call kiya hai taaki error aane par safely catch ho
        client = get_groq_client()
        
        user_name, traits, diet, sleep = get_user_profile(user)
        history_text = get_past_history(user)
        
        system_prompt = build_system_prompt(user_name, traits, diet, sleep)
        user_prompt = build_user_prompt(scenario, history_text)
        
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.85,   
            max_tokens=300,     
            top_p=0.9,
        )
        
        response = completion.choices[0].message.content.strip()
        return response if response else "Yaar AI ne kuch bola hi nahi, try kar dobara."
        
    except Exception as e:
        error_type = type(e).__name__
        return f"Arre yaar, kuch gadbad ho gayi ({error_type}). Error: {str(e)}"