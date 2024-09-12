import streamlit as st
import pandas as pd
import os
import uuid
import sendgrid
import base64
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content, Attachment, FileContent, FileName, FileType, Disposition

st.set_page_config(page_title="WCPM TRACK INFO", layout="wide")

# Custom CSS for styling
st.markdown("""
<style>
    .track-title { font-size: 24px; font-weight: bold; margin-bottom: 10px; }
    .inline-input { display: inline-block; width: auto; }
    .track-container { margin-bottom: 40px; }
    .center-button {
        display: flex;
        justify-content: center;
        margin-top: 20px;
    }
</style>
""", unsafe_allow_html=True)

if 'tracks' not in st.session_state:
    st.session_state.tracks = [{
        'id': str(uuid.uuid4()),
        'title': 'TRACK TITLE 1',
        'bpm': '',
        'key': '',
        'meter': '',
        'instrumentation': ''
    }]

def add_track():
    new_track_number = len(st.session_state.tracks) + 1
    st.session_state.tracks.append({
        'id': str(uuid.uuid4()),
        'title': f'TRACK TITLE {new_track_number}',
        'bpm': '',
        'key': '',
        'meter': '',
        'instrumentation': ''
    })


def delete_track(track_id):
    st.session_state.tracks = [track for track in st.session_state.tracks if track['id'] != track_id]
    if len(st.session_state.tracks) == 0:
        st.session_state.tracks.append({
            'id': str(uuid.uuid4()),
            'title': 'TRACK TITLE 1',
            'bpm': '',
            'key': '',
            'meter': '',
            'instrumentation': ''
        })


def generate_excel_file():
    df = pd.DataFrame(st.session_state.tracks)
    file_path = f"/tmp/tracks_{uuid.uuid4()}.xlsx"

    # Save DataFrame to an Excel file using pandas
    df.to_excel(file_path, index=False, engine='openpyxl')

    return file_path
def all_track_info_provided():
    """Check if all required fields are filled in for all tracks."""
    for track in st.session_state.tracks:
        if not all([track['bpm'], track['key'], track['meter'], track['instrumentation']]):
            return False
    return True
    
