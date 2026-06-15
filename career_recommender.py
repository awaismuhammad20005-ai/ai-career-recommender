"""
AI Career Path Recommender System
Suggests career paths based on intern profiles, skills, and interests
"""

import os
import json
import datetime
from flask import Flask, render_template, request, jsonify, session
import openai
from dotenv import load_dotenv
import hashlib

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = 'career_recommender_secret_key_2024'

# Initialize OpenAI - FIXED VERSION
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# Configure OpenAI properly
if OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY
    client_available = True
else:
    client_available = False

# Career Database
CAREER_PATHS = {
    "Software Development": {
        "roles": ["Frontend Developer", "Backend Developer", "Full Stack Developer", "Mobile Developer"],
        "skills_needed": ["Python", "JavaScript", "React", "Node.js", "SQL", "Git"],
        "learning_path": [
            "Learn Python basics (2 weeks)",
            "Master HTML/CSS/JavaScript (3 weeks)",
            "Learn React or Vue.js (4 weeks)",
            "Build 3 portfolio projects (4 weeks)",
            "Learn backend with Node.js (3 weeks)",
            "Database design and SQL (2 weeks)",
            "Apply for junior developer roles"
        ],
        "salary_range": "$60,000 - $120,000",
        "growth_rate": "22% (Much faster than average)",
        "entry_level": "Junior Developer",
        "mid_level": "Software Engineer",
        "senior_level": "Senior/Lead Developer"
    },
    "Data Science & AI": {
        "roles": ["Data Analyst", "Data Scientist", "ML Engineer", "AI Researcher"],
        "skills_needed": ["Python", "SQL", "Statistics", "Machine Learning", "TensorFlow", "Data Visualization"],
        "learning_path": [
            "Learn Python and libraries (3 weeks)",
            "Master statistics and probability (3 weeks)",
            "Learn SQL and database (2 weeks)",
            "Machine Learning fundamentals (4 weeks)",
            "Deep learning with TensorFlow (4 weeks)",
            "Build data science portfolio (4 weeks)",
            "Apply for data analyst/scientist roles"
        ],
        "salary_range": "$70,000 - $140,000",
        "growth_rate": "35% (Very high demand)",
        "entry_level": "Data Analyst",
        "mid_level": "Data Scientist",
        "senior_level": "Senior Data Scientist/ML Engineer"
    },
    "Cloud Computing": {
        "roles": ["Cloud Engineer", "DevOps Engineer", "Site Reliability Engineer", "Cloud Architect"],
        "skills_needed": ["AWS/Azure/GCP", "Docker", "Kubernetes", "Linux", "CI/CD", "Terraform"],
        "learning_path": [
            "Learn Linux fundamentals (2 weeks)",
            "Master Docker containers (2 weeks)",
            "Learn cloud platform (AWS/Azure) (4 weeks)",
            "Kubernetes orchestration (3 weeks)",
            "CI/CD pipelines (2 weeks)",
            "Infrastructure as Code (2 weeks)",
            "Get cloud certification (4 weeks)"
        ],
        "salary_range": "$80,000 - $150,000",
        "growth_rate": "25% (Very high demand)",
        "entry_level": "Cloud Support Associate",
        "mid_level": "Cloud Engineer",
        "senior_level": "Cloud Architect"
    },
    "Cybersecurity": {
        "roles": ["Security Analyst", "Penetration Tester", "Security Engineer", "SOC Analyst"],
        "skills_needed": ["Networking", "Linux", "Python", "Security Tools", "Cryptography", "Risk Assessment"],
        "learning_path": [
            "Learn networking basics (2 weeks)",
            "Master Linux security (2 weeks)",
            "Learn Python for security (3 weeks)",
            "Security tools (Nmap, Wireshark) (2 weeks)",
            "Ethical hacking concepts (3 weeks)",
            "Get Security+ certification (3 weeks)",
            "Apply for security analyst roles"
        ],
        "salary_range": "$75,000 - $130,000",
        "growth_rate": "32% (Critical demand)",
        "entry_level": "Junior Security Analyst",
        "mid_level": "Security Engineer",
        "senior_level": "Security Architect"
    },
    "DevOps": {
        "roles": ["DevOps Engineer", "Build Engineer", "Release Manager", "Platform Engineer"],
        "skills_needed": ["Linux", "Jenkins", "Docker", "Kubernetes", "AWS", "Git", "Scripting"],
        "learning_path": [
            "Master Linux system administration (2 weeks)",
            "Learn Git and version control (1 week)",
            "Docker containers (2 weeks)",
            "CI/CD with Jenkins/GitLab (3 weeks)",
            "Kubernetes basics (3 weeks)",
            "Cloud platforms (AWS/Azure) (3 weeks)",
            "Infrastructure as Code (2 weeks)"
        ],
        "salary_range": "$85,000 - $145,000",
        "growth_rate": "24% (High demand)",
        "entry_level": "Junior DevOps Engineer",
        "mid_level": "DevOps Engineer",
        "senior_level": "Senior DevOps/Platform Engineer"
    },
    "UI/UX Design": {
        "roles": ["UI Designer", "UX Designer", "Product Designer", "UX Researcher"],
        "skills_needed": ["Figma", "Adobe XD", "User Research", "Wireframing", "Prototyping", "HTML/CSS"],
        "learning_path": [
            "Learn design principles (2 weeks)",
            "Master Figma/Adobe XD (3 weeks)",
            "User research methods (2 weeks)",
            "Wireframing and prototyping (2 weeks)",
            "Build portfolio (4 weeks)",
            "Learn basic HTML/CSS (2 weeks)",
            "Apply for junior design roles"
        ],
        "salary_range": "$55,000 - $110,000",
        "growth_rate": "13% (Steady growth)",
        "entry_level": "Junior UI/UX Designer",
        "mid_level": "UI/UX Designer",
        "senior_level": "Senior Product Designer"
    },
    "Project Management": {
        "roles": ["Project Coordinator", "Scrum Master", "Project Manager", "Program Manager"],
        "skills_needed": ["Agile", "Scrum", "JIRA", "Communication", "Leadership", "Risk Management"],
        "learning_path": [
            "Learn Agile methodologies (2 weeks)",
            "Master Scrum framework (2 weeks)",
            "JIRA/Trello tools (1 week)",
            "Communication skills (2 weeks)",
            "Get Scrum Master certification (3 weeks)",
            "Risk management basics (2 weeks)",
            "Apply for coordinator roles"
        ],
        "salary_range": "$65,000 - $120,000",
        "growth_rate": "11% (Average growth)",
        "entry_level": "Project Coordinator",
        "mid_level": "Project Manager",
        "senior_level": "Senior Program Manager"
    }
}

