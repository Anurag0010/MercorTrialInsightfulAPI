import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os
from typing import List
import csv
from email.utils import make_msgid
from openpyxl import Workbook
from openpyxl.utils import get_column_letter
from openpyxl.styles import Alignment, Font

class EmailSender:
    def __init__(self, smtp_server: str, smtp_port: int, smtp_user: str, smtp_password: str, use_tls: bool = True):        
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.use_tls = use_tls
        self.attachment_filename = None
        self.attachment_filename_in_email = None
        
    def send_email(self, email_message: str, email_from: str, email_subject: str, email_to: List[str], email_cc: List[str] = None, email_bcc: List[str] = None, is_html: bool = False):
        """Send the email with the given configuration."""
        # Create a multipart email
        msg = MIMEMultipart()
        all_recipients = []
        msg['From'] = email_from
        msg['To'] = ', '.join(email_to)
        all_recipients += email_to
        if email_cc:
            msg['Cc'] = ', '.join(email_cc)
            all_recipients += email_cc
        if email_bcc:
            all_recipients += email_bcc
        msg['Subject'] = email_subject
        msg["Message-ID"] = make_msgid()  # Adds a unique Message-ID

        # Add the message body
        msg.attach(MIMEText(email_message, 'plain' if not is_html else 'html'))

        # Send the email via SMTP
        try:
            # Attach the CSV file if it exists
            if self.attachment_filename and os.path.exists(self.attachment_filename):
                with open(self.attachment_filename, 'rb') as attachment:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment.read())
                    encoders.encode_base64(part)
                    part.add_header('Content-Disposition', f'attachment; filename= {self.attachment_filename_in_email}')
                    msg.attach(part)
            
            # Clean up: delete the attachment file after sending the email
            if self.attachment_filename and os.path.exists(self.attachment_filename):
                os.remove(self.attachment_filename)
                print(f"Attachment file '{self.attachment_filename}' deleted.")
            
            # server = smtplib.SMTP_SSL(smtp_server, smtp_port)
            # server.login(smtp_user, smtp_password)
            # server.sendmail(smtp_user, all_recipients, msg.as_string())
            if self.use_tls:
                with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                    server.starttls()  # Enable TLS if required
                    server.login(self.smtp_user, self.smtp_password)
                    server.sendmail(self.smtp_user, all_recipients, msg.as_string())
            else:
                with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port) as server:
                    server.login(self.smtp_user, self.smtp_password)
                    server.sendmail(self.smtp_user, all_recipients, msg.as_string())
            
                    
            print("Email sent successfully! to {}".format(all_recipients))
        except Exception as e:
            print(f"Failed to send email: {str(e)}")

        for col in worksheet.columns:
            max_length = 0
            column = col[0].column_letter  # Get the column name
            column_name = col[0].value
            column_alignment = EXCEL_COL_PROPS.get(column_name, EXCEL_COL_PROPS["__default__"]).get("alignment", "right")
            first_line_alignment = EXCEL_COL_PROPS.get(column_name, EXCEL_COL_PROPS["__default__"]).get("first_line_alignment", "right")
            for i, cell in enumerate(col):
                try:
                    if i == 0:
                        cell.alignment = Alignment(horizontal=first_line_alignment)
                        cell.font = Font(bold=True)
                    else:
                        cell.alignment = Alignment(horizontal=column_alignment)
                    if cell.value:
                        max_length = max(max_length, len(str(cell.value)))
                except:
                    pass

            adjusted_width = (max_length + 2) * 1.2 # Adding a little extra space for readability
            worksheet.column_dimensions[column].width = adjusted_width    
    
    