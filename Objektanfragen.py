import random
import smtplib
import os
import webbrowser
from threading import Timer
from faker import Faker
from lxml import etree
from email.message import EmailMessage
from flask import Flask, request, render_template_string

# =============== CONFIG ================
SMTP_SERVER = 'w01f25a5.kasserver.com'
SMTP_PORT = 587
SMTP_USER = 'info@emprochen.de'
SMTP_PASSWORD = 'estateSQLpw2010'

# ============ HELPERS =================
fake = Faker("de_DE")
app = Flask(__name__)

def replace_umlauts(s):
    umlaut_map = {
        'ä': 'ae',
        'ö': 'oe',
        'ü': 'ue',
        'ß': 'ss',
        'Ä': 'Ae',
        'Ö': 'Oe',
        'Ü': 'Ue'
    }
    for umlaut, replacement in umlaut_map.items():
        s = s.replace(umlaut, replacement)
    return s


def generate_interessent():
    first = fake.first_name()
    last = fake.last_name()

    # Umlaute ersetzen
    first_ascii = replace_umlauts(first.lower())
    last_ascii = replace_umlauts(last.lower())

    email = f"{first_ascii}.{last_ascii}@empro.invalid"
    phone = fake.phone_number()
    street = fake.street_name() + " " + str(random.randint(0,30))
    city = fake.city()
    zip = fake.postcode()
    return {
        "vorname": first,
        "nachname": last,
        "email": email,
        "tel": phone,
        "street": street,
        "city": city,
        "zip": zip
    }

def create_openimmo_xml(objektnr, interessent):
    NSMAP = {None: "http://www.openimmo.de"}
    root = etree.Element("openimmo_feedback", nsmap=NSMAP)

    anfrage = etree.SubElement(root, "objekt")

    oobjd = etree.SubElement(anfrage, "oobj_id")
    oobjd.text = objektnr

    anfragedaten = etree.SubElement(anfrage, "interessent")

    etree.SubElement(anfragedaten, "vorname").text = interessent["vorname"]
    etree.SubElement(anfragedaten, "nachname").text = interessent["nachname"]
    etree.SubElement(anfragedaten, "email").text = interessent["email"]
    etree.SubElement(anfragedaten, "strasse").text = interessent["street"]
    etree.SubElement(anfragedaten, "plz").text = interessent["zip"]
    etree.SubElement(anfragedaten, "ort").text = interessent["city"]
    etree.SubElement(anfragedaten, "tel").text = interessent["tel"]
    etree.SubElement(anfragedaten, "anfrage").text = "Ich möchte gerne besichtigen"
    return etree.tostring(root, pretty_print=True, xml_declaration=True, encoding='iso-8859-1')

def send_email(receiver_email, subject, xml_data):
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = SMTP_USER
    msg['To'] = receiver_email
    msg['Bcc'] = 'frank.mueller@empro.de'
    msg.set_content("Bitte entnehmen Sie die Objektanfrage dem Anhang.")

    msg.add_attachment(xml_data, maintype='application', subtype='xml', filename='anfrage.xml')

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)

# ============ FLASK WEB UI ============
HTML_FORM = """
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <title>OpenImmo Anfragen Tool</title>
</head>
<body>
    <h2>OpenImmo Anfragen senden</h2>
    <form method="POST">
        <label>Empfänger-E-Mail:</label><br>
        <input type="email" name="receiver" required><br><br>

        <label>Objektnummer:</label><br>
        <input type="text" name="objektnr" required><br><br>

        <label>Anzahl der Anfragen:</label><br>
        <input type="number" name="anzahl" min="1" required><br><br>

        <button type="submit">Anfragen senden</button>
    </form>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        receiver = request.form['receiver']
        objektnr = request.form['objektnr']
        anzahl = int(request.form['anzahl'])
        
        for i in range(anzahl):
            interessent = generate_interessent()
            xml_data = create_openimmo_xml(objektnr, interessent)
            send_email(receiver, f"Objektanfrage von immowelt.de zu {objektnr}", xml_data)

        return f"{anzahl} Anfragen wurden erfolgreich an {receiver} gesendet."
    
    return render_template_string(HTML_FORM)

if __name__ == '__main__':
    port = 5050
    Timer(1.0, lambda: webbrowser.open(f'http://127.0.0.1:{port}')).start()
    app.run(debug=False, port=port)
