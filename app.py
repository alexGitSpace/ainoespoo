from flask import Flask, render_template, request, jsonify
from openai import OpenAI
import os
import sys
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

try:
    from config.config import OPENAI_API_KEY
except ImportError:
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')

if not OPENAI_API_KEY:
    print("Warning: OPENAI_API_KEY not found. Please set it in config/config.py or as an environment variable.")
    sys.exit(1)

client = OpenAI(api_key=OPENAI_API_KEY)

app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

FORM_STEPS = [
    {'id': 'company_name', 'label': 'Company Name', 'completed': False},
    {'id': 'language', 'label': 'Language', 'completed': False},
    {'id': 'sphere', 'label': 'Business Sphere', 'completed': False},
    {'id': 'education', 'label': 'Education', 'completed': False},
    {'id': 'experience', 'label': 'Experience', 'completed': False},
    {'id': 'location', 'label': 'Location', 'completed': False},
]

BUSINESS_PLAN_SECTIONS = [
    {
        'id': 'section_1',
        'title': 'Section 1: The Big Picture',
        'description': 'Your Vision and Foundation',
        'core_questions': [
            {'id': 'business_idea', 'label': 'Your Business Idea', 'fill': 'In a few sentences: what will you sell, and who will buy it? Keep it simple and clear.'},
            {'id': 'vision_3_5_years', 'label': 'Your Vision (3–5 years)', 'fill': 'Imagine your business in 3-5 years. What does it look like? What impact are you making? Don\'t be afraid to dream a little.'},
            {'id': 'skills_passion', 'label': 'Your Skills & Passion', 'fill': 'What experience, skills, or passion do you have that relates to this business? Why are YOU the right person to do this?'},
        ],
        'optional_questions': [
            {'id': 'industry', 'label': 'Industry', 'fill': 'Briefly describe your industry, typical price levels, and trends affecting you (e.g., seasonality, regulation, technology). Keep to 3–5 bullets.'},
        ]
    },
    {
        'id': 'section_2',
        'title': 'Section 2: Your Market, Customers, and Offer',
        'description': 'Who you\'re serving and what you\'re selling',
        'core_questions': [
            {'id': 'ideal_customer', 'label': 'Your Ideal Customer', 'fill': 'Describe 1-2 types of customers you want to serve (e.g., small cafes in Helsinki, busy parents). Are they consumers (B2C) or other businesses (B2B)?'},
            {'id': 'problem_you_solve', 'label': 'The Problem You Solve', 'fill': 'What specific problem, need, or desire does your product/service address for your ideal customer? Why would they pay for your solution?'},
            {'id': 'products_services_pricing', 'label': 'Your Products, Services & Pricing', 'fill': 'List your main 1-3 products or services. How will you charge for them (e.g., per hour, fixed price, subscription)? What is a rough price point and your estimated cost per unit?'},
            {'id': 'differentiation', 'label': 'What Makes You Different?', 'fill': 'Who are your top 2-3 competitors or alternatives? What is the main reason a customer would choose you over them? (e.g., better price, higher quality, more convenient, unique expertise).'},
        ],
        'optional_questions': [
            {'id': 'customer_purchase_criteria', 'label': 'Customer Purchase Criteria', 'fill': 'What 3–5 factors customers compare when choosing (e.g., price, speed, quality, location, reviews, warranty, language, payment options). Rank them by importance.'},
            {'id': 'customer_risks', 'label': 'Customer Risks', 'fill': 'List things that might stop a customer from buying (e.g., price too high, trust, delivery delay, privacy concerns). Add how you will reduce each risk.'},
        ]
    },
    {
        'id': 'section_3',
        'title': 'Section 3: Operations and Go-to-Market',
        'description': 'How you\'ll run the business and reach customers',
        'core_questions': [
            {'id': 'launch_plan', 'label': 'Your Launch Plan', 'fill': 'What are the first few practical steps you will take to get your first customer in the first 3 months? (e.g., build a simple website, contact 10 potential clients, run a small social media ad).'},
            {'id': 'sales_marketing_channels', 'label': 'Sales & Marketing Channels', 'fill': 'How will your first customers hear about you? Pick 1-2 channels to start with (e.g., Instagram, local networking events, Google search, word-of-mouth).'},
        ],
        'optional_questions': [
            {'id': 'production_logistics', 'label': 'Production and logistics (goods)', 'fill': 'If you sell goods: where you get them, minimum order sizes, lead times, shipping methods/costs, return process, and main cost drivers.'},
            {'id': 'delivery_operations', 'label': 'Delivery operations (services)', 'fill': 'If you sell services: how you deliver, hours of operation, tools/software used, capacity per week, service level targets, and variable costs (e.g., travel, subcontracting).'},
            {'id': 'distribution_network', 'label': 'Distribution network', 'fill': 'List partners/channels that will sell or deliver your offer (marketplaces, resellers, distributors). Include expected share of sales and fees/commissions.'},
            {'id': 'third_parties_partners', 'label': 'Other third parties and key partners', 'fill': 'Suppliers, subcontractors, or advisors you rely on. For each: role and key terms (price, notice period).'},
            {'id': 'internationalization', 'label': 'Internationalization plans', 'fill': 'If you plan to sell outside your country: target countries, timeline, language/currency needs, and any rules you must follow.'},
        ]
    },
    {
        'id': 'section_4',
        'title': 'Section 4: Finances, Risks, and Formalities',
        'description': 'Numbers, challenges, and legal setup',
        'core_questions': [
            {'id': 'startup_costs', 'label': 'Startup Costs & Initial Financing', 'fill': 'What are the essential things you need to buy to get started (e.g., laptop, materials, website domain)? How much cash do you need to cover costs for the first 3 months? (Estimates are fine!)'},
            {'id': 'swot_analysis', 'label': 'SWOT Analysis', 'fill': 'List your top 2 strengths, weaknesses, opportunities, and threats. Be honest! This is a great way to summarize your situation.'},
            {'id': 'company_basics', 'label': 'Company Basics', 'fill': 'What is your planned company name and legal form (e.g., sole trader/toiminimi, limited company/osakeyhtiö)? Who are the owners and what are the ownership percentages?'},
        ],
        'optional_questions': [
            {'id': 'profitability_timeline', 'label': 'Profitability Timeline', 'fill': 'Estimate monthly fixed costs, expected monthly sales for months 1–6, and when you break even. Include how much cash you need until break-even (runway).'},
            {'id': 'operating_risks', 'label': 'Potential risks in the operating environment', 'fill': 'Big external risks you cannot control (e.g., regulation changes, supplier issues, economic downturn). For each, note likelihood (low/med/high) and a simple backup plan.'},
            {'id': 'intellectual_property', 'label': 'Intellectual Property', 'fill': 'Names/brands, domains, designs, or inventions. Say if registered/applied, and any next steps (e.g., file trademark).'},
            {'id': 'permits_notices', 'label': 'Permits and notices', 'fill': 'Licenses/permits you may need (food, construction, health), who issues them, and expected timing/cost.'},
            {'id': 'insurance', 'label': 'Insurance', 'fill': 'What insurance you plan to have (liability, professional, product, property). Add estimated annual premium or a quote if available.'},
            {'id': 'key_contracts', 'label': 'Key contracts', 'fill': 'Any important contracts you need or already have (supplier, landlord, key customer). Note main terms (length, price, termination).'},
        ]
    }
]

