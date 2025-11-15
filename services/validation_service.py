from openai import OpenAI
import os
import sys
import re

try:
    from config.config import OPENAI_API_KEY
except ImportError:
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')

if not OPENAI_API_KEY:
    print("Warning: OPENAI_API_KEY not found. Please set it in config/config.py or as an environment variable.")
    sys.exit(1)

client = OpenAI(api_key=OPENAI_API_KEY)


def is_gibberish(text):
    text_clean = text.strip().lower()
    
    if len(text_clean) < 4:
        return False
    
    text_alpha = re.sub(r'[^a-z]', '', text_clean)
    
    if len(text_alpha) < 4:
        return False
    
    vowels = set('aeiou')
    vowel_count = sum(1 for char in text_alpha if char in vowels)
    consonant_count = len(text_alpha) - vowel_count
    
    if consonant_count > 0:
        vowel_ratio = vowel_count / len(text_alpha)
        if vowel_ratio < 0.15 and len(text_alpha) > 5:
            return True
    
    common_words = {
        'the', 'be', 'to', 'of', 'and', 'a', 'in', 'that', 'have', 'i',
        'it', 'for', 'not', 'on', 'with', 'he', 'as', 'you', 'do', 'at',
        'this', 'but', 'his', 'by', 'from', 'they', 'we', 'say', 'her', 'she',
        'or', 'an', 'will', 'my', 'one', 'all', 'would', 'there', 'their',
        'what', 'so', 'up', 'out', 'if', 'about', 'who', 'get', 'which',
        'go', 'me', 'when', 'make', 'can', 'like', 'time', 'no', 'just',
        'him', 'know', 'take', 'people', 'into', 'year', 'your', 'good',
        'some', 'could', 'them', 'see', 'other', 'than', 'then', 'now',
        'look', 'only', 'come', 'its', 'over', 'think', 'also', 'back',
        'after', 'use', 'two', 'how', 'our', 'work', 'first', 'well',
        'way', 'even', 'new', 'want', 'because', 'any', 'these', 'give',
        'day', 'most', 'us', 'is', 'are', 'was', 'were', 'has', 'had',
        'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did',
        'will', 'would', 'should', 'could', 'may', 'might', 'must',
        'can', 'cannot', 'shall', 'ought'
    }
    
    words = re.findall(r'\b[a-z]+\b', text_clean)
    if words:
        word_count = len(words)
        common_word_count = sum(1 for word in words if word in common_words)
        if word_count > 2 and common_word_count == 0:
            if len(text_alpha) > 8:
                return True
    
    consecutive_consonants = 0
    max_consecutive = 0
    for char in text_alpha:
        if char not in vowels:
            consecutive_consonants += 1
            max_consecutive = max(max_consecutive, consecutive_consonants)
        else:
            consecutive_consonants = 0
    
    if max_consecutive >= 5 and len(text_alpha) > 6:
        return True
    
    return False


def validate_answer(user_message, current_step, question_info=None):
    if not question_info:
        return True
    
    user_message_clean = user_message.strip()
    
    if len(user_message_clean) < 2:
        return False
    
    if user_message_clean.isdigit() and len(user_message_clean) > 3:
        return False
    
    if user_message_clean.replace(' ', '').isdigit() and len(user_message_clean.replace(' ', '')) > 3:
        return False
    
    if len(set(user_message_clean.replace(' ', ''))) < 3 and len(user_message_clean) > 5:
        return False
    
    if is_gibberish(user_message_clean):
        return False
    
    question_label = question_info.get('label', '')
    question_fill = question_info.get('fill', '')
    
    validation_prompt = f"""You are validating if a user's answer appropriately addresses a business plan question.

Question: "{question_label}"
Question context: {question_fill}

User's answer: "{user_message}"

Determine if the user's answer:
1. Actually addresses the question being asked
2. Provides meaningful information relevant to the question
3. Is not just random numbers, gibberish, or meaningless text
4. Is not just a generic response, question, or unrelated comment
5. Contains actual words or meaningful content (not just digits or symbols)

Examples of INVALID answers:
- Random numbers like "5645646" or "123456"
- Gibberish like "asdfgh" or "qwerty"
- Single words that don't answer the question
- Unrelated comments or questions

Respond with ONLY "YES" if the answer is appropriate and addresses the question, or "NO" if it does not address the question properly or is nonsensical."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {'role': 'system', 'content': validation_prompt},
                {'role': 'user', 'content': 'Validate this answer.'}
            ],
            temperature=0.3,
            max_tokens=10
        )
        
        result = response.choices[0].message.content.strip().upper()
        return result.startswith('YES')
    except Exception as e:
        print(f"Validation error: {str(e)}")
        return True