# User progress storage (in-memory for demo)
user_progress = {}

def get_ai_recommendation(skills, interests, experience_level):
    """Get AI-powered career recommendations"""
    
    if not client_available:
        return get_fallback_recommendation(skills, interests, experience_level)
    
    prompt = f"""
    You are a career counselor. Based on the following intern profile, recommend the top 3 career paths.
    
    Skills: {skills}
    Interests: {interests}
    Experience Level: {experience_level}
    
    Return ONLY valid JSON with this structure:
    {{
        "recommendations": [
            {{
                "career": "Career name",
                "match_score": "90%",
                "reason": "Why this fits",
                "estimated_time": "3-6 months",
                "starting_salary": "$XX,XXX",
                "job_demand": "High/Medium/Low"
            }}
        ],
        "learning_resources": [
            "Resource 1",
            "Resource 2",
            "Resource 3"
        ],
        "next_steps": [
            "Step 1",
            "Step 2",
            "Step 3"
        ]
    }}
    """
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=800
        )
        
        result = response.choices[0].message.content
        result = result.replace('```json', '').replace('```', '')
        return json.loads(result)
        
    except Exception as e:
        print(f"OpenAI error: {e}")
        return get_fallback_recommendation(skills, interests, experience_level)

def get_fallback_recommendation(skills, interests, experience_level):
    """Fallback recommendation based on keyword matching"""
    
    skills_lower = skills.lower()
    interests_lower = interests.lower()
    
    recommendations = []
    
    # Match based on keywords
    if any(word in skills_lower or word in interests_lower for word in ['python', 'java', 'javascript', 'coding', 'program']):
        recommendations.append({
            "career": "Software Development",
            "match_score": "92%",
            "reason": "Strong programming interest and skills",
            "estimated_time": "3-6 months",
            "starting_salary": "$60,000 - $75,000",
            "job_demand": "Very High"
        })
    
    if any(word in skills_lower or word in interests_lower for word in ['data', 'analytics', 'statistics', 'ml', 'ai']):
        recommendations.append({
            "career": "Data Science & AI",
            "match_score": "88%",
            "reason": "Interest in data and analytics",
            "estimated_time": "4-8 months",
            "starting_salary": "$65,000 - $80,000",
            "job_demand": "Very High"
        })
    
    if any(word in skills_lower or word in interests_lower for word in ['cloud', 'aws', 'azure', 'devops', 'docker']):
        recommendations.append({
            "career": "Cloud Computing",
            "match_score": "85%",
            "reason": "Cloud and infrastructure interest",
            "estimated_time": "3-6 months",
            "starting_salary": "$70,000 - $85,000",
            "job_demand": "Very High"
        })
    
    if any(word in skills_lower or word in interests_lower for word in ['security', 'cyber', 'hacking', 'protect']):
        recommendations.append({
            "career": "Cybersecurity",
            "match_score": "87%",
            "reason": "Security-focused mindset",
            "estimated_time": "4-7 months",
            "starting_salary": "$65,000 - $80,000",
            "job_demand": "High"
        })
    
    if any(word in skills_lower or word in interests_lower for word in ['design', 'ui', 'ux', 'figma', 'creative']):
        recommendations.append({
            "career": "UI/UX Design",
            "match_score": "86%",
            "reason": "Creative and design-oriented",
            "estimated_time": "3-5 months",
            "starting_salary": "$50,000 - $65,000",
            "job_demand": "High"
        })
    
    # Add default if no matches
    if not recommendations:
        recommendations.append({
            "career": "Software Development",
            "match_score": "75%",
            "reason": "Versatile career with many opportunities",
            "estimated_time": "3-6 months",
            "starting_salary": "$60,000 - $75,000",
            "job_demand": "High"
        })
    
    return {
        "recommendations": recommendations[:3],
        "learning_resources": [
            "Coursera: Career specific courses",
            "Udemy: Practical skill development",
            "LinkedIn Learning: Professional skills",
            "GitHub: Open source contribution"
        ],
        "next_steps": [
            "Complete skills assessment",
            "Choose top career match",
            "Start recommended learning path",
            "Build portfolio projects",
            "Network with professionals"
        ]
    }