form_data = {}
chat_history = []

TIERS = [
    {'id': 'beginner', 'name': 'Beginner', 'points_required': 0, 'icon': '🌱'},
    {'id': 'motivated_entrepreneur', 'name': 'Motivated Entrepreneur', 'points_required': 3, 'icon': '🚀'},
    {'id': 'growing_entrepreneur', 'name': 'Growing Entrepreneur', 'points_required': 6, 'icon': '🌟'},
    {'id': 'experienced_business_professional', 'name': 'Experienced Business Professional', 'points_required': 10, 'icon': '💼'},
    {'id': 'master_entrepreneur', 'name': 'Master Entrepreneur', 'points_required': 20, 'icon': '👑'}
]


def calculate_points(form_data):
    points = 0
    if form_data.get('company_name'):
        points += 1
    if form_data.get('language'):
        points += 1
    if form_data.get('sphere'):
        points += 1
    if form_data.get('education'):
        points += 1
    if form_data.get('experience'):
        points += 1
    if form_data.get('location'):
        points += 1
    return points


def get_current_tier(points):
    current_tier = TIERS[0]
    for tier in reversed(TIERS):
        if points >= tier['points_required']:
            current_tier = tier
            break
    return current_tier


def is_initial_form_complete(form_data):
    return all(form_data.get(step['id']) for step in FORM_STEPS)