def send_email_with_excel(recipient_email, file_path):
    try:
        # Try to get the API key from secrets
        sendgrid_secrets = st.secrets.get("sendgrid", {})
        api_key = sendgrid_secrets.get("sendgrid_api_key")  # Changed from "api_key" to "sendgrid_api_key"
        
        if not api_key:
            st.error("SendGrid API key not found in secrets. Please check your configuration.")
            st.write("Available sendgrid secrets:", list(sendgrid_secrets.keys()))  # Debug information
            return False
        
        # Mask the API key for logging (show only first 5 characters)
        masked_api_key = api_key[:5] + "*" * (len(api_key) - 5)
        st.write(f"Using API Key: {masked_api_key}")
        
        sg = sendgrid.SendGridAPIClient(api_key=api_key)

        # Define the email details
        from_email = Email('sendtowcpm@gmail.com')  # Use the email you verified with SendGrid
        to_email = To('nicolas.techer@warnerchappellpm.com')
        subject = 'WCPM Track Information'
        content = Content('text/plain', 'Please find the attached Excel file with track information.')

        # Create the mail object
        mail = Mail(from_email, to_email, subject, content)

        # Read and encode the file
        with open(file_path, "rb") as attachment_file:
            file_data = attachment_file.read()
            encoded_file = base64.b64encode(file_data).decode()

        # Create the attachment
        attachment = Attachment(
            FileContent(encoded_file),
            FileName(os.path.basename(file_path)),
            FileType('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
            Disposition('attachment')
        )

        # Add the attachment to the mail
        mail.add_attachment(attachment)

        # Send the email
        response = sg.send(mail)
        st.write(f"Email sent with status code: {response.status_code}")
        return True

    except Exception as e:
        st.error(f"Error sending email: {str(e)}")
        if isinstance(e, sendgrid.SendGridException):
            st.error(f"SendGrid error details: {e.body}")
        elif isinstance(e, requests.exceptions.RequestException):
            st.error(f"Request error details: {e.response.text if e.response else 'No response'}")
        return False

# Add this near the top of your app, after the imports
st.write("Available secrets:", list(st.secrets.keys()))
if "sendgrid" in st.secrets:
    st.write("SendGrid secret keys:", list(st.secrets.sendgrid.keys()))
    if "sendgrid_api_key" in st.secrets.sendgrid:
        st.write("SendGrid API key is properly configured.")
    else:
        st.error("SendGrid API key is missing from the secrets.")
else:
    st.error("SendGrid secrets not found. Please check your Streamlit secrets configuration.")

# Print the current working directory and list its contents
st.write("Current working directory:", os.getcwd())
st.write("Contents of current directory:", os.listdir())


# Main app layout
st.markdown("<h1 style='text-align: center;'>WCPM TRACK INFO</h1>", unsafe_allow_html=True)

# Create three columns with width ratio 1:4:1
left_col, center_col, right_col = st.columns([1, 4, 1])

with center_col:
    for track_index, track in enumerate(st.session_state.tracks):
        with st.container():
            st.markdown("<div class='track-container'>", unsafe_allow_html=True)

            # Add track title with trash button on the same row
            col1, col2 = st.columns([0.4, 11.5])
            with col1:
                st.button("🗑", key=f"delete_track_{track['id']}", on_click=delete_track, args=(track['id'],))
            with col2:
                new_track_title = st.text_input(
                    "",
                    value=track['title'],
                    key=f"track_title_{track['id']}",
                    label_visibility="collapsed"
                )
                if new_track_title != track['title']:
                    st.session_state.tracks[track_index]['title'] = new_track_title

            # BPM, Key, Meter, Instrumentation text fields on the same row
            cols = st.columns([0.5, 0.6, 0.6, 6])

            with cols[0]:
                new_bpm = st.text_input(
                    "",
                    value=track['bpm'],
                    key=f"bpm_{track['id']}",
                    placeholder="BPM"
                )
                if new_bpm != track['bpm']:
                    st.session_state.tracks[track_index]['bpm'] = new_bpm

            with cols[1]:
                new_key = st.text_input(
                    "",
                    value=track['key'],
                    key=f"key_{track['id']}",
                    placeholder="Key(s)"
                )
                if new_key != track['key']:
                    st.session_state.tracks[track_index]['key'] = new_key

            with cols[2]:
                new_meter = st.text_input(
                    "",
                    value=track['meter'],
                    key=f"meter_{track['id']}",
                    placeholder="Meter(s)"
                )
                if new_meter != track['meter']:
                    st.session_state.tracks[track_index]['meter'] = new_meter

            with cols[3]:
                new_instrumentation = st.text_input(
                    "",
                    value=track['instrumentation'],
                    key=f"instrumentation_{track['id']}",
                    placeholder="Instrumentation"
                )
                if new_instrumentation != track['instrumentation']:
                    st.session_state.tracks[track_index]['instrumentation'] = new_instrumentation

            # Display warning or success message
            if all([track['bpm'], track['key'], track['meter'], track['instrumentation']]):
                st.success("✅ All info is provided")
            else:
                missing_fields = [field for field in ['BPM', 'Key', 'Meter', 'Instrumentation'] if not track[field.lower()]]
                st.warning(f"❌ Missing: {', '.join(missing_fields)}")

            st.markdown("</div>", unsafe_allow_html=True)

    # Add track button
    st.button("𝗔𝗗𝗗 𝗔𝗡𝗢𝗧𝗛𝗘𝗥 𝗧𝗥𝗔𝗖𝗞", on_click=add_track)

    # Submit button

    # Submit button
submit_button_key = "submit_button"  # Unique key for the submit button
if all_track_info_provided():
    if st.button("𝗦𝗨𝗕𝗠𝗜𝗧", key=submit_button_key):
        file_path = generate_excel_file()
        if send_email_with_excel("nicolas.techer@warnerchappellpm.com", file_path):
            st.success("Submission complete")
        else:
            st.error("Failed to send email. Please check the error messages above.")
else:
    st.button("𝗦𝗨𝗕𝗠𝗜𝗧", key=submit_button_key, disabled=True)
    st.warning("You must provide all track info to be able to submit this form.")
