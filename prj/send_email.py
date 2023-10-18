import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from db import email_params


def send_email(to_email, title='Pokemon Fight', results='Fight results'):
    email = email_params['email']
    password = email_params['password']

    text = f"Results of your fast fight:\n {results}"
    html = f"""\
            <html>
            <head></head>
            <body>
                <h3>Results of your fast fight:</h3>
                {results}
            </body>
            </html>
            """
    part1 = MIMEText(text, "plain")
    part2 = MIMEText(html, 'html')

    message = MIMEMultipart('alternative')
    message['Subject'] = title
    message['From'] = email
    message['To'] = to_email
    message.attach(part1)
    message.attach(part2)

    try:
        server = smtplib.SMTP(email_params['mail_server'], email_params['port'])
        server.starttls()
        server.login(email, password)
        server.sendmail(email, to_email, message.as_string())
        server.quit()
        print('email sent')
        return 0
    except Exception as e:
        print('error about email:', e)
        return e