@app.route('/')
def index():
    """Main page"""
    return render_template('career_recommender.html')

@app.route('/recommend', methods=['POST'])
def recommend():
    """Get career recommendations"""
    data = request.json
    skills = data.get('skills', '')
    interests = data.get('interests', '')
    experience = data.get('experience', 'Beginner')
    
    if not skills or not interests:
        return jsonify({'error': 'Please provide both skills and interests'}), 400
    
    # Get AI recommendation
    ai_rec = get_ai_recommendation(skills, interests, experience)
    
    # Get detailed career info for top match
    top_career = ai_rec['recommendations'][0]['career']
    career_details = CAREER_PATHS.get(top_career, CAREER_PATHS["Software Development"])
    
    # Create user session
    user_id = hashlib.md5(f"{skills}{interests}{datetime.datetime.now()}".encode()).hexdigest()
    
    response = {
        "user_id": user_id,
        "recommendations": ai_rec['recommendations'],
        "top_career": {
            "name": top_career,
            "details": career_details,
            "learning_path": career_details['learning_path'],
            "roles": career_details['roles'],
            "salary_range": career_details['salary_range'],
            "growth_rate": career_details['growth_rate']
        },
        "learning_resources": ai_rec['learning_resources'],
        "next_steps": ai_rec['next_steps']
    }
    
    return jsonify(response)

@app.route('/track', methods=['POST'])
def track_progress():
    """Track user progress"""
    data = request.json
    user_id = data.get('user_id')
    career_path = data.get('career_path')
    completed_steps = data.get('completed_steps', [])
    progress_percentage = data.get('progress_percentage', 0)
    
    if user_id not in user_progress:
        user_progress[user_id] = {}
    
    user_progress[user_id][career_path] = {
        'completed_steps': completed_steps,
        'progress_percentage': progress_percentage,
        'last_updated': datetime.datetime.now().isoformat(),
        'start_date': user_progress[user_id].get(career_path, {}).get('start_date', datetime.datetime.now().isoformat())
    }
    
    # Generate motivational message
    message = ""
    if progress_percentage >= 75:
        message = "🎉 Amazing progress! You're almost there! Keep pushing!"
    elif progress_percentage >= 50:
        message = "🌟 Great job! You're halfway there. Stay motivated!"
    elif progress_percentage >= 25:
        message = "💪 Good progress! Every step brings you closer to your goal!"
    else:
        message = "🚀 You've started your journey! Consistency is key!"
    
    return jsonify({
        'status': 'success',
        'message': message,
        'progress': progress_percentage,
        'next_milestone': get_next_milestone(progress_percentage)
    })

def get_next_milestone(progress):
    """Get next milestone based on progress"""
    if progress < 25:
        return "Complete 25% of your learning path"
    elif progress < 50:
        return "Complete 50% of your learning path"
    elif progress < 75:
        return "Complete 75% of your learning path"
    elif progress < 100:
        return "Complete 100% and start applying"
    else:
        return "You've completed the learning path! Time to apply!"

@app.route('/get_progress', methods=['GET'])
def get_progress():
    """Get user progress"""
    user_id = request.args.get('user_id')
    career_path = request.args.get('career_path')
    
    if user_id in user_progress and career_path in user_progress[user_id]:
        return jsonify(user_progress[user_id][career_path])
    return jsonify({'progress_percentage': 0, 'completed_steps': []})

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🎯 AI Career Path Recommender System")
    print("="*60)
    print("🌐 URL: http://localhost:5000")
    print("💡 Features: Career recommendations, learning paths, progress tracking")
    print("="*60 + "\n")
    app.run(debug=True, host='0.0.0.0', port=5000)