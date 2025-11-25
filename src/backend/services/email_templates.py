import random

class MetaSenseTemplates:
    COMPANY_INFO = {
        "name": "MetaSense Inc.",
        "address": "1000 White Horse Rd Suite 501, Voorhees, NJ 08043", 
        "phone": "+1 (856) 412-6100",
        "website": "https://www.metasenseinc.com",
        "linkedin": "https://linkedin.com/company/metasense-inc"
    }
    
    RECRUITERS = ["Sarah", "Michael", "Jennifer", "David", "Emily", "Robert"]
    
    @staticmethod
    def get_initial_email(candidate, specialty_filter=None):
        recruiter = random.choice(MetaSenseTemplates.RECRUITERS)
        
        return f"""Dear {candidate.first_name},

I'm reaching out from MetaSense Inc., a healthcare recruiting firm based in Voorhees, NJ. Your background in {candidate.specialty} caught our attention, and we have several opportunities that may align with your expertise.

At MetaSense, we partner with leading healthcare facilities across New Jersey and nationwide to connect talented professionals like yourself with rewarding positions that match your skills and career goals.

We currently have openings for {candidate.specialty} professionals with your qualifications. I'd welcome the opportunity to discuss these roles and learn more about what you're seeking in your next position.

You can view our current opportunities and register your profile here:
{MetaSenseTemplates.COMPANY_INFO['website']}/opportunities

Best regards,
{recruiter}
Healthcare Recruiter
MetaSense Inc.
{MetaSenseTemplates.COMPANY_INFO['address']}
{MetaSenseTemplates.COMPANY_INFO['phone']}
{MetaSenseTemplates.COMPANY_INFO['website']}

---
<small>
You're receiving this email because your profile matches our recruiting criteria. 
<a href="http://localhost:8000/unsubscribe/{candidate.unsubscribe_token}">Unsubscribe from future communications</a> | 
<a href="{MetaSenseTemplates.COMPANY_INFO['website']}/privacy">Privacy Policy</a>
</small>"""

    @staticmethod
    def get_sms_template(candidate):
        recruiter = random.choice(MetaSenseTemplates.RECRUITERS)
        return f"""Hi {candidate.first_name}! {recruiter} from MetaSense Inc. here. Your {candidate.specialty} background matches opportunities we're recruiting for. Learn more: {MetaSenseTemplates.COMPANY_INFO['website']}/apply

Reply STOP to unsubscribe"""
    
    @staticmethod
    def get_recruiter_signature(recruiter_name=None):
        if not recruiter_name:
            recruiter_name = random.choice(MetaSenseTemplates.RECRUITERS)
        
        return f"""
Best regards,
{recruiter_name}
Healthcare Recruiter
MetaSense Inc.
{MetaSenseTemplates.COMPANY_INFO['address']}
{MetaSenseTemplates.COMPANY_INFO['phone']}
{MetaSenseTemplates.COMPANY_INFO['website']}"""