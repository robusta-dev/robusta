import logging
import tempfile
import time
import re
from typing import List, Optional
from urllib.parse import parse_qs, urlparse

import apprise
from apprise import NotifyFormat, NotifyType
from apprise.attachment.AttachFile import AttachFile
from apprise.AppriseAttachment import AppriseAttachment

from robusta.core.reporting.base import BaseBlock, Emojis, Finding, FindingStatus
from robusta.core.reporting.blocks import MarkdownBlock

from robusta.core.reporting.consts import EnrichmentAnnotation, FindingSource
from robusta.core.sinks.common.html_tools import (
    HTMLBaseSender,
    HTMLTransformer,
    with_attr,
)
from robusta.core.sinks.transformer import Transformer


class MailSender(HTMLBaseSender):
    def __init__(
        self,
        mailto: str,
        account_id: str,
        cluster_name: str,
        signing_key: str,
        use_ses: bool = False,
        aws_region: Optional[str] = None,
        from_email: Optional[str] = None,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        configuration_set: Optional[str] = None,
        skip_ses_init: bool = False,
    ):
        self.mailto = mailto
        self.signing_key = signing_key
        self.account_id = account_id
        self.cluster_name = cluster_name

        # SES configuration
        self.use_ses = use_ses
        self.from_email = from_email
        self.configuration_set = configuration_set
        self.ses_client = None

        if use_ses and not skip_ses_init:
            self._initialize_ses_client(
                aws_region, aws_access_key_id, aws_secret_access_key
            )

    def _initialize_ses_client(
        self,
        aws_region: str,
        aws_access_key_id: Optional[str],
        aws_secret_access_key: Optional[str],
    ):
        """Initialize AWS SES client with proper error handling"""
        try:
            import boto3
            from botocore.exceptions import BotoCoreError, ClientError

            session_kwargs = {"region_name": aws_region}
            if aws_access_key_id and aws_secret_access_key:
                session_kwargs.update(
                    {
                        "aws_access_key_id": aws_access_key_id,
                        "aws_secret_access_key": aws_secret_access_key,
                    }
                )

            self.ses_client = boto3.client("ses", **session_kwargs)

            # Verify SES configuration by checking send quota
            self.ses_client.get_send_quota()
            logging.info("SES client initialized successfully")

        except ImportError:
            logging.error("boto3 not available. Install boto3 to use SES functionality")
            raise
        except (BotoCoreError, ClientError) as e:
            logging.error(f"Failed to initialize SES client: {e}")
            raise
        except Exception as e:
            logging.error(f"Unexpected error initializing SES client: {e}")
            raise

    def send_finding(
        self, finding: Finding, platform_enabled: bool, include_headers: bool
    ):
        """Route to appropriate send method based on configuration"""
        if self.use_ses:
            self.send_finding_via_ses(finding, platform_enabled, include_headers)
        else:
            self._send_finding_via_apprise(finding, platform_enabled, include_headers)

    def _send_finding_via_apprise(
        self, finding: Finding, platform_enabled: bool, include_headers: bool
    ):
        """Send finding using existing Apprise functionality"""
        blocks = self._build_email_blocks(finding, platform_enabled, include_headers)
        transformer = HTMLTransformer()
        html_body = self.__build_html(transformer.to_html(blocks).strip())

        ap_obj = apprise.Apprise()
        attachments = AppriseAttachment()
        attachment_files = []
        try:
            for file_block in transformer.file_blocks:
                # This is awkward, but it's the standard way to handle
                # attachments in apprise - by providing local filesystem
                # names.
                f = tempfile.NamedTemporaryFile()
                attachment_files.append(f)
                f.write(file_block.contents)
                attachment = AttachFile(f.name, name=file_block.filename)
                attachments.add(attachment)
            ap_obj.add(self.mailto)
            logging.debug(
                f"MailSender: sending title={finding.title}, body={html_body}"
            )

            status = (
                FindingStatus.RESOLVED
                if finding.title.startswith("[RESOLVED]")
                else FindingStatus.FIRING
            )
            ap_obj.notify(
                title=finding.title,
                body=html_body,
                body_format=NotifyFormat.HTML,
                notify_type=NotifyType.SUCCESS
                if status == FindingStatus.RESOLVED
                else NotifyType.WARNING,
                attach=attachments,
            )
        finally:
            for f in attachment_files:
                try:
                    f.close()
                except Exception:
                    pass

    def send_finding_via_ses(
        self, finding: Finding, platform_enabled: bool, include_headers: bool
    ):
        """Send finding using AWS SES"""
        if self.ses_client is None:
            logging.warning("SES client not initialized, falling back to Apprise")
            self._send_finding_via_apprise(finding, platform_enabled, include_headers)
            return

        recipients = self._extract_recipients_from_mailto(self.mailto)

        # Build email content
        blocks = self._build_email_blocks(finding, platform_enabled, include_headers)
        transformer = HTMLTransformer()
        html_body = self.__build_html(transformer.to_html(blocks).strip())
        text_body = self._build_text_version(blocks)

        # Prepare SES message
        destination = {"ToAddresses": recipients}
        message = {
            "Subject": {"Data": finding.title, "Charset": "UTF-8"},
            "Body": {
                "Html": {"Data": html_body, "Charset": "UTF-8"},
                "Text": {"Data": text_body, "Charset": "UTF-8"},
            },
        }

        # Handle attachments using SES raw email
        if transformer.file_blocks:
            self._send_ses_with_attachments(
                destination, message, transformer.file_blocks
            )
        else:
            self._send_ses_simple_email(destination, message)

    def _build_email_blocks(
        self, finding: Finding, platform_enabled: bool, include_headers: bool
    ) -> List[BaseBlock]:
        """Build email content blocks (shared between Apprise and SES)"""
        blocks: List[BaseBlock] = []

        status: FindingStatus = (
            FindingStatus.RESOLVED
            if finding.title.startswith("[RESOLVED]")
            else FindingStatus.FIRING
        )

        if include_headers:
            blocks.append(self.__create_finding_header(finding, status))
            links_block = self.create_links(finding, "header_links", platform_enabled)
            if links_block:
                blocks.append(links_block)

            blocks.append(MarkdownBlock(text=f"*Source:* `{self.cluster_name}`"))

        if finding.description:
            if finding.source == FindingSource.PROMETHEUS:
                blocks.append(
                    MarkdownBlock(
                        f"{Emojis.Alert.value} *Alert:* {finding.description}"
                    )
                )
            elif finding.source == FindingSource.KUBERNETES_API_SERVER:
                blocks.append(
                    MarkdownBlock(
                        f"{Emojis.K8Notification.value} *K8s event detected:* {finding.description}"
                    )
                )
            else:
                blocks.append(
                    MarkdownBlock(
                        f"{Emojis.K8Notification.value} *Notification:* {finding.description}"
                    )
                )

        for enrichment in finding.enrichments:
            if enrichment.annotations.get(EnrichmentAnnotation.SCAN, False):
                enrichment.blocks = [
                    Transformer.scanReportBlock_to_fileblock(b)
                    for b in enrichment.blocks
                ]
            blocks.extend(enrichment.blocks)

        return blocks

    def _extract_recipients_from_mailto(self, mailto_url: str) -> List[str]:
        """Extract recipient email addresses from mailto URL"""
        recipients = []

        # Parse the mailto URL to extract recipients
        parsed = urlparse(mailto_url)
        if parsed.scheme in ["mailto", "mailtos"]:
            # Get the main recipient from the netloc (for mailtos://) or path (for mailto:)
            if parsed.netloc:
                recipients.append(parsed.netloc)
            elif parsed.path:
                recipients.append(parsed.path)

            # Get additional recipients from query parameters
            query_params = parse_qs(parsed.query)
            if "to" in query_params:
                # Handle comma-separated recipients in query parameter
                for to_param in query_params["to"]:
                    if "," in to_param:
                        recipients.extend(
                            [email.strip() for email in to_param.split(",")]
                        )
                    else:
                        recipients.append(to_param)

        # Fallback: extract email addresses using regex
        if not recipients:
            email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
            recipients = re.findall(email_pattern, mailto_url)

        return recipients

    def _build_text_version(self, blocks: List[BaseBlock]) -> str:
        """Build plain text version of email content"""
        text_parts = []
        for block in blocks:
            if hasattr(block, "text"):
                # Simple markdown to text conversion
                text = block.text
                # Remove markdown formatting
                text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)  # Bold
                text = re.sub(r"\*(.*?)\*", r"\1", text)  # Italic
                text = re.sub(r"`(.*?)`", r"\1", text)  # Code
                text = re.sub(r"<(.*?)\|(.*?)>", r"\2 (\1)", text)  # Links
                text_parts.append(text)

        return "\n\n".join(text_parts)

    def _send_ses_simple_email(self, destination, message):
        """Send simple SES email without attachments"""
        try:
            from botocore.exceptions import ClientError

            kwargs = {
                "Source": self.from_email,
                "Destination": destination,
                "Message": message,
            }
            if self.configuration_set:
                kwargs["ConfigurationSetName"] = self.configuration_set

            response = self.ses_client.send_email(**kwargs)
            logging.info(
                f"SES email sent successfully. MessageId: {response['MessageId']}"
            )

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "Throttling":
                logging.warning("SES rate limit exceeded, retrying after delay")
                time.sleep(1)
                # Retry the operation
                response = self.ses_client.send_email(**kwargs)
                logging.info(
                    f"SES email sent successfully after retry. MessageId: {response['MessageId']}"
                )
            elif error_code == "MessageRejected":
                logging.error(f"SES message rejected: {e.response['Error']['Message']}")
                raise
            elif error_code == "SendingPausedException":
                logging.error("SES sending is paused for this account")
                raise
            else:
                logging.error(f"SES send failed: {e}")
                raise

    def _send_ses_with_attachments(self, destination, message, file_blocks):
        """Send SES raw email with attachments using email.mime"""
        try:
            from email.mime.multipart import MIMEMultipart
            from email.mime.text import MIMEText
            from email.mime.application import MIMEApplication
            from botocore.exceptions import ClientError

            # Build MIME message
            msg = MIMEMultipart()
            msg["From"] = self.from_email
            msg["To"] = ", ".join(destination["ToAddresses"])
            msg["Subject"] = message["Subject"]["Data"]

            # Add HTML and text bodies
            msg.attach(MIMEText(message["Body"]["Html"]["Data"], "html"))
            msg.attach(MIMEText(message["Body"]["Text"]["Data"], "plain"))

            # Add attachments
            for file_block in file_blocks:
                attachment = MIMEApplication(file_block.contents)
                attachment.add_header(
                    "Content-Disposition", "attachment", filename=file_block.filename
                )
                msg.attach(attachment)

            # Send raw email
            kwargs = {"RawMessage": {"Data": msg.as_string()}}
            if self.configuration_set:
                kwargs["ConfigurationSetName"] = self.configuration_set

            response = self.ses_client.send_raw_email(**kwargs)
            logging.info(
                f"SES raw email sent successfully. MessageId: {response['MessageId']}"
            )

        except ClientError as e:
            logging.error(f"SES raw email send failed: {e}")
            raise

    def __create_finding_header(
        self, finding: Finding, status: FindingStatus
    ) -> MarkdownBlock:
        title = finding.title.removeprefix("[RESOLVED] ")
        sev = finding.severity
        status_name: str = (
            "Prometheus Alert Firing" if status == FindingStatus.FIRING else "Resolved"
        )
        status_str: str = (
            f"{status.to_emoji()} `{status_name}`" if finding.add_silence_url else ""
        )
        return with_attr(
            MarkdownBlock(
                f"{status_str} {sev.to_emoji()} `{sev.name.lower()}` "
                f"<{finding.get_investigate_uri(self.account_id, self.cluster_name)}|*{title}*>"
            ),
            "html_class",
            "header",
        )

    def __build_html(self, body):
        return f"""<html>
<style>
{self.get_css()}
</style>
<body>

{body}

</body>
</html>
"""