def get_current_business_plan_question(form_data):
    for section in BUSINESS_PLAN_SECTIONS:
        for question in section['core_questions']:
            if not form_data.get(question['id']):
                return section, question, 'core'
        for question in section['optional_questions']:
            if not form_data.get(question['id']):
                return section, question, 'optional'
    return None, None, None


def get_business_plan_progress(form_data):
    progress = []
    
    preliminary_progress = {
        'section_id': 'section_0',
        'title': 'Section 0: Basic Information',
        'description': 'Your company and background details',
        'core_completed': [],
        'core_total': len(FORM_STEPS),
        'optional_completed': [],
        'optional_total': 0
    }
    for step in FORM_STEPS:
        if form_data.get(step['id']):
            preliminary_progress['core_completed'].append(step['id'])
    progress.append(preliminary_progress)
    
    for section in BUSINESS_PLAN_SECTIONS:
        section_progress = {
            'section_id': section['id'],
            'title': section['title'],
            'description': section['description'],
            'core_completed': [],
            'core_total': len(section['core_questions']),
            'optional_completed': [],
            'optional_total': len(section['optional_questions'])
        }
        for question in section['core_questions']:
            if form_data.get(question['id']):
                section_progress['core_completed'].append(question['id'])
        for question in section['optional_questions']:
            if form_data.get(question['id']):
                section_progress['optional_completed'].append(question['id'])
        progress.append(section_progress)
    return progress


