## AI Tree Trimming MVP

This repository contains a minimal example for an AI‑powered lead capture and auto‑response solution aimed at tree trimming businesses.  The goal of this MVP (minimum viable product) is to demonstrate how a service can collect leads, record them to a local file, and trigger an automated response via SMS.

### Features

* A simple landing page (`index.html`) that explains the service and includes a form for prospects to submit their details and optional tree photos.
* A Python Flask server (`app.py`) that:
  * Serves the landing page and handles form submissions.
  * Saves lead information to a CSV file (`leads.csv`).
  * Sends an automated text message to the lead using Twilio (credentials must be supplied via environment variables).

### Requirements

To run the application locally you will need:

* Python 3.8 or newer
* [pip](https://pip.pypa.io/en/stable/) for installing dependencies
* A Twilio account with a verified phone number (optional — you can skip SMS sending by omitting the environment variables)

Install dependencies with:

```
pip install -r requirements.txt
```

Create a `.env` file in the project root (or set these environment variables in your shell) with the following content:

```
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=the_twilio_number_used_to_send_messages
OWNER_PHONE_NUMBER=the_number_receiving_lead_notifications
```

If you do not provide these variables, the application will still save leads but will skip sending SMS messages.

### Running the Server

Start the Flask development server by executing the following command from the project root:

```
python app.py
```

Then open your browser to `http://localhost:5000` to see the landing page.  The server will display logs on the console when leads are submitted.

### Customising the Auto‑Response

The automated SMS message is defined in `app.py` in the `send_sms` function.  Edit the `message_body` variable there to customise the text that leads receive after submitting the form.  You might include a link to your online calendar so the customer can book an inspection or provide additional instructions.

### Disclaimer

This MVP is provided as a demonstration.  Before using it in production, you should add proper validation, error handling, and security (for example, protecting file uploads and sanitising input).  You should also abide by all applicable laws and regulations when sending automated messages to customers.
