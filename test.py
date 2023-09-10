import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
import mysql.connector
import requests
from itertools import zip_longest

url = 'https://etender.gov.az/api/events?EventType=2&PageSize=6&PageNumber=1&EventStatus=1&Keyword=&buyerOrganizationName=&PrivateRfxId=&startDateFrom=&startDateTo=&AwardedparticipantName=&AwardedparticipantVoen=&DocumentViewType='

r = requests.get(url)

json_file = r.json()

company_names = []
start_dates = []
end_dates = []
unique_ids = []
usl_codes = []
opening_dates = []


for item in json_file['items']:
    company_name = item['buyerOrganizationName']
    start_date = item['startDate']
    end_date = item['endDate']
    unique_id = item['eventId']

    company_names.append(str(company_name))
    start_dates.append(str(start_date))
    end_dates.append(str(end_date))
    unique_ids.append(str(unique_id))


for i in unique_ids:
    urls = f'https://etender.gov.az/api/events/{i}'
    resp = requests.get(urls)
    json_resp = resp.json()
    usl_codes.append(str(json_resp.get('cpvCode')))


zipped = zip_longest(company_names, start_dates, end_dates, unique_ids, usl_codes, fillvalue = None)

zipped_lists = list(zipped)

def send_email(subject, message):
    sender_email = "senderEmail@example.com"
    recipient_email = "receiverEmail@example.com"
    password = "sendersEmailPassword"

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = subject

    msg.attach(MIMEText(message, 'plain'))
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587) 
        server.starttls()
        server.login(sender_email, password)
        server.sendmail(sender_email, recipient_email, msg.as_string())
        server.quit()
        print("Email sent successfully")
    except Exception as e:
        print("Error sending email:", e)


db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'yourPassword',
    'database': 'yourDbName',
    'autocommit': False
}

connect = mysql.connector.connect(**db_config)

try:
    my_cursor = connect.cursor()
    

    if connect.is_connected():
    
        print("Connection successfully created!")
        for company_name, start_date, end_date, unique_id, usl_code in zipped_lists:

            check_sql = 'SELECT COUNT(*) FROM tenders WHERE event_id = %s'
            my_cursor.execute(check_sql, (unique_id,))
            exists = my_cursor.fetchone()[0]

            current_datetime = datetime.datetime.now()

            if not exists:
                sql = 'INSERT INTO tenders (company_name, start_date, end_date, event_id, usl_code, date_created) VALUES (%s, %s, %s, %s, %s, %s);'
                val = (company_name, start_date, end_date, unique_id, usl_code, current_datetime)
                my_cursor.execute(sql, val)
                connect.commit()
                subject = "New Tender Inserted"
                message = f"New tender inserted: {company_name}, {usl_code}"
                send_email(subject, message)

            else:
                print(f"Event_id {unique_id} already exists, skipping...")
        



    print("Commited successfully")


except Exception as e:
    print("Error:", e)
    connect.rollback()

finally:
    my_cursor.close()
    connect.close()