def get_step_prompt(current_step, form_data):
    if current_step and current_step.startswith('bp_'):
        section, question, question_type = get_current_business_plan_question(form_data)
        if section and question:
            context_parts = []
            if form_data.get('company_name'):
                context_parts.append(f"Company: {form_data['company_name']}")
            if form_data.get('sphere'):
                context_parts.append(f"Business Sphere: {form_data['sphere']}")
            
            context = f"Context: {', '.join(context_parts)}. " if context_parts else ""
            
            section_info = f"We're working on {section['title']} - {section['description']}."
            question_instruction = f"Ask about: {question['label']}. {question['fill']}"
            
            if question_type == 'optional':
                question_instruction += " (This is an optional deeper dive question - they can skip if they prefer.)"
            
            return f"""You are a friendly business advisor assistant helping create a comprehensive business plan. {context}
{section_info}
Current question: {question_instruction}
Keep responses concise (1-2 sentences) and conversational. Be encouraging and supportive."""
        else:
            return """You are a friendly business advisor assistant. All business plan questions have been completed.
Thank them for their thorough responses and let them know their business plan information has been collected."""
    
    step_descriptions = {
        'company_name': "Ask for the company name. Be friendly and welcoming.",
        'language': "Ask for the preferred language (e.g., English, Spanish, French, German).",
        'sphere': "Ask what industry or business sphere the company operates in.",
        'education': "Ask about the educational background (e.g., Bachelor's in Business, MBA, etc.).",
        'experience': "Ask how many years of business experience they have.",
        'location': "Ask where the business is located."
    }
    
    collected_info = []
    if form_data.get('company_name'):
        collected_info.append(f"Company Name: {form_data['company_name']}")
    if form_data.get('language'):
        collected_info.append(f"Language: {form_data['language']}")
    if form_data.get('sphere'):
        collected_info.append(f"Business Sphere: {form_data['sphere']}")
    if form_data.get('education'):
        collected_info.append(f"Education: {form_data['education']}")
    if form_data.get('experience'):
        collected_info.append(f"Experience: {form_data['experience']}")
    if form_data.get('location'):
        collected_info.append(f"Location: {form_data['location']}")
    
    context = ""
    if collected_info:
        context = f"Information collected so far: {', '.join(collected_info)}. "
    
    current_task = step_descriptions.get(current_step, "Continue the conversation naturally.")
    
    if current_step == 'location':
        return f"""You are a friendly business form assistant helping to collect information. {context}
Current task: {current_task}
After collecting the location, congratulate them on completing the initial form and introduce the business plan checklist. Explain that you'll now help them work through a comprehensive business plan with 4 sections covering vision, market, operations, and finances.
Keep responses concise (1-2 sentences) and conversational."""
    elif current_step == 'complete':
        if not form_data.get('email'):
            return f"""You are a friendly business form assistant. All required information has been collected:
{', '.join(collected_info)}
Now, please ask for their email address so we can send them a summary report of the information they provided.
Keep responses concise and conversational."""
        else:
            return f"""You are a friendly business form assistant. All information including email has been collected.
Thank them for completing the form and let them know that a report will be sent to their email address shortly.
Keep responses concise and conversational."""
    else:
        next_steps = []
        for step in FORM_STEPS:
            if step['id'] == current_step:
                idx = FORM_STEPS.index(step)
                if idx + 1 < len(FORM_STEPS):
                    next_steps.append(step_descriptions[FORM_STEPS[idx + 1]['id']])
                break
        
        next_hint = (f" After collecting this information, you'll ask about:"
                     f" {next_steps[0] if next_steps else 'completion'}.") if next_steps else ""
        
        return f"""You are a friendly business form assistant helping to collect information. {context}
Current task: {current_task}{next_hint}
Keep responses concise (1-2 sentences) and conversational. 
Acknowledge their input and naturally move to the next question."""


def get_openai_response(user_message, current_step):
    global chat_history
    
    try:
        context_message = get_step_prompt(current_step, form_data)
        
        system_message = {
            'role': 'system',
            'content': context_message
        }
        
        messages = [system_message]
        
        if chat_history:
            messages.extend(chat_history[-10:])
        
        messages.append({
            'role': 'user',
            'content': user_message
        })
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.7,
            max_tokens=200
        )
        
        ai_message = response.choices[0].message.content.strip()
        
        chat_history.append({
            'role': 'user',
            'content': user_message
        })
        chat_history.append({
            'role': 'assistant',
            'content': ai_message
        })
        
        should_advance = False
        if current_step == 'company_name' and len(user_message.strip()) > 1:
            should_advance = True
        elif current_step == 'language' and len(user_message.strip()) > 1:
            should_advance = True
        elif current_step == 'sphere' and len(user_message.strip()) > 2:
            should_advance = True
        elif current_step == 'education' and len(user_message.strip()) > 2:
            should_advance = True
        elif current_step == 'experience' and len(user_message.strip()) > 0:
            should_advance = True
        elif current_step == 'location' and len(user_message.strip()) > 2:
            should_advance = True
        
        if should_advance and current_step != 'complete':
            next_step_idx = None
            for idx, step in enumerate(FORM_STEPS):
                if step['id'] == current_step:
                    if idx + 1 < len(FORM_STEPS):
                        next_step_idx = idx + 1
                    else:
                        next_step_idx = 'complete'
                    break
            
            if next_step_idx == 'complete':
                return {'message': ai_message, 'step': 'complete'}
            elif next_step_idx is not None:
                return {'message': ai_message, 'step': FORM_STEPS[next_step_idx]['id']}
        
        return {'message': ai_message, 'step': current_step}
    
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Chat API error: {error_details}")
        return {
            'message': f"I apologize, but I encountered an error. Please try again. Error: {str(e)}",
            'step': current_step
        }


