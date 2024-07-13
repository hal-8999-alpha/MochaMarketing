from __future__ import print_function
import os.path
import base64
import json
import sys
from email.message import EmailMessage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.send']


def create_email_template(data):
    data_type = data['type'] 
    email = data['email']
    password = data.setdefault('temp_password', {})

    # print(data_type)
    # print(email)
    # print(password)
    
    templates = {
        'Password': {
            'subject': 'Reset Your Password',
            'body': f'''
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
            </head>
            <body style="font-family: 'Roboto', sans-serif; background-color: #4a3910; color: white; margin: 0; padding: 0;">
                <div style="width: 80%; margin: auto; padding: 20px;">
                <div style="text-align: center; background-color: #000; max-width: 80%; margin: 0 auto;">
                        <img src="https://res.cloudinary.com/dlmcflarh/image/upload/v1683659398/Mocha%20Marketing/content/logo_yaiecf.png" alt="Logo" style="width: auto; max-width: 200px; height: auto;">
                    </div>
                    
            <h1 style="text-align: center; font-size: 24px; margin-bottom: 10px;">Reset Your Password</h1>
                    <p style="font-size: 18px; text-align: center; line-height: 1.5; margin-bottom: 20px;">You're receiving this email because someone is attempting to reset your password.</p>
                    <div style="text-align: center;">
                        <a href="https://app.mochamarketing.media/" style="display: inline-block; text-align: center; font-size: 18px; padding: 10px 20px; background-color: #f0e7d8; color: #4a3910; text-decoration: none; border-radius: 4px;">Login</a>
                    </div>
                    <p style="font-size: 18px; text-align: center; line-height: 1.5; margin-bottom: 20px;">
                        If you did not ask to reset your password please email us right away. <br><br>
                        As long as no one has access to your email account your Mocha Marketing account is safe.<br><br>
                        Please login using the following credentials to login and change your password:<br><br>
                        Email: {email}<br><br>
                        Temporary Password: {password}<br>
                    </p>
                    <div style="font-size: 16px; font-style: italic; color: #f0e7d8; text-align: center; margin-top: 20px;">
                        Best regards,<br>
                        Jayson Paglow <br>
                    Brewing Connection <br>
                        <a href="https://mochamarketing.media/">Mocha Marketing</a><br>
                    </div>
                </div>
            </body>
            </html>
            '''
        },
        'Meeting': {
            'subject': 'Your Profile is Being Built',
            'body': f'''
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
            </head>
            <body style="font-family: 'Roboto', sans-serif; background-color: #4a3910; color: white; margin: 0; padding: 0;">
                <div style="width: 80%; margin: auto; padding: 20px;">
                <div style="text-align: center; background-color: #000; max-width: 80%; margin: 0 auto;">
                        <img src="https://res.cloudinary.com/dlmcflarh/image/upload/v1683659398/Mocha%20Marketing/content/logo_yaiecf.png" alt="Logo" style="width: auto; max-width: 200px; height: auto;">
                    </div>
                    
            <h1 style="text-align: center; font-size: 24px; margin-bottom: 10px;">Brewing Your Account</h1>
                    <p style="font-size: 18px; text-align: center; line-height: 1.5; margin-bottom: 20px;">Thank you for signing up for Mocha Marketing. We're building your long term profile and plan right now!</p>
                    <div style="text-align: center;">
                        <a href="https://app.mochamarketing.media/" style="display: inline-block; text-align: center; font-size: 18px; padding: 10px 20px; background-color: #f0e7d8; color: #4a3910; text-decoration: none; border-radius: 4px;">Login</a>
                    </div>
                    <p style="font-size: 18px; text-align: center; line-height: 1.5; margin-bottom: 20px;">
                        Click the button above to goto your account. You must sign in and change your password within 48 hours.<br> 
                        Email: {email}<br><br>
                        Temporary Password: {password}<br>
                    </p>
                    <div style="font-size: 16px; font-style: italic; color: #f0e7d8; text-align: center; margin-top: 20px;">
                        Best regards,<br>
                        Jayson Paglow <br>
                    Brewing Connection <br>
                        <a href="https://mochamarketing.media/">Mocha Marketing</a><br>
                    </div>
                </div>
            </body>
            </html>
            '''
        },
        'Quarter': {
            'subject': 'You Have a New Plan',
            'body': f'''
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
            </head>
            <body style="font-family: 'Roboto', sans-serif; background-color: #4a3910; color: white; margin: 0; padding: 0;">
                <div style="width: 80%; margin: auto; padding: 20px;">
                <div style="text-align: center; background-color: #000; max-width: 80%; margin: 0 auto;">
                        <img src="https://res.cloudinary.com/dlmcflarh/image/upload/v1683659398/Mocha%20Marketing/content/logo_yaiecf.png" alt="Logo" style="width: auto; max-width: 200px; height: auto;">
                    </div>
                    
            <h1 style="text-align: center; font-size: 24px; margin-bottom: 10px;">Long Term Plan</h1>
                    <p style="font-size: 18px; text-align: center; line-height: 1.5; margin-bottom: 20px;">We finished building your unique profile, direction for the year and direction for the next three months</p>
                    <div style="text-align: center;">
                        <a href="https://app.mochamarketing.media/" style="display: inline-block; text-align: center; font-size: 18px; padding: 10px 20px; background-color: #f0e7d8; color: #4a3910; text-decoration: none; border-radius: 4px;">Login</a>
                    </div>
                    <p style="font-size: 18px; text-align: center; line-height: 1.5; margin-bottom: 20px;">
                        To edit your plan <br>
                        1) Login to Mocha Marketing <br>
                        2) Click the Yearly and Quarterly Tabs <br>
                        3) Make your edits by clicking on the text and changing it. <br>
                        <br> 
                        If you have any questions feel free to reach out to this email directly.
                    </p>
                    <div style="font-size: 16px; font-style: italic; color: #f0e7d8; text-align: center; margin-top: 20px;">
                        Best regards,<br>
                        Jayson Paglow <br>
                    Brewing Connection <br>
                        <a href="https://mochamarketing.media/">Mocha Marketing</a><br>
                    </div>
                </div>
            </body>
            </html>
            '''
        },
        'Month': {
            'subject': 'Your Content is Ready',
            'body': f'''
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
            </head>
            <body style="font-family: 'Roboto', sans-serif; background-color: #4a3910; color: white; margin: 0; padding: 0;">
                <div style="width: 80%; margin: auto; padding: 20px;">
                <div style="text-align: center; background-color: #000; max-width: 80%; margin: 0 auto;">
                        <img src="https://res.cloudinary.com/dlmcflarh/image/upload/v1683659398/Mocha%20Marketing/content/logo_yaiecf.png" alt="Logo" style="width: auto; max-width: 200px; height: auto;">
                    </div>
                    
            <h1 style="text-align: center; font-size: 24px; margin-bottom: 10px;">30 Days of Content</h1>
                    <p style="font-size: 18px; text-align: center; line-height: 1.5; margin-bottom: 20px;">Your next 30 days of content is ready for review.</p>
                    <div style="text-align: center;">
                        <a href="https://app.mochamarketing.media/" style="display: inline-block; text-align: center; font-size: 18px; padding: 10px 20px; background-color: #f0e7d8; color: #4a3910; text-decoration: none; border-radius: 4px;">Login</a>
                    </div>
                    <p style="font-size: 18px; text-align: center; line-height: 1.5; margin-bottom: 20px;">
                        If a post is visible in your Day Calendar tab, then it can be edited. To edit your content: <br><br>
                        1) Login to Mocha Marketing <br>
                        2) Click the Daily Calendar Tab <br>
                        3) Make your edits by clicking on the text and changing it. <br>
                        <br> 
                        If you have any questions feel free to reach out to this email directly.
                    </p>
                    <div style="font-size: 16px; font-style: italic; color: #f0e7d8; text-align: center; margin-top: 20px;">
                        Best regards,<br>
                        Jayson Paglow <br>
                    Brewing Connection <br>
                        <a href="https://mochamarketing.media/">Mocha Marketing</a><br>
                    </div>
                </div>
            </body>
            </html>
            '''
        },
        'MonthAutomated': {
            'subject': 'You Have a New 30 Day Plan',
            'body': f'''
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
            </head>
            <body style="font-family: 'Roboto', sans-serif; background-color: #4a3910; color: white; margin: 0; padding: 0;">
                <div style="width: 80%; margin: auto; padding: 20px;">
                <div style="text-align: center; background-color: #000; max-width: 80%; margin: 0 auto;">
                        <img src="https://res.cloudinary.com/dlmcflarh/image/upload/v1683659398/Mocha%20Marketing/content/logo_yaiecf.png" alt="Logo" style="width: auto; max-width: 200px; height: auto;">
                    </div>
                    
            <h1 style="text-align: center; font-size: 24px; margin-bottom: 10px;">30 Days of Content</h1>
                    <p style="font-size: 18px; text-align: center; line-height: 1.5; margin-bottom: 20px;">We've finished building your content calendar for the next 30 days.</p>
                    <div style="text-align: center;">
                        <a href="https://app.mochamarketing.media/" style="display: inline-block; text-align: center; font-size: 18px; padding: 10px 20px; background-color: #f0e7d8; color: #4a3910; text-decoration: none; border-radius: 4px;">Login</a>
                    </div>
                    <p style="font-size: 18px; text-align: center; line-height: 1.5; margin-bottom: 20px;">
                        To edit your 30 Day Calendar: <br><br>
                        1) Login to Mocha Marketing <br>
                        2) Click the 30 Day Calendar Tab <br>
                        3) Make your edits by clicking on the text and changing it. <br>
                        <br> 
                        If you have any questions feel free to reach out to this email directly.
                    </p>
                    <div style="font-size: 16px; font-style: italic; color: #f0e7d8; text-align: center; margin-top: 20px;">
                        Best regards,<br>
                        Jayson Paglow <br>
                    Brewing Connection <br>
                        <a href="https://mochamarketing.media/">Mocha Marketing</a><br>
                    </div>
                </div>
            </body>
            </html>
            '''
        },
        'Day': {
            'subject': 'Your Content Is Ready',
            'body': f'''
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
            </head>
            <body style="font-family: 'Roboto', sans-serif; background-color: #4a3910; color: white; margin: 0; padding: 0;">
                <div style="width: 80%; margin: auto; padding: 20px;">
                <div style="text-align: center; background-color: #000; max-width: 80%; margin: 0 auto;">
                        <img src="https://res.cloudinary.com/dlmcflarh/image/upload/v1683659398/Mocha%20Marketing/content/logo_yaiecf.png" alt="Logo" style="width: auto; max-width: 200px; height: auto;">
                    </div>
                    
            <h1 style="text-align: center; font-size: 24px; margin-bottom: 10px;">30 Days of Content</h1>
                    <p style="font-size: 18px; text-align: center; line-height: 1.5; margin-bottom: 20px;">We've completed the next 30 days of content for you and it will start being posted 7 days from now. Once a post is scheduled it cannot be edited, only deleted.</p>
                    <div style="text-align: center;">
                        <a href="https://app.mochamarketing.media/" style="display: inline-block; text-align: center; font-size: 18px; padding: 10px 20px; background-color: #f0e7d8; color: #4a3910; text-decoration: none; border-radius: 4px;">Login</a>
                    </div>
                    <p style="font-size: 18px; text-align: center; line-height: 1.5; margin-bottom: 20px;">
                        If a post is visible in your Day Calendar tab, then it can be edited. To edit your content: <br><br>
                        1) Login to Mocha Marketing <br>
                        2) Click the Daily Calendar Tab <br>
                        3) Make your edits by clicking on the text and changing it. <br>
                        <br> 
                        Any edits you make will be automatically applied. If you have any questions feel free to reach out to this email directly.
                    </p>
                    <div style="font-size: 16px; font-style: italic; color: #f0e7d8; text-align: center; margin-top: 20px;">
                        Best regards,<br>
                        Jayson Paglow <br>
                    Brewing Connection <br>
                        <a href="https://mochamarketing.media/">Mocha Marketing</a><br>
                    </div>
                </div>
            </body>
            </html>
            '''
        }
        
    }
    return templates.get(data_type, "Invalid template type")


def main(data, credentials):
    """Sends an email message using the Gmail API."""
    print("Email")
    try:
        # Call the Gmail API
        service = build('gmail', 'v1', credentials=credentials)
        message = MIMEMultipart()

        # Get the HTML email content based on the data type
        template = create_email_template(data)
        html_content = template['body']

        # Attach the HTML content to the email
        message.attach(MIMEText(html_content, "html"))

        message['To'] = data['email']
        message['From'] = 'Notifications <hello@mochamarketing.media>'
        message['Subject'] = template['subject']

        # Encoded message
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

        create_message = {
            'raw': encoded_message
        }
        send_message = (service.users().messages().send(userId="me", body=create_message).execute())
        print("Sent")
        # print(F'Message Id: {send_message["id"]}')
    except HttpError as error:
        print(F'An error occurred: {error}')
        send_message = None
    print("Sent")
    return send_message


if __name__ == '__main__':
    if len(sys.argv) > 2:
        data = json.loads(sys.argv[1])
        credentials_json = sys.argv[2]
        credentials = Credentials.from_authorized_user_info(json.loads(credentials_json))
        main(data, credentials)
    else:
        print("Error: No data argument or credentials provided")