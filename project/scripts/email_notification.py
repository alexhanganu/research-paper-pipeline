"""
Email notification system for sending alerts about new papers.
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict
from datetime import datetime

def send_email_smtp(to_email: str, subject: str, body_html: str, body_text: str = None):
    """
    Send email using SMTP (Gmail, Outlook, etc.)
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        body_html: HTML body content
        body_text: Plain text fallback
    """
    # Get SMTP configuration from environment
    smtp_server = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
    smtp_port = int(os.environ.get('SMTP_PORT', '587'))
    smtp_user = os.environ.get('SMTP_USER', '')
    smtp_password = os.environ.get('SMTP_PASSWORD', '')
    from_email = os.environ.get('FROM_EMAIL', smtp_user)
    
    if not smtp_user or not smtp_password:
        print("Error: SMTP credentials not configured.")
        print("Set SMTP_USER and SMTP_PASSWORD environment variables.")
        return False
    
    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = from_email
        msg['To'] = to_email
        
        # Attach plain text and HTML versions
        if body_text:
            part1 = MIMEText(body_text, 'plain')
            msg.attach(part1)
        
        part2 = MIMEText(body_html, 'html')
        msg.attach(part2)
        
        # Send email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
        
        print(f"✓ Email sent successfully to {to_email}")
        return True
        
    except Exception as e:
        print(f"✗ Failed to send email: {e}")
        return False

def send_email_aws_ses(to_email: str, subject: str, body_html: str, body_text: str = None):
    """
    Send email using AWS SES
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        body_html: HTML body content
        body_text: Plain text fallback
    """
    try:
        import boto3
        
        from_email = os.environ.get('FROM_EMAIL', 'noreply@example.com')
        region = os.environ.get('AWS_REGION', 'us-east-1')
        
        client = boto3.client('ses', region_name=region)
        
        response = client.send_email(
            Source=from_email,
            Destination={'ToAddresses': [to_email]},
            Message={
                'Subject': {'Data': subject},
                'Body': {
                    'Text': {'Data': body_text or 'Please view this email in HTML format.'},
                    'Html': {'Data': body_html}
                }
            }
        )
        
        print(f"✓ Email sent via AWS SES to {to_email}")
        return True
        
    except ImportError:
        print("boto3 not installed. Install with: pip install boto3")
        return False
    except Exception as e:
        print(f"✗ Failed to send email via AWS SES: {e}")
        return False

def send_email_azure(to_email: str, subject: str, body_html: str, body_text: str = None):
    """
    Send email using Azure Communication Services
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        body_html: HTML body content
        body_text: Plain text fallback
    """
    try:
        from azure.communication.email import EmailClient
        
        connection_string = os.environ.get('AZURE_COMMUNICATION_CONNECTION_STRING', '')
        from_email = os.environ.get('FROM_EMAIL', 'noreply@example.com')
        
        if not connection_string:
            print("Error: AZURE_COMMUNICATION_CONNECTION_STRING not set")
            return False
        
        client = EmailClient.from_connection_string(connection_string)
        
        message = {
            "senderAddress": from_email,
            "recipients": {
                "to": [{"address": to_email}]
            },
            "content": {
                "subject": subject,
                "plainText": body_text or 'Please view this email in HTML format.',
                "html": body_html
            }
        }
        
        poller = client.begin_send(message)
        result = poller.result()
        
        print(f"✓ Email sent via Azure to {to_email}")
        return True
        
    except ImportError:
        print("azure-communication-email not installed. Install with: pip install azure-communication-email")
        return False
    except Exception as e:
        print(f"✗ Failed to send email via Azure: {e}")
        return False

def create_new_papers_email(papers: List[Dict], query: str = "") -> tuple:
    """
    Create email content for new papers notification.
    
    Args:
        papers: List of paper dictionaries
        query: Search query used
        
    Returns:
        Tuple of (html_body, text_body)
    """
    # HTML version
    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .header {{ background-color: #4CAF50; color: white; padding: 20px; text-align: center; }}
            .paper {{ border: 1px solid #ddd; margin: 15px 0; padding: 15px; border-radius: 5px; }}
            .paper-title {{ font-size: 18px; font-weight: bold; color: #2c3e50; margin-bottom: 8px; }}
            .paper-meta {{ color: #7f8c8d; font-size: 14px; margin-bottom: 8px; }}
            .paper-abstract {{ margin-top: 10px; font-size: 14px; }}
            .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; color: #7f8c8d; font-size: 12px; }}
            a {{ color: #3498db; text-decoration: none; }}
            a:hover {{ text-decoration: underline; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>New Research Papers Found</h1>
            <p>Research Paper Processing Pipeline</p>
        </div>
        
        <div style="padding: 20px;">
            <p><strong>Summary:</strong> Found {len(papers)} new paper(s) matching your search criteria.</p>
            {f'<p><strong>Search Query:</strong> {query}</p>' if query else ''}
            <p><strong>Date:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            
            <hr style="margin: 30px 0;">
    """
    
    # Add each paper
    for i, paper in enumerate(papers, 1):
        authors_str = ', '.join(paper.get('authors', [])[:3])
        if len(paper.get('authors', [])) > 3:
            authors_str += f" et al. ({len(paper['authors'])} authors)"
        
        abstract = paper.get('abstract', 'No abstract available.')
        if len(abstract) > 300:
            abstract = abstract[:300] + '...'
        
        html += f"""
            <div class="paper">
                <div class="paper-title">{i}. {paper.get('title', 'Untitled')}</div>
                <div class="paper-meta">
                    <strong>Authors:</strong> {authors_str}<br>
                    <strong>Journal:</strong> {paper.get('journal', 'Unknown')}<br>
                    <strong>Year:</strong> {paper.get('year', 'Unknown')}<br>
                    <strong>PMID:</strong> <a href="{paper.get('url', '#')}">{paper.get('pmid', 'N/A')}</a>
                </div>
                <div class="paper-abstract">
                    <strong>Abstract:</strong> {abstract}
                </div>
            </div>
        """
    
    html += """
            <div class="footer">
                <p>This is an automated notification from the Research Paper Processing Pipeline.</p>
                <p>To process these papers, run the pipeline with your configured settings.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Plain text version
    text = f"""
