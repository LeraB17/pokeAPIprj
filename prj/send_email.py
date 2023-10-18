import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from db import email_params


def send_email(to_email, result, title='Pokemon Fight'):
    email = email_params['email']
    password = email_params['password']

    text = f"""Results of your fast fight:\n\n
            You: {result["select_pokemon_name"]}\n
            Your hp: {result["select_pokemon_hp"]}\n
            Your attack: {result["select_pokemon_attack"]}\n\n
            Vs: {result["vs_pokemon_name"]}\n
            Vs hp: {result["vs_pokemon_hp"]}\n
            Vs attack: {result["vs_pokemon_attack"]}\n\n
            Rounds: \n
            {result['rounds']}
            Winner: {result['winner_name']}"""
    html = f"""\
            <html>
            <head></head>
            <body>
                <h3>Results of your fast fight:</h3>
                <div>You: {result["select_pokemon_name"]}</div>
                <div>Your hp: {result["select_pokemon_hp"]}</div>
                <div>Your attack: {result["select_pokemon_attack"]}</div>
                <br/>
                <div>Vs: {result["vs_pokemon_name"]}</div>
                <div>Vs hp: {result["vs_pokemon_hp"]}</div>
                <div>Vs attack: {result["vs_pokemon_attack"]}</div>
                <h4>Rounds:</h4>
                {result['rounds']}
                <br/>
                <div>Winner: {result['winner_name']}</div>
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
