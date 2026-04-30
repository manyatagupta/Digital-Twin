import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

API_KEY = os.getenv("GROQ_API_KEY") 
client = Groq(api_key=API_KEY)

def get_digital_twin_prediction(user, scenario):
    try:
        # User name ko logic ke liye Ajay set kiya hai
        user_name = user.username if user.is_authenticated else "Ajay"
        
        prompt = f"""
        You are the 'Digital Twin' of {user_name}. 
        User Scenario: {scenario}.
        
        Predict what this user will choose or do in this situation. 
        Keep the response short, quirky, and in Hinglish. 
        Start with something like 'Dekh bhai...' or 'Mere hisaab se...'
        """

        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile", 
            messages=[{"role": "user", "content": prompt}],
        )
        
        return completion.choices[0].message.content
    except Exception as e:
        return f"Arre yaar, AI connect nahi ho pa raha. Error: {str(e)}"