New Research Papers Found
Research Paper Processing Pipeline
{'='*60}

Summary: Found {len(papers)} new paper(s) matching your search criteria.
{f'Search Query: {query}' if query else ''}
Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{'='*60}

"""
    
    for i, paper in enumerate(papers, 1):
        authors_str = ', '.join(paper.get('authors', [])[:3])
        if len(paper.get('authors', [])) > 3:
            authors_str += f" et al."
        
        text += f"""
{i}. {paper.get('title', 'Untitled')}

Authors: {authors_str}
Journal: {paper.get('journal', 'Unknown')}
Year: {paper.get('year', 'Unknown')}
PMID: {paper.get('pmid', 'N/A')}
URL: {paper.get('url', 'N/A')}

{paper.get('abstract', 'No abstract available.')[:300]}...

{'='*60}
"""
    
    text += """
This is an automated notification from the Research Paper Processing Pipeline.
To process these papers, run the pipeline with your configured settings.
"""
    
    return html, text

def notify_new_papers(papers: List[Dict], to_email: str, query: str = "", 
                     method: str = 'smtp'):
    """
    Send email notification about new papers.
    
    Args:
        papers: List of new papers
        to_email: Recipient email
        query: Search query used
        method: 'smtp', 'aws_ses', or 'azure'
    """
    if not papers:
        print("No new papers to notify about.")
        return False
    
    subject = f"New Research Papers Found ({len(papers)} papers)"
    html_body, text_body = create_new_papers_email(papers, query)
    
    if method == 'smtp':
        return send_email_smtp(to_email, subject, html_body, text_body)
    elif method == 'aws_ses':
        return send_email_aws_ses(to_email, subject, html_body, text_body)
    elif method == 'azure':
        return send_email_azure(to_email, subject, html_body, text_body)
    else:
        print(f"Unknown email method: {method}")
        return False

if __name__ == '__main__':
    # Test email generation
    test_papers = [
        {
            'title': 'BRCA1 mutations in breast cancer patients',
            'authors': ['Smith J', 'Doe J', 'Johnson M'],
            'journal': 'Nature Medicine',
            'year': '2024',
            'pmid': '12345678',
            'url': 'https://pubmed.ncbi.nlm.nih.gov/12345678/',
            'abstract': 'This study examines BRCA1 mutations...'
        }
    ]
    
    html, text = create_new_papers_email(test_papers, "cancer biomarkers")
    print("HTML Email Preview:")
    print(html[:500])