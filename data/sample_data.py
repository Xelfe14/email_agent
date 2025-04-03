import os
import pandas as pd
from typing import Dict, List, Any

def get_sample_emails() -> pd.DataFrame:
    """
    Return sample email-response pairs for training the RAG system.

    Returns:
        DataFrame with columns 'email_text', 'response_text', and metadata columns
    """
    samples = [
        {
            "email_text": """
            Subject: Seed Funding for AI-Driven Fintech Startup - BudgetIQ

            Dear Investment Team,

            My name is Sarah Chen, co-founder and CEO of BudgetIQ. We're an AI-driven personal finance platform that helps millennials automate their savings and investments based on spending patterns and financial goals.

            We've built a working MVP with 5,000 active users and are seeing a 15% month-over-month growth rate. Our user retention after 3 months is 78%, significantly above industry average.

            We're raising a $1.5M seed round to scale our engineering team and marketing efforts. I'd love to discuss how we might work together and share our detailed pitch deck and financial projections.

            Our founding team comes from Robinhood, Betterment, and Google, and we're based in San Francisco.

            Would you be available for a 30-minute call next week to discuss further?

            Best regards,
            Sarah Chen
            CEO, BudgetIQ
            sarah@budgetiq.io | www.budgetiq.io
            """,

            "response_text": """
            Subject: Re: Seed Funding for AI-Driven Fintech Startup - BudgetIQ

            Dear Sarah,

            Thank you for reaching out about BudgetIQ. Your platform's focus on helping millennials automate savings and investments sounds interesting, and your early traction metrics are promising.

            I'd be happy to learn more about your company. Could you please send over your pitch deck and financial projections to review before our call? This would help make our discussion more productive.

            I'm available for a call next Tuesday at 2 PM PT or Wednesday at 10 AM PT. Please let me know if either of these times works for you.

            Looking forward to hearing more about your team's background at Robinhood, Betterment, and Google, and how you're leveraging that experience at BudgetIQ.

            Best regards,


            """,

            "industry": "Fintech",
            "funding_stage": "Seed",
            "company_type": "B2C"
        },

        {
            "email_text": """
            Subject: Series A Opportunity - SupplyChainAI

            Hello,

            I'm David Rodriguez, founder and CEO of SupplyChainAI. We provide AI-powered supply chain optimization software for manufacturing companies that reduces inventory costs by 23% on average while improving delivery times by 27%.

            We've been generating revenue for the past 18 months with $1.2M ARR and 140% YoY growth. Our customers include three Fortune 500 manufacturers and several mid-market companies across automotive, electronics, and industrial equipment sectors.

            We're raising a $7M Series A to expand our sales team and develop additional predictive features. Our pre-money valuation is $28M based on our traction and technology moat (we have two granted patents on our core algorithms).

            Would your fund be interested in exploring this opportunity? I can share our deck and financial model, and would be happy to set up a call to dive deeper.

            Regards,
            David Rodriguez
            Founder & CEO, SupplyChainAI
            david@supplychainai.com
            """,

            "response_text": """
            Subject: Re: Series A Opportunity - SupplyChainAI

            Hi David,

            Thanks for reaching out about SupplyChainAI. Your solution addresses a critical pain point in manufacturing, and your metrics around inventory cost reduction and delivery time improvements are impressive.

            I've been following developments in the supply chain optimization space, particularly given the disruptions of the past few years, so your timing is good.

            Yes, we'd be interested in learning more about your opportunity. Please send over your deck, financial model, and any case studies you might have from your Fortune 500 clients (anonymized as needed).

            Could you also share more details on:

            1. Your customer acquisition strategy and CAC/LTV metrics
            2. The team's background and experience in both AI and supply chain
            3. Your roadmap for utilizing the Series A funds

            I have time this Thursday at 1 PM ET or Friday at 11 AM ET for an initial call.

            Looking forward to connecting,


            """,

            "industry": "Supply Chain/Manufacturing",
            "funding_stage": "Series A",
            "company_type": "B2B"
        },

        {
            "email_text": """
            Subject: CleanEnergy Storage - Pre-seed funding opportunity

            Hi there,

            I'm Alex Patel, CEO of CleanEnergy Storage. We're developing a revolutionary grid-scale energy storage technology using recycled materials that costs 40% less than lithium-ion batteries while providing similar energy density.

            Our founding team includes Dr. Maria Lopez (former Tesla battery researcher) and James Kim (engineering lead from Sunrun). We're currently pre-revenue but have a working prototype and have completed initial safety certifications.

            We're raising $750K in pre-seed funding to build our pilot installation and pursue strategic partnerships with two utilities that have expressed strong interest.

            Would your fund consider pre-seed opportunities in clean tech hardware? I'd appreciate the chance to share our vision and technical approach.

            Thanks for your consideration,

            Alex Patel
            CleanEnergy Storage
            alex@cleanenergystorage.tech
            """,

            "response_text": """
            Subject: Re: CleanEnergy Storage - Pre-seed funding opportunity

            Hello Alex,

            Thank you for reaching out about CleanEnergy Storage. Your approach to grid-scale energy storage using recycled materials sounds innovative, particularly with the cost advantages you've mentioned compared to traditional lithium-ion solutions.

            While we primarily focus on post-revenue companies, we do make exceptions for breakthrough technologies in the clean energy space, especially with strong technical founding teams like yours. Dr. Lopez's background at Tesla and James Kim's experience at Sunrun are certainly impressive credentials.

            I'd like to learn more about:

            - The specific technology and how it achieves the cost reduction
            - Your IP position and defensibility
            - The timeline to commercial deployment
            - Details about the utility companies that have expressed interest

            Please share your pitch materials, and we can schedule a call for next week. I have availability on Monday afternoon or Wednesday morning.

            Regards,


            """,

            "industry": "CleanTech",
            "funding_stage": "Pre-seed",
            "company_type": "B2B"
        },

        {
            "email_text": """
            Subject: Cybersecurity SaaS - $3M Seed Round

            Dear Investment Team,

            I'm reaching out regarding ShieldGuard, our zero-trust cybersecurity platform for mid-market businesses. We provide enterprise-grade protection at SMB-friendly prices, with a particular focus on protecting remote workforces.

            Since launching 8 months ago, we've reached $45K in MRR with a 9% MoM growth rate and a 2.3% churn rate. Our customers span financial services, healthcare, and professional services sectors - all industries with sensitive data protection needs.

            My background is 12 years at Microsoft's security division, and my co-founder was previously CISO at a regional bank. We're raising $3M to accelerate product development and expand our sales team.

            We've already secured $1.2M from angel investors and a small seed fund. Would you be interested in discussing the opportunity to participate in our round?

            Best,

            Thomas Williams
            CEO, ShieldGuard Security
            thomas@shieldguardsecurity.com
            """,

            "response_text": """
            Subject: Re: Cybersecurity SaaS - $3M Seed Round

            Hi Thomas,

            Thanks for introducing us to ShieldGuard. Your focus on bringing enterprise-grade cybersecurity to mid-market companies addresses a clear gap in the market, especially with the acceleration of remote work.

            The traction you've shown in 8 months is promising - $45K MRR with healthy growth and relatively low churn indicates product-market fit in a competitive space. Your combined background with your co-founder also brings the right mix of technical and industry-specific security expertise.

            We'd definitely like to explore this opportunity further. A few questions before we meet:

            1. What's your current pricing model and target ACV?
            2. How does ShieldGuard differentiate from other solutions targeting similar markets?
            3. What are your key growth channels so far?
            4. What's the planned allocation of the $3M you're raising?

            I can make time for a call tomorrow at 3 PM ET or Thursday at 11 AM ET. Let me know what works for you, and please send your pitch deck in advance.

            Looking forward to connecting,


            """,

            "industry": "Cybersecurity",
            "funding_stage": "Seed",
            "company_type": "B2B"
        }
    ]

    # Convert to DataFrame
    df = pd.DataFrame(samples)

    return df

def save_sample_data(output_path: str) -> None:
    """
    Save sample data to CSV file.

    Args:
        output_path: Path to save the CSV file
    """
    df = get_sample_emails()

    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Save to CSV
    df.to_csv(output_path, index=False)

    print(f"Sample data saved to {output_path}")

if __name__ == "__main__":
    # When run directly, save sample data
    save_sample_data("email_agent/data/sample_emails.csv")
