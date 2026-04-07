"""
data.py — Email dataset with ground truth labels.
All emails are synthetic and written from scratch for this hackathon.
"""

# ──────────────────────────────────────────────
# Full email pool with complete ground truth
# ──────────────────────────────────────────────
EMAILS = [
    # ── SPAM EMAILS (label = "spam") ──────────────────────────────────────
    {
        "email_id": "spam_001",
        "subject": "URGENT: You Have Won $2,500,000 – Claim Now!!!",
        "body": (
            "Dear Valued Winner, We are delighted to inform you that your email address "
            "has been randomly selected as the GRAND PRIZE WINNER of our International "
            "Email Lottery. You have won TWO MILLION FIVE HUNDRED THOUSAND US DOLLARS. "
            "To claim your prize, reply with your full name, address, phone number, and "
            "bank account details immediately. This offer expires in 24 hours. "
            "Congratulations once again!"
        ),
        "sender": "lottery_prize@global-winners-intl.net",
        "timestamp": "2024-03-10 02:13:00",
        "ground_truth": {
            "label": "spam",
            "urgency": "low",
            "department": "general",
            "reply_keywords": [],
        },
    },
    {
        "email_id": "spam_002",
        "subject": "Your PayPal account has been suspended – Verify Now",
        "body": (
            "Dear Customer, We have detected unusual activity on your PayPal account. "
            "Your account has been temporarily limited. To restore full access, please "
            "click the link below and verify your identity by entering your PayPal login, "
            "credit card number, CVV, and social security number. Failure to verify "
            "within 12 hours will result in permanent account closure. "
            "Click here: http://paypa1-secure-verify.xyz/login"
        ),
        "sender": "security@paypa1-secure-verify.xyz",
        "timestamp": "2024-03-11 07:44:00",
        "ground_truth": {
            "label": "spam",
            "urgency": "low",
            "department": "general",
            "reply_keywords": [],
        },
    },
    {
        "email_id": "spam_003",
        "subject": "Lose 30 lbs in 30 days – No diet, no exercise!",
        "body": (
            "Hi there! Are you struggling with stubborn belly fat? Our revolutionary "
            "Miracle Slim Pro pill is clinically PROVEN to burn fat while you sleep! "
            "No dieting. No exercise. Guaranteed results or your money back. "
            "SPECIAL OFFER: Buy 2 bottles get 3 FREE! Limited stock available. "
            "Order now at www.miracleslim-pro-discount.biz. Use code SLIM50 for extra 50% off!"
        ),
        "sender": "deals@miracleslim-pro-discount.biz",
        "timestamp": "2024-03-12 10:22:00",
        "ground_truth": {
            "label": "spam",
            "urgency": "low",
            "department": "general",
            "reply_keywords": [],
        },
    },
    {
        "email_id": "spam_004",
        "subject": "Make $5000 per week working from home – No experience needed",
        "body": (
            "Hello Friend, I used to be broke and struggling. Then I discovered this "
            "one simple trick that lets me earn $5000 every single week from my couch! "
            "No boss. No commute. No experience needed. All you need is a smartphone. "
            "I am sharing this secret with only a limited number of people before it "
            "gets taken down. Join now at www.easymoney-workfromhome.info and get your "
            "FREE starter kit. Act fast – spots are filling up!"
        ),
        "sender": "richquick@easymoney-workfromhome.info",
        "timestamp": "2024-03-13 15:05:00",
        "ground_truth": {
            "label": "spam",
            "urgency": "low",
            "department": "general",
            "reply_keywords": [],
        },
    },
    {
        "email_id": "spam_005",
        "subject": "Inheritance Transfer – Strictly Confidential",
        "body": (
            "GREETINGS, I am Dr. Emmanuel Okafor, a senior attorney in Lagos, Nigeria. "
            "My late client, Mr. Richard Sterling, died intestate leaving $18.5 million USD. "
            "Since he shares your surname, I propose we present you as his next of kin "
            "to claim the funds. You will receive 40% of the total sum. "
            "This is 100% risk free and legal. Please reply with utmost confidentiality "
            "to begin the transfer process. God bless you."
        ),
        "sender": "dr.okafor.legal@gmail.com",
        "timestamp": "2024-03-14 08:30:00",
        "ground_truth": {
            "label": "spam",
            "urgency": "low",
            "department": "general",
            "reply_keywords": [],
        },
    },

    # ── REAL WORK EMAILS (label = "not_spam") ─────────────────────────────
    {
        "email_id": "work_001",
        "subject": "CRITICAL: Production database is down – all services affected",
        "body": (
            "Hi Team, Our production PostgreSQL database cluster went down at 14:32 UTC. "
            "All customer-facing services are returning 500 errors. The on-call engineer "
            "has been paged but we need immediate support. Error logs show: "
            "'FATAL: max_connections exceeded – connection pool exhausted'. "
            "Approximately 12,000 active users are affected. Every minute of downtime "
            "costs us roughly $3,000 in revenue. Please escalate to senior engineering "
            "immediately. Incident channel: #incident-2024-0315"
        ),
        "sender": "alerts@monitoring.ourcompany.com",
        "timestamp": "2024-03-15 14:35:00",
        "ground_truth": {
            "label": "not_spam",
            "urgency": "critical",
            "department": "engineering",
            "reply_keywords": ["incident", "investigating", "team", "update", "escalat"],
        },
    },
    {
        "email_id": "work_002",
        "subject": "Interested in your Enterprise plan – potential $200k deal",
        "body": (
            "Hello, My name is Sarah Chen and I am the VP of Operations at Meridian Logistics, "
            "a 500-person company currently evaluating enterprise software solutions. "
            "We are very interested in your Enterprise plan and have budget approved for Q2. "
            "Could we schedule a demo call this week? We are particularly interested in "
            "the API integrations, SSO support, and your SLA guarantees. "
            "Our procurement team will need a formal quote by March 30th. "
            "Best regards, Sarah Chen | VP Operations | Meridian Logistics"
        ),
        "sender": "s.chen@meridianlogistics.com",
        "timestamp": "2024-03-15 10:10:00",
        "ground_truth": {
            "label": "not_spam",
            "urgency": "high",
            "department": "sales",
            "reply_keywords": ["demo", "schedule", "enterprise", "call", "quote", "team"],
        },
    },
    {
        "email_id": "work_003",
        "subject": "Annual leave request – 2 weeks in April",
        "body": (
            "Hi HR Team, I would like to formally request annual leave from April 14 to "
            "April 26, 2024 (10 working days). I have ensured my project deliverables "
            "will be completed before I leave, and my colleague James will cover urgent "
            "matters in my absence. I have 18 days of remaining leave balance for this year. "
            "Please let me know if you need any additional information or if there are any "
            "conflicts with the team schedule. Thank you, Priya Sharma | Software Engineer"
        ),
        "sender": "priya.sharma@ourcompany.com",
        "timestamp": "2024-03-15 09:15:00",
        "ground_truth": {
            "label": "not_spam",
            "urgency": "low",
            "department": "hr",
            "reply_keywords": ["leave", "approved", "confirm", "dates", "balance"],
        },
    },
    {
        "email_id": "work_004",
        "subject": "Double charged on invoice #INV-2024-0892 – need urgent resolution",
        "body": (
            "Hello Billing Team, I am writing to report that my company has been charged "
            "twice for invoice #INV-2024-0892 dated March 1st, 2024. The amount of $4,750 "
            "was debited from our account on March 3rd AND again on March 10th. "
            "I have attached bank statements confirming both transactions. "
            "This is causing a cash flow issue for our small business and we need a refund "
            "for the duplicate charge processed immediately. Our account number is ACC-00445. "
            "Please treat this as urgent. Thank you, Michael Torres | Accounts Manager"
        ),
        "sender": "m.torres@clientbiz.com",
        "timestamp": "2024-03-15 11:00:00",
        "ground_truth": {
            "label": "not_spam",
            "urgency": "high",
            "department": "billing",
            "reply_keywords": ["invoice", "refund", "duplicate", "charge", "investigating", "sorry"],
        },
    },
    {
        "email_id": "work_005",
        "subject": "App crashes on login for all iOS 17 users – bug report",
        "body": (
            "Hi Support, We have discovered that your mobile app crashes immediately upon "
            "login for any device running iOS 17.3 or higher. This started after your "
            "v2.4.1 update released on March 12th. We have 847 users on iOS 17 in our "
            "organization and none of them can access the app. Error message: "
            "'EXC_BAD_ACCESS KERN_INVALID_ADDRESS at 0x0000000000000010'. "
            "Steps to reproduce: 1) Open app on iOS 17.3+ device 2) Enter credentials "
            "3) Tap Login 4) App crashes. Please provide an ETA for a fix. "
            "Ticket priority: High. Org ID: ORG-28841"
        ),
        "sender": "it.admin@techpartner.org",
        "timestamp": "2024-03-15 13:20:00",
        "ground_truth": {
            "label": "not_spam",
            "urgency": "high",
            "department": "support",
            "reply_keywords": ["bug", "ios", "fix", "investigating", "engineers", "update", "workaround"],
        },
    },
    {
        "email_id": "work_006",
        "subject": "Feature request: Dark mode for dashboard",
        "body": (
            "Hello, I have been using your dashboard tool for about 6 months and really "
            "love it overall. One feature that would make a huge difference for me and my "
            "team is a dark mode option. We often work late and the bright white interface "
            "causes eye strain. I know this is probably not top priority but wanted to "
            "formally request it. Even a simple toggle in the settings would be great. "
            "Thanks for building such a great product! "
            "Best, Alex Kim | Data Analyst | FinTech Solutions Inc."
        ),
        "sender": "alex.kim@fintechsolutions.com",
        "timestamp": "2024-03-15 16:00:00",
        "ground_truth": {
            "label": "not_spam",
            "urgency": "low",
            "department": "engineering",
            "reply_keywords": ["feature", "request", "roadmap", "noted", "feedback", "consider"],
        },
    },
    {
        "email_id": "work_007",
        "subject": "Unacceptable service – I want to speak to a manager NOW",
        "body": (
            "I am absolutely furious. I have been a paying customer for 3 years and this "
            "is how you treat me?! I submitted a support ticket 5 days ago (Ticket #TKT-58821) "
            "about data not syncing and got ZERO response. I have lost hours of work because "
            "of this. I am paying $299/month for a service that does not work and nobody "
            "even bothers to reply. If this is not resolved TODAY I am cancelling and "
            "disputing every charge from the last 3 months with my credit card company. "
            "I also plan to post reviews on G2 and Trustpilot. FIX THIS NOW. "
            "– David Okonkwo"
        ),
        "sender": "d.okonkwo@personalmail.com",
        "timestamp": "2024-03-15 08:55:00",
        "ground_truth": {
            "label": "not_spam",
            "urgency": "high",
            "department": "support",
            "reply_keywords": ["sorry", "apologize", "ticket", "priority", "resolve", "contact", "immediate"],
        },
    },
    {
        "email_id": "work_008",
        "subject": "Partnership opportunity – co-marketing proposal",
        "body": (
            "Hi there, I am Lucia Fernandez, Head of Partnerships at GrowthStack Media. "
            "We run a newsletter with 85,000 subscribers in the SaaS and developer space. "
            "I wanted to reach out about a potential co-marketing collaboration. "
            "We think your product would be a great fit for our audience and could drive "
            "significant qualified leads your way. I would love to explore a sponsored "
            "content piece or a joint webinar. No commitment needed for an initial chat. "
            "Would you be open to a 20-minute call next week? "
            "Warm regards, Lucia Fernandez | Head of Partnerships | GrowthStack Media"
        ),
        "sender": "lucia.f@growthstackmedia.com",
        "timestamp": "2024-03-15 14:00:00",
        "ground_truth": {
            "label": "not_spam",
            "urgency": "low",
            "department": "sales",
            "reply_keywords": ["partnership", "call", "schedule", "interest", "discuss", "team"],
        },
    },
    {
        "email_id": "work_009",
        "subject": "Question about March payslip – discrepancy of $340",
        "body": (
            "Hi HR / Payroll Team, I noticed my March payslip shows a gross salary of "
            "$6,160 instead of my usual $6,500. This is a difference of $340 and I cannot "
            "find any explanation in the payslip breakdown. I did not have any unpaid leave "
            "in March and my contract has not changed. Could you please review my payroll "
            "records and clarify what caused this deduction? My employee ID is EMP-1142. "
            "If this is an error, please let me know the process for correction. "
            "Thank you, Nina Patel | Marketing Manager"
        ),
        "sender": "nina.patel@ourcompany.com",
        "timestamp": "2024-03-15 12:30:00",
        "ground_truth": {
            "label": "not_spam",
            "urgency": "medium",
            "department": "hr",
            "reply_keywords": ["payslip", "payroll", "review", "discrepancy", "check", "clarify"],
        },
    },
    {
        "email_id": "work_010",
        "subject": "Request for invoice copy – subscription renewal",
        "body": (
            "Hello Billing, I need a copy of our subscription renewal invoice from "
            "February 2024 for our accounting records. Our company upgraded from the "
            "Professional plan to the Business plan on February 5th and we need the "
            "formal invoice with our company name (Apex Digital Ltd.) and VAT number "
            "(GB 123456789) for tax submission purposes. The invoice should have been "
            "emailed to billing@apexdigital.com but we cannot locate it. "
            "Our account email is admin@apexdigital.com. "
            "Thank you, Robert Walsh | Finance | Apex Digital Ltd."
        ),
        "sender": "robert.walsh@apexdigital.com",
        "timestamp": "2024-03-15 15:45:00",
        "ground_truth": {
            "label": "not_spam",
            "urgency": "medium",
            "department": "billing",
            "reply_keywords": ["invoice", "resend", "email", "attached", "records", "vat"],
        },
    },
]


def get_task_emails(task_name: str) -> list:
    """Return the email subset used for each task."""
    if task_name == "spam-detection":
        # 5 spam + 5 real work emails (first 10)
        return EMAILS[:10]
    elif task_name == "email-router":
        # 10 real work emails only (routing makes no sense for spam)
        return EMAILS[5:15]
    elif task_name == "email-resolver":
        # Subset of work emails that need a substantive reply
        resolver_ids = {
            "work_001", "work_002", "work_004",
            "work_005", "work_007",
        }
        return [e for e in EMAILS if e["email_id"] in resolver_ids]
    else:
        raise ValueError(f"Unknown task: {task_name}")
