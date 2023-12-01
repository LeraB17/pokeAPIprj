import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from settings import *


def send_email(to_email, content, subject='result'):
    subjects = {
        'result': 'Pokemon Fights: Results',
        'code_second': 'Pokemon Fights: Confirm',
        'code': 'Pokemon Fights: Change password',
    }
    
    if subject not in subjects.keys():
        raise ValueError(f"subject {subject} is not allowed")
    
    if subject == 'result':
        html = f"""\
                    <html>
                    <head></head>
                    <body>
                        <h3>Results of your fast fight:</h3>
                        <div>You: {content["select_pokemon_name"]}</div>
                        <div>Your hp: {content["select_pokemon_hp"]}</div>
                        <div>Your attack: {content["select_pokemon_attack"]}</div>
                        <br/>
                        <div>Vs: {content["vs_pokemon_name"]}</div>
                        <div>Vs hp: {content["vs_pokemon_hp"]}</div>
                        <div>Vs attack: {content["vs_pokemon_attack"]}</div>
                        <h4>Rounds:</h4>
                        {content['rounds']}
                        <br/>
                        <div>Winner: {content['winner_name']}</div>
                    </body>
                    </html>
                    """
    elif subject == 'code_second':
        html = f"""\
                    <html>
                    <head></head>
                    <body>
                        <h3>Confirm login with code:</h3>
                        <h1>{content}</h1>
                    </body>
                    </html>
                    """
    elif subject == 'code':
        html = f"""\
                    <html>
                    <head></head>
                    <body>
                        <h3>Code for chanhe password:</h3>
                        <h1>{content}</h1>
                    </body>
                    </html>
                    """
    else: 
        html = f"""\
                    <html>
                    <head></head>
                    <body>
                        <h3>Hi from Pokemon Fights!</h3>
                    </body>
                    </html>
                    """

    email = MAIL_EMAIL
    password = MAIL_PASSWORD
    
    part = MIMEText(html, 'html')

    message = MIMEMultipart('alternative')
    message['Subject'] = subjects[subject]
    message['From'] = email
    message['To'] = to_email
    message.attach(part)

    try:
        server = smtplib.SMTP(MAIL_SERVER, MAIL_PORT)
        server.starttls()
        server.login(email, password)
        server.sendmail(email, to_email, message.as_string())
        server.quit()
        print('email sent')
        return 0
    except Exception as e:
        print('error about email:', e)
        return e
