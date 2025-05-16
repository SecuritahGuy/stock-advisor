"""
Notification module for sending alerts about trading signals.
"""
import logging
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("notify")


def check_email_configuration():
    """
    Check if email configuration is set up and log warnings if not.
    """
    smtp_username = os.getenv("SMTP_USERNAME")
    smtp_password = os.getenv("SMTP_PASSWORD")
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = os.getenv("SMTP_PORT")

    if not all([smtp_username, smtp_password, smtp_server, smtp_port]):
        logger.warning("Email configuration is incomplete. Notifications will be disabled.")
    else:
        logger.info("Email configuration is set up correctly.")


class EmailNotifier:
    """Class for sending email notifications."""
    
    def __init__(self, smtp_server=None, smtp_port=None, username=None, password=None, 
                 sender=None, recipients=None):
        """
        Initialize the email notifier.
        
        Args:
            smtp_server (str): SMTP server address
            smtp_port (int): SMTP server port
            username (str): SMTP username
            password (str): SMTP password
            sender (str): Sender email address
            recipients (list): List of recipient email addresses
        """
        # Use provided values or environment variables
        self.smtp_server = smtp_server or os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = smtp_port or int(os.environ.get('SMTP_PORT', 587))
        self.username = username or os.environ.get('SMTP_USERNAME')
        self.password = password or os.environ.get('SMTP_PASSWORD')
        self.sender = sender or os.environ.get('EMAIL_SENDER')
        self.recipients = recipients or os.environ.get('EMAIL_RECIPIENTS', '').split(',')
        
        # Validate configuration
        self._validate_config()
    
    def _validate_config(self):
        """Validate email configuration."""
        missing = []
        
        if not self.smtp_server:
            missing.append("SMTP_SERVER")
        if not self.smtp_port:
            missing.append("SMTP_PORT")
        if not self.username:
            missing.append("SMTP_USERNAME")
        if not self.password:
            missing.append("SMTP_PASSWORD")
        if not self.sender:
            missing.append("EMAIL_SENDER")
        if not self.recipients or not self.recipients[0]:
            missing.append("EMAIL_RECIPIENTS")
        
        if missing:
            logger.warning(f"Missing email configuration: {', '.join(missing)}")
            logger.warning("Email notifications will be disabled")
            self.enabled = False
        else:
            self.enabled = True
            logger.info(f"Email notifications configured for {len(self.recipients)} recipients")
    
    def send_signal_alert(self, signal):
        """
        Send an email alert for a new trading signal.
        
        Args:
            signal: Signal object
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.enabled:
            logger.warning("Email notifications are disabled due to missing configuration")
            return False
        
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.sender
            msg['To'] = ', '.join(self.recipients)
            
            # Set subject based on signal type
            action = signal.action.value
            msg['Subject'] = f"Stock Advisor {action} Signal: {signal.ticker}"
            
            # Create email body
            body = f"""
            <html>
            <body>
                <h2>New Trading Signal</h2>
                <p><strong>Action:</strong> {action}</p>
                <p><strong>Ticker:</strong> {signal.ticker}</p>
                <p><strong>Price:</strong> ${signal.price:.2f}</p>
                <p><strong>Strength:</strong> {signal.strength.value}</p>
                <p><strong>Reason:</strong> {signal.reason}</p>
                <p><strong>Timestamp:</strong> {signal.timestamp.strftime('%Y-%m-%d %H:%M:%S')}</p>
                <hr>
                <p><em>This is an automated alert from your Stock Advisor application. 
                This is not financial advice. Always do your own research before making
                investment decisions.</em></p>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(body, 'html'))
            
            # Connect to SMTP server
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.username, self.password)
            
            # Send email
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Sent {action} signal alert for {signal.ticker} to {len(self.recipients)} recipients")
            return True
            
        except Exception as e:
            logger.error(f"Error sending email alert: {str(e)}")
            return False
    
    def send_daily_summary(self, portfolio_data, signals, metrics):
        """
        Send a daily summary email with portfolio performance and signals.
        
        Args:
            portfolio_data (dict): Portfolio valuation data
            signals (list): List of Signal objects from today
            metrics (dict): Portfolio performance metrics
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.enabled:
            logger.warning("Email notifications are disabled due to missing configuration")
            return False
        
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.sender
            msg['To'] = ', '.join(self.recipients)
            
            # Set subject
            today = datetime.now().strftime('%Y-%m-%d')
            msg['Subject'] = f"Stock Advisor Daily Summary - {today}"
            
            # Create email body
            body = f"""
            <html>
            <body>
                <h1>Stock Advisor Daily Summary</h1>
                <p>{today}</p>
                
                <h2>Portfolio Performance</h2>
                <table border="1" cellpadding="5" cellspacing="0">
                    <tr>
                        <th>Metric</th>
                        <th>Value</th>
                    </tr>
                    <tr>
                        <td>Total Value</td>
                        <td>${portfolio_data['total_value']:.2f}</td>
                    </tr>
                    <tr>
                        <td>Total Cost</td>
                        <td>${portfolio_data['total_cost']:.2f}</td>
                    </tr>
                    <tr>
                        <td>Total P/L</td>
                        <td>${portfolio_data['total_pl']:.2f} ({portfolio_data['total_pl_pct']:.2f}%)</td>
                    </tr>
                </table>
                
                <h2>Positions</h2>
                <table border="1" cellpadding="5" cellspacing="0">
                    <tr>
                        <th>Ticker</th>
                        <th>Shares</th>
                        <th>Cost Basis</th>
                        <th>Current Price</th>
                        <th>Current Value</th>
                        <th>P/L</th>
                        <th>P/L %</th>
                    </tr>
            """
            
            # Add position rows
            for position in portfolio_data['positions']:
                body += f"""
                    <tr>
                        <td>{position['ticker']}</td>
                        <td>{position['shares']:.2f}</td>
                        <td>${position['cost_basis']:.2f}</td>
                        <td>${position.get('current_price', 0):.2f}</td>
                        <td>${position['current_value']:.2f}</td>
                        <td>${position['pl']:.2f}</td>
                        <td>{position['pl_pct']:.2f}%</td>
                    </tr>
                """
            
            body += """
                </table>
            """
            
            # Add signals section if there are any
            if signals:
                body += """
                <h2>Today's Signals</h2>
                <table border="1" cellpadding="5" cellspacing="0">
                    <tr>
                        <th>Time</th>
                        <th>Ticker</th>
                        <th>Action</th>
                        <th>Price</th>
                        <th>Reason</th>
                    </tr>
                """
                
                for signal in signals:
                    body += f"""
                    <tr>
                        <td>{signal.timestamp.strftime('%H:%M:%S')}</td>
                        <td>{signal.ticker}</td>
                        <td>{signal.action.value}</td>
                        <td>${signal.price:.2f}</td>
                        <td>{signal.reason}</td>
                    </tr>
                    """
                
                body += """
                </table>
                """
            else:
                body += "<h2>Today's Signals</h2><p>No signals generated today.</p>"
            
            # Add metrics section
            if metrics:
                body += """
                <h2>Performance Metrics</h2>
                <table border="1" cellpadding="5" cellspacing="0">
                    <tr>
                        <th>Metric</th>
                        <th>Value</th>
                    </tr>
                """
                
                if 'percent_return' in metrics:
                    body += f"""
                    <tr>
                        <td>Return ({metrics.get('period', 'all')})</td>
                        <td>{metrics['percent_return']:.2f}%</td>
                    </tr>
                    """
                
                if 'annualized_return' in metrics:
                    body += f"""
                    <tr>
                        <td>Annualized Return</td>
                        <td>{metrics['annualized_return']:.2f}%</td>
                    </tr>
                    """
                
                if 'volatility' in metrics:
                    body += f"""
                    <tr>
                        <td>Volatility (Ann.)</td>
                        <td>{metrics['volatility']:.2f}%</td>
                    </tr>
                    """
                
                if 'sharpe_ratio' in metrics:
                    body += f"""
                    <tr>
                        <td>Sharpe Ratio</td>
                        <td>{metrics['sharpe_ratio']:.2f}</td>
                    </tr>
                    """
                
                body += """
                </table>
                """
            
            # Close the email body
            body += """
                <hr>
                <p><em>This is an automated report from your Stock Advisor application. 
                This is not financial advice. Always do your own research before making
                investment decisions.</em></p>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(body, 'html'))
            
            # Connect to SMTP server
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.username, self.password)
            
            # Send email
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Sent daily summary to {len(self.recipients)} recipients")
            return True
            
        except Exception as e:
            logger.error(f"Error sending daily summary: {str(e)}")
            return False
