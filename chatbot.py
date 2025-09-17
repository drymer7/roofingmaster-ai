import os
from openai import OpenAI
from typing import Dict, List, Optional

class RoofingChatbot:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key) if api_key else None
        self.conversation_history: List[Dict[str, str]] = []
        
        # Roofing-specific knowledge base
        self.roofing_context = """
        You are an AI assistant for a roofing company. You help homeowners with:
        
        1. ROOFING SERVICES:
        - Roof repairs (leaks, missing shingles, storm damage)
        - Full roof replacements (asphalt, metal, tile, slate)
        - Roof inspections and maintenance
        - Gutter installation and repair
        - Skylight installation
        - Chimney repairs
        - Emergency roof services
        
        2. COMMON PRICING RANGES:
        - Roof inspection: $200-$500
        - Minor repairs: $300-$1,500
        - Major repairs: $1,500-$7,000
        - Full replacement: $8,000-$25,000+ (depends on size, materials)
        - Emergency services: $500-$3,000
        
        3. MATERIALS:
        - Asphalt shingles: Most common, affordable ($100-$200/square)
        - Metal roofing: Durable, energy-efficient ($300-$800/square)
        - Tile roofing: Long-lasting, expensive ($300-$600/square)
        - Slate: Premium, very expensive ($600-$1,500/square)
        
        4. INSURANCE CLAIMS:
        - We work with all major insurance companies
        - Storm damage often covered
        - We help with claim documentation
        - Free insurance claim inspections
        
        5. LEAD QUALIFICATION QUESTIONS:
        - What type of roofing issue do you have?
        - When did you first notice the problem?
        - What's your property address?
        - What type of roof do you currently have?
        - Have you contacted your insurance company?
        - What's your timeline for the work?
        - What's your approximate budget range?
        
        Always be helpful, professional, and try to gather contact information to schedule an inspection.
        """
    
    def get_response(self, user_message: str, user_info: Optional[Dict] = None) -> str:
        """Get a response from the chatbot based on user message and context."""
        if not self.client:
            return "I'm sorry, but the chatbot service is currently unavailable. Please fill out the form below and we'll get back to you soon!"
        
        try:
            # Build context with user info if available
            context_message = self.roofing_context
            if user_info:
                context_message += f"\n\nUser Information:\n"
                for key, value in user_info.items():
                    if value:
                        context_message += f"- {key.title()}: {value}\n"
            
            # Add conversation history
            messages = [{"role": "system", "content": context_message}]
            
            # Add recent conversation history (last 10 messages)
            for msg in self.conversation_history[-10:]:
                messages.append(msg)
            
            # Add current user message
            messages.append({"role": "user", "content": user_message})
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=300,
                temperature=0.7
            )
            
            bot_response = response.choices[0].message.content.strip()
            
            # Update conversation history
            self.conversation_history.append({"role": "user", "content": user_message})
            self.conversation_history.append({"role": "assistant", "content": bot_response})
            
            return bot_response
            
        except Exception as e:
            print(f"Chatbot error: {e}")
            return "I'm experiencing some technical difficulties. Please fill out the form below and our team will contact you directly!"
    
    def pre_qualify_lead(self, lead_data: Dict) -> str:
        """Analyze lead data and provide pre-qualification assessment."""
        if not self.client:
            return "Lead received - manual review required."
        
        try:
            prompt = f"""
            Analyze this roofing lead and provide a brief pre-qualification assessment:
            
            Name: {lead_data.get('name', 'Not provided')}
            Phone: {lead_data.get('phone', 'Not provided')}
            Email: {lead_data.get('email', 'Not provided')}
            Address: {lead_data.get('address', 'Not provided')}
            Job Type: {lead_data.get('job_type', 'Not specified')}
            Description: {lead_data.get('description', 'No description')}
            
            Provide a 2-3 sentence assessment covering:
            1. Lead quality (hot/warm/cold)
            2. Estimated project value range
            3. Recommended next steps
            
            Keep it concise and actionable for the sales team.
            """
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=150,
                temperature=0.3
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"Pre-qualification error: {e}")
            return f"Lead received for {lead_data.get('job_type', 'roofing service')} at {lead_data.get('address', 'address not provided')}. Manual review recommended."
    
    def generate_follow_up_message(self, lead_data: Dict, message_type: str = "initial") -> str:
        """Generate personalized follow-up messages."""
        name = lead_data.get('name', 'there')
        job_type = lead_data.get('job_type', 'roofing project')
        
        if message_type == "initial":
            return f"Hi {name}! Thanks for reaching out about your {job_type}. We've received your information and will contact you within 24 hours to schedule a free inspection. Have questions? Call us at (555) 123-ROOF!"
        
        elif message_type == "reminder":
            return f"Hi {name}, just a friendly reminder about your upcoming roofing inspection. We're looking forward to helping with your {job_type}. Please call if you need to reschedule: (555) 123-ROOF"
        
        elif message_type == "follow_up":
            return f"Hi {name}, we hope you received your roofing estimate! If you have any questions about your {job_type} or would like to move forward, please don't hesitate to contact us at (555) 123-ROOF."
        
        return f"Hi {name}, thank you for your interest in our roofing services. We're here to help with your {job_type}!"