@app.route('/')
def index():
    return render_template('index.html', steps=FORM_STEPS)


@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message', '').strip()
    
    if not user_message:
        return jsonify({'error': 'Message is required'}), 400
    
    initial_form_complete = is_initial_form_complete(form_data)
    current_step = None
    
    if not initial_form_complete:
        for step in FORM_STEPS:
            if not form_data.get(step['id']):
                current_step = step['id']
                break
        
        if current_step == 'company_name' and len(user_message.strip()) > 1:
            form_data['company_name'] = user_message
        elif current_step == 'language':
            lang_map = {
                'english': 'English',
                'spanish': 'Spanish',
                'french': 'French',
                'german': 'German'
            }
            user_lower = user_message.lower()
            for key, value in lang_map.items():
                if key in user_lower:
                    form_data['language'] = value
                    break
            if not form_data.get('language'):
                form_data['language'] = user_message
        elif current_step == 'sphere' and len(user_message.strip()) > 2:
            form_data['sphere'] = user_message
        elif current_step == 'education' and len(user_message.strip()) > 2:
            form_data['education'] = user_message
        elif current_step == 'experience' and len(user_message.strip()) > 0:
            form_data['experience'] = user_message
        elif current_step == 'location' and len(user_message.strip()) > 2:
            form_data['location'] = user_message
    else:
        section, question, question_type = get_current_business_plan_question(form_data)
        if section and question:
            current_step = f"bp_{question['id']}"
            if len(user_message.strip()) > 2:
                form_data[question['id']] = user_message
        else:
            current_step = 'bp_complete'
    
    if not form_data.get('email'):
        import re
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        email_match = re.search(email_pattern, user_message)
        if email_match:
            form_data['email'] = email_match.group()
        elif '@' in user_message and len(user_message.strip()) > 5:
            potential_email = user_message.strip()
            if '.' in potential_email.split('@')[1] if '@' in potential_email else False:
                form_data['email'] = potential_email
    
    if current_step is None:
        current_step = 'complete' if not initial_form_complete else 'bp_complete'
    
    response = get_openai_response(user_message, current_step)
    
    completed_steps = []
    for step in FORM_STEPS:
        if form_data.get(step['id']):
            completed_steps.append(step['id'])
    
    business_plan_progress = get_business_plan_progress(form_data)
    
    email_collected = form_data.get('email') is not None
    report_sent = False
    
    if email_collected and initial_form_complete and not form_data.get('report_sent'):
        section, question, _ = get_current_business_plan_question(form_data)
        if not section:
            try:
                send_report_email(form_data)
                form_data['report_sent'] = True
                report_sent = True
            except Exception as e:
                print(f"Error sending email: {str(e)}")
    
    points = calculate_points(form_data)
    current_tier = get_current_tier(points)
    
    return jsonify({
        'response': response['message'],
        'completed_steps': completed_steps,
        'business_plan_progress': business_plan_progress,
        'initial_form_complete': initial_form_complete,
        'form_data': form_data.copy(),
        'email_collected': email_collected,
        'report_sent': report_sent,
        'points': points,
        'current_tier': current_tier['id'],
        'tiers': TIERS
    })


@app.route('/api/tts', methods=['POST'])
def text_to_speech():
    data = request.json
    text = data.get('text', '').strip()
    
    if not text:
        return jsonify({'error': 'Text is required'}), 400
    
    try:
        audio_response = client.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input=text
        )
        
        import base64
        audio_data = audio_response.read()
        audio_base64 = base64.b64encode(audio_data).decode('utf-8')
        
        return jsonify({
            'audio': audio_base64,
            'format': 'mp3'
        })
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"TTS error: {error_details}")
        return jsonify({'error': f'TTS failed: {str(e)}'}), 500


