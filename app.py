import os
import subprocess
import csv
import re
import logging
import tempfile
import threading
from io import StringIO
from datetime import datetime
from urllib.parse import urlparse
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
from flask import Flask, render_template, request, jsonify, make_response, redirect, url_for, flash, send_file

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "subdomain-scanner-secret-key")

# Configure database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Import database module and models
from database import db
import models

# Initialize database with app
db.init_app(app)

# Create all tables
with app.app_context():
    db.create_all()

# Add current year to all templates
@app.context_processor
def inject_year():
    return {'current_year': datetime.now().year}

class SubdomainScanner:
    def __init__(self):
        self.active_domains = []
        self.inactive_domains = []
        self.scan_results = []
        self.domain = None
        self.scan_completed = False
        self.scan_in_progress = False
        self.error_message = None
    
    def validate_domain(self, domain):
        """Validate if the input is a proper domain name"""
        # Simple domain validation regex
        pattern = r'^([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$'
        return bool(re.match(pattern, domain))
    
    def scan_subdomains(self, domain):
        """Scan subdomains using subfinder and dnsx tools or simulates it if not available"""
        self.domain = domain
        self.active_domains = []
        self.inactive_domains = []
        self.scan_results = []
        self.error_message = None
        self.scan_completed = False
        self.scan_in_progress = True
        
        try:
            # Check if subfinder is installed
            has_subfinder = subprocess.run(["which", "subfinder"], stdout=subprocess.PIPE, stderr=subprocess.PIPE).returncode == 0
            
            if has_subfinder:
                # Run subfinder command
                logger.debug(f"Starting subdomain scan for {domain}")
                process = subprocess.Popen(
                    f"subfinder -silent -d {domain}",
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                stdout, stderr = process.communicate()
                
                if process.returncode != 0 and not stdout:
                    logger.error(f"Error executing the command: {stderr}")
                    self.error_message = f"Error executing the subdomain enumeration: {stderr}"
                    self.scan_in_progress = False
                    return False
                
                # Process the output - split by lines and remove empty lines
                subdomains = [line.strip() for line in stdout.split('\n') if line.strip()]
            else:
                # If tool is not available, use common subdomain prefixes
                logger.warning("subfinder not installed. Using built-in subdomain list")
                common_subdomains = ["www", "api", "mail", "blog", "shop", "store", "admin", "dev", "test", "app", "m"]
                subdomains = [f"{prefix}.{domain}" for prefix in common_subdomains]
                
            logger.debug(f"Found {len(subdomains)} subdomains")
            
            # Check liveness of each subdomain
            for subdomain in subdomains:
                self._check_domain_liveness(subdomain)
            
            self.scan_completed = True
            logger.info(f"Scan completed. Found {len(self.active_domains)} active and {len(self.inactive_domains)} inactive domains")
            
            # Save results to database
            self._save_to_database()
            
            return True
            
        except Exception as e:
            logger.exception("Error during subdomain scanning")
            self.error_message = f"Error during scan: {str(e)}"
            return False
        finally:
            self.scan_in_progress = False
    
    def _check_domain_liveness(self, domain):
        """Check if a domain is active by making a curl request"""
        try:
            # Ensure domain has http/https prefix
            if not domain.startswith(('http://', 'https://')):
                domain_with_protocol = f"https://{domain}"
            else:
                domain_with_protocol = domain
            
            # Execute curl command with timeout and verbose output
            # -I returns headers only
            # -v provides verbose output that includes protocol details
            # --max-time 3 limits request time to 3 seconds
            # -k ignores SSL certificate errors
            logger.debug(f"Checking liveness for {domain_with_protocol}")
            process = subprocess.Popen(
                f"curl -I -v --max-time 3 -k {domain_with_protocol}",
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            stdout, stderr = process.communicate()
            
            # Check if domain is active based on response
            is_active = process.returncode == 0
            
            # Get the first line of the response instead of just the status code
            # Look in both stdout and stderr because curl -v puts protocol info in stderr
            response_info = "No response"
            combined_output = stdout + stderr
            
            if is_active or "HTTP/" in combined_output:  # Domain might be active even if curl reports an error
                # Check for HTTP status line with various patterns
                # First try the standard HTTP response format
                status_line_match = re.search(r'(HTTP/\d(?:\.\d)? \d{3}.*?)[\r\n]', combined_output)
                if status_line_match:
                    response_info = status_line_match.group(1).strip()
                    is_active = True  # If we found a response line, consider it active
                else:
                    # Try alternate format sometimes seen in curl verbose output with < prefix
                    status_line_match = re.search(r'< (HTTP/\d(?:\.\d)? \d{3}.*?)[\r\n]', combined_output)
                    if status_line_match:
                        response_info = status_line_match.group(1).strip()
                        is_active = True  # If we found a response line, consider it active
                    else:
                        # Try a more flexible regex just looking for HTTP and status code
                        status_line_match = re.search(r'HTTP/\d(?:\.\d)? (\d{3})', combined_output)
                        if status_line_match:
                            status_code = status_line_match.group(1)
                            response_info = f"HTTP/2 {status_code}"
                            is_active = True  # If we found a response line, consider it active
                        else:
                            # As a fallback, check if we have a 200 OK anywhere in the response
                            if "200 OK" in combined_output:
                                response_info = "HTTP/2 200 OK"
                                is_active = True  # If we found a response line, consider it active
            
            # For debugging
            if is_active and response_info == "No response":
                logger.debug(f"Domain {domain} is marked active but no HTTP response was found")
                logger.debug(f"Curl output: {combined_output[:200]}...")  # Log the first 200 chars
            
            # Store the result
            result = {
                'domain': domain,
                'is_active': is_active,
                'response_info': response_info,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'response_headers': stdout if is_active else None
            }
            
            self.scan_results.append(result)
            
            if is_active:
                self.active_domains.append(result)
            else:
                self.inactive_domains.append(result)
                
            logger.debug(f"Domain {domain} is {'active' if is_active else 'inactive'}")
            
        except Exception as e:
            logger.exception(f"Error checking liveness for {domain}")
            # Consider the domain inactive if there's an error
            result = {
                'domain': domain,
                'is_active': False,
                'response_info': f"Error: {str(e)[:50]}...",
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'error': str(e)
            }
            self.scan_results.append(result)
            self.inactive_domains.append(result)
    
    def _save_to_database(self):
        """Save scan results to database"""
        from models import ScanHistory, ScanResult
        
        try:
            # Create scan history record
            scan_history = ScanHistory(
                domain=self.domain,
                active_count=len(self.active_domains),
                inactive_count=len(self.inactive_domains),
                total_count=len(self.scan_results)
            )
            db.session.add(scan_history)
            db.session.flush()  # Flush to get the ID
            
            # Create scan result records
            for result in self.scan_results:
                scan_result = ScanResult(
                    scan_id=scan_history.id,
                    subdomain=result['domain'],
                    is_active=result['is_active'],
                    response_info=result['response_info'],
                    timestamp=datetime.strptime(result['timestamp'], "%Y-%m-%d %H:%M:%S")
                )
                db.session.add(scan_result)
            
            # Commit the transaction
            db.session.commit()
            logger.info(f"Saved scan results to database. Scan ID: {scan_history.id}")
            
        except Exception as e:
            logger.exception("Error saving scan results to database")
            db.session.rollback()
    
    def get_csv_data(self):
        """Generate CSV data from scan results"""
        if not self.scan_results:
            return None
        
        output = StringIO()
        csv_writer = csv.writer(output)
        
        # Write header
        csv_writer.writerow(['Domain', 'Status', 'Response Info', 'Timestamp'])
        
        # Write data
        for result in self.scan_results:
            csv_writer.writerow([
                result['domain'],
                'Active' if result['is_active'] else 'Inactive',
                result['response_info'] if result.get('response_info') else 'N/A',
                result['timestamp']
            ])
        
        return output.getvalue()

# Create a scanner instance
scanner = SubdomainScanner()

@app.route('/')
def index():
    return render_template('index.html', 
                           scanner=scanner, 
                           active_domains=scanner.active_domains,
                           inactive_domains=scanner.inactive_domains)

@app.route('/scan', methods=['POST'])
def scan():
    domain = request.form.get('domain', '').strip()
    
    if not domain:
        flash('Please enter a domain', 'danger')
        return redirect(url_for('index'))
    
    if not scanner.validate_domain(domain):
        flash('Please enter a valid domain name', 'danger')
        return redirect(url_for('index'))
    
    # Start scanning in a new thread
    success = scanner.scan_subdomains(domain)
    
    if not success and scanner.error_message:
        flash(scanner.error_message, 'danger')
    
    return redirect(url_for('index'))

@app.route('/export')
def export():
    if not scanner.scan_completed or not scanner.scan_results:
        flash('No scan results available to export', 'warning')
        return redirect(url_for('index'))
    
    csv_data = scanner.get_csv_data()
    if not csv_data:
        flash('Error generating CSV data', 'danger')
        return redirect(url_for('index'))
    
    # Create a response with CSV data
    response = make_response(csv_data)
    filename = f"subdomain_scan_{scanner.domain}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    response.headers['Content-Disposition'] = f'attachment; filename={filename}'
    response.headers['Content-Type'] = 'text/csv'
    
    return response

@app.route('/status')
def scan_status():
    """API endpoint to get the current scan status"""
    return jsonify({
        'scan_in_progress': scanner.scan_in_progress,
        'scan_completed': scanner.scan_completed,
        'active_count': len(scanner.active_domains),
        'inactive_count': len(scanner.inactive_domains),
        'total_count': len(scanner.scan_results),
        'error_message': scanner.error_message
    })
    
@app.route('/recheck/<path:domain>', methods=['POST'])
def recheck_domain(domain):
    """API endpoint to recheck a specific domain for its response"""
    try:
        # Ensure domain has http/https prefix
        if not domain.startswith(('http://', 'https://')):
            domain_with_protocol = f"https://{domain}"
        else:
            domain_with_protocol = domain
        
        # Execute curl command with timeout and verbose output
        logger.debug(f"Re-checking domain: {domain_with_protocol}")
        process = subprocess.Popen(
            f"curl -I -v --max-time 5 -k {domain_with_protocol}",  # Increased timeout for recheck
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = process.communicate()
        
        # Get the response info
        response_info = "No response"
        combined_output = stdout + stderr
        
        # Check if we got a response (even if curl returned an error code)
        is_active = process.returncode == 0 or "HTTP/" in combined_output
        
        # Check for HTTP status line with various patterns
        # First try the standard HTTP response format
        status_line_match = re.search(r'(HTTP/\d(?:\.\d)? \d{3}.*?)[\r\n]', combined_output)
        if status_line_match:
            response_info = status_line_match.group(1).strip()
        else:
            # Try alternate format sometimes seen in curl verbose output with < prefix
            status_line_match = re.search(r'< (HTTP/\d(?:\.\d)? \d{3}.*?)[\r\n]', combined_output)
            if status_line_match:
                response_info = status_line_match.group(1).strip()
            else:
                # Try a more flexible regex just looking for HTTP and status code
                status_line_match = re.search(r'HTTP/\d(?:\.\d)? (\d{3})', combined_output)
                if status_line_match:
                    status_code = status_line_match.group(1)
                    response_info = f"HTTP/2 {status_code}"
                else:
                    # As a fallback, check if we have a 200 OK anywhere in the response
                    if "200 OK" in combined_output:
                        response_info = "HTTP/2 200 OK"
        
        # For debugging
        logger.debug(f"Recheck result for {domain}: response_info={response_info}, is_active={is_active}")
        if is_active and response_info == "No response":
            logger.debug(f"Domain {domain} is marked active but no HTTP response was found")
            logger.debug(f"Curl output: {combined_output[:500]}...")  # Log the first 500 chars
        
        # Update the domain in scan results if it exists
        domain_updated = False
        for result in scanner.scan_results:
            if result['domain'] == domain:
                result['response_info'] = response_info
                # Update the is_active status if we received a response
                if response_info != "No response":
                    result['is_active'] = True
                domain_updated = True
                
                # Also update in active/inactive domains lists
                if result['is_active']:
                    for active_result in scanner.active_domains:
                        if active_result['domain'] == domain:
                            active_result['response_info'] = response_info
                            break
                else:
                    for inactive_result in scanner.inactive_domains:
                        if inactive_result['domain'] == domain:
                            inactive_result['response_info'] = response_info
                            # If domain is now active, move it from inactive to active list
                            if response_info != "No response":
                                inactive_result['is_active'] = True
                                scanner.active_domains.append(inactive_result)
                                scanner.inactive_domains.remove(inactive_result)
                            break
                break
        
        # Always return success with the response, even if we couldn't update the domain in results
        # This lets the user still see the fresh curl result
        return jsonify({
            'success': True, 
            'domain': domain, 
            'response_info': response_info
        })
            
    except Exception as e:
        logger.exception(f"Error rechecking domain {domain}")
        return jsonify({
            'success': False, 
            'error': str(e)
        }), 500

@app.route('/history')
def history():
    """Show scan history from the database"""
    from models import ScanHistory
    
    # Get all scan history records, ordered by newest first
    scan_histories = ScanHistory.query.order_by(ScanHistory.timestamp.desc()).all()
    
    return render_template('history.html', scan_histories=scan_histories)

@app.route('/history/<int:scan_id>')
def history_detail(scan_id):
    """Show detailed results for a specific scan"""
    from models import ScanHistory, ScanResult
    
    # Get the scan history record
    scan_history = ScanHistory.query.get_or_404(scan_id)
    
    # Get all results for this scan
    results = ScanResult.query.filter_by(scan_id=scan_id).all()
    
    # Separate active and inactive domains
    active_domains = [r for r in results if r.is_active]
    inactive_domains = [r for r in results if not r.is_active]
    
    return render_template('history_detail.html', 
                          scan_history=scan_history, 
                          results=results,
                          active_domains=active_domains,
                          inactive_domains=inactive_domains)

@app.route('/history/delete/<int:scan_id>', methods=['POST'])
def delete_history(scan_id):
    """Delete a specific scan history and all its results"""
    from models import ScanHistory
    
    # Get the scan history record
    scan_history = ScanHistory.query.get_or_404(scan_id)
    
    try:
        # The 'cascade' option in the relationship will automatically delete related results
        db.session.delete(scan_history)
        db.session.commit()
        flash(f'Scan history for {scan_history.domain} has been deleted', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting scan history: {e}")
        flash('An error occurred while deleting the scan history', 'danger')
        
    return redirect(url_for('history'))

@app.route('/setup')
def setup():
    """Show setup documentation"""
    return render_template('setup.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003, debug=True)