@app.route('/api/transcribe', methods=['POST'])
def transcribe():
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file provided'}), 400
    
    audio_file = request.files['audio']
    if audio_file.filename == '':
        return jsonify({'error': 'No audio file selected'}), 400
    
    try:
        audio_file.seek(0)
        file_content = audio_file.read()
        audio_file.seek(0)
        
        filename = audio_file.filename or 'audio.webm'
        content_type = audio_file.content_type or 'audio/webm'
        
        transcription = client.audio.transcriptions.create(
            model="whisper-1",
            file=(filename, file_content, content_type)
        )
        return jsonify({'text': transcription.text})
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Transcription error: {error_details}")
        return jsonify({'error': f'Transcription failed: {str(e)}'}), 500


def generate_report(form_data):
    report = f"""
BUSINESS INFORMATION FORM REPORT
{'=' * 50}

Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

COMPANY INFORMATION
{'-' * 50}
Company Name: {form_data.get('company_name', 'N/A')}
Business Sphere: {form_data.get('sphere', 'N/A')}
Location: {form_data.get('location', 'N/A')}

PERSONAL INFORMATION
{'-' * 50}
Preferred Language: {form_data.get('language', 'N/A')}
Education: {form_data.get('education', 'N/A')}
Experience: {form_data.get('experience', 'N/A')}

CONTACT INFORMATION
{'-' * 50}
Email: {form_data.get('email', 'N/A')}

{'=' * 50}

This report was generated automatically by the Business Form Assistant.
Thank you for providing your information!
"""
    return report


def send_report_email(form_data):
    try:
        email_config = {}
        try:
            from config.config import SMTP_SERVER, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, FROM_EMAIL
            email_config = {
                'server': SMTP_SERVER,
                'port': SMTP_PORT,
                'username': SMTP_USERNAME,
                'password': SMTP_PASSWORD,
                'from_email': FROM_EMAIL
            }
        except ImportError:
            email_config = {
                'server': os.environ.get('SMTP_SERVER', 'smtp.gmail.com'),
                'port': int(os.environ.get('SMTP_PORT', '587')),
                'username': os.environ.get('SMTP_USERNAME', ''),
                'password': os.environ.get('SMTP_PASSWORD', ''),
                'from_email': os.environ.get('FROM_EMAIL', 'noreply@example.com')
            }
        
        if not email_config['username'] or not email_config['password']:
            print("Warning: Email configuration not found. Report will not be sent.")
            return False
        
        to_email = form_data.get('email')
        if not to_email:
            return False
        
        report_text = generate_report(form_data)
        
        msg = MIMEMultipart()
        msg['From'] = email_config['from_email']
        msg['To'] = to_email
        msg['Subject'] = 'Business Information Form Report'
        
        msg.attach(MIMEText(report_text, 'plain'))
        
        with smtplib.SMTP(email_config['server'], email_config['port']) as server:
            server.starttls()
            server.login(email_config['username'], email_config['password'])
            server.send_message(msg)
        
        return True
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        raise


@app.route('/api/send-report', methods=['POST'])
def send_report_manual():
    data = request.json
    email = data.get('email', '').strip() if data else ''
    
    if not email:
        if form_data.get('email'):
            email = form_data['email']
        else:
            return jsonify({'error': 'Email address is required. Please provide your email first.'}), 400
    
    import re
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    if not re.match(email_pattern, email):
        return jsonify({'error': 'Invalid email address format.'}), 400
    
    report_data = form_data.copy()
    report_data['email'] = email
    
    try:
        send_report_email(report_data)
        if not form_data.get('email'):
            form_data['email'] = email
        return jsonify({'success': True, 'message': 'Report sent successfully!'})
    except Exception as e:
        return jsonify({'error': f'Failed to send report: {str(e)}'}), 500


@app.route('/api/reset', methods=['POST'])
def reset():
    global form_data, chat_history
    form_data = {}
    chat_history = []
    return jsonify({'success': True})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
