#!/usr/bin/env python3
"""
Generate diverse dummy log files for testing sentinel-rs.

This script creates realistic log files with various formats containing
fake PII data (emails, IPs, credit cards, etc.) for benchmarking and testing.
"""

import random
import string
from datetime import datetime, timedelta
from pathlib import Path


# Fake data generators
FIRST_NAMES = ['John', 'Jane', 'Bob', 'Alice', 'Charlie', 'Diana', 'Eve', 'Frank', 'Grace', 'Henry']
LAST_NAMES = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Rodriguez', 'Martinez']
DOMAINS = ['gmail.com', 'yahoo.com', 'hotmail.com', 'company.com', 'example.org', 'test.net', 'acme.io']
SERVICES = ['AuthService', 'UserService', 'PaymentService', 'DatabaseService', 'CacheService', 'APIGateway', 'MessageQueue']
ACTIONS = ['login', 'logout', 'register', 'update', 'delete', 'query', 'insert', 'fetch', 'validate', 'process']
ERROR_TYPES = ['NullPointerException', 'TimeoutError', 'ValidationError', 'DatabaseError', 'NetworkError', 'AuthError']


def random_email():
    """Generate a random email address."""
    first = random.choice(FIRST_NAMES).lower()
    last = random.choice(LAST_NAMES).lower()
    num = random.randint(0, 999)
    domain = random.choice(DOMAINS)
    return f"{first}.{last}{num}@{domain}"


def random_ip():
    """Generate a random IPv4 address."""
    return f"{random.randint(1, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 255)}"


def random_ipv6():
    """Generate a random IPv6 address."""
    return ':'.join(f'{random.randint(0, 65535):04x}' for _ in range(8))


def random_credit_card():
    """Generate a fake credit card number."""
    return f"{random.randint(1000, 9999)}-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}"


def random_ssn():
    """Generate a fake SSN."""
    return f"{random.randint(100, 999)}-{random.randint(10, 99)}-{random.randint(1000, 9999)}"


def random_phone():
    """Generate a fake phone number."""
    return f"+1-{random.randint(200, 999)}-{random.randint(200, 999)}-{random.randint(1000, 9999)}"


def random_api_key():
    """Generate a fake API key."""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=random.choice([32, 40, 64])))


def random_aws_key():
    """Generate a fake AWS access key."""
    return 'AKIA' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=16))


def random_token():
    """Generate a fake bearer token."""
    token = ''.join(random.choices(string.ascii_letters + string.digits + '-._', k=random.randint(30, 50)))
    return f"Bearer {token}"


def random_timestamp():
    """Generate a random timestamp in the past week."""
    now = datetime.now()
    delta = timedelta(seconds=random.randint(0, 7 * 24 * 3600))
    ts = now - delta
    return ts.strftime('%Y-%m-%d %H:%M:%S')


def random_iso_timestamp():
    """Generate a random ISO format timestamp."""
    now = datetime.now()
    delta = timedelta(seconds=random.randint(0, 7 * 24 * 3600))
    ts = now - delta
    return ts.isoformat() + 'Z'


# Log format generators (30+ different formats from various systems/contexts)
def generate_log_formats():
    """Generate diverse log line formats."""
    
    formats = [
        # 1. Standard Apache access log
        lambda: f'{random_ip()} - - [{random_timestamp()}] "GET /api/users HTTP/1.1" 200 {random.randint(100, 5000)} "{random_email()}"',
        
        # 2. Application login event
        lambda: f'[{random_timestamp()}] INFO: User {random_email()} logged in from {random_ip()}',
        
        # 3. Authentication failure
        lambda: f'[{random_timestamp()}] WARN: Failed login attempt for {random_email()} from {random_ip()}',
        
        # 4. Database query log
        lambda: f'{random_timestamp()} [DEBUG] Executing query for user_email={random_email()} from host={random_ip()}',
        
        # 5. Payment processing
        lambda: f'{random_iso_timestamp()} PaymentService: Processing payment for card {random_credit_card()} amount=${random.randint(10, 5000)}',
        
        # 6. API request with auth
        lambda: f'[{random_timestamp()}] API Request: POST /api/v1/users auth={random_token()} ip={random_ip()}',
        
        # 7. User registration
        lambda: f'{random_timestamp()} UserService: New registration email={random_email()} phone={random_phone()} ip={random_ip()}',
        
        # 8. Error with stack trace preview
        lambda: f'[{random_timestamp()}] ERROR: {random.choice(ERROR_TYPES)} in {random.choice(SERVICES)} for user {random_email()}',
        
        # 9. Microservice communication
        lambda: f'{random_iso_timestamp()} {random.choice(SERVICES)} -> {random.choice(SERVICES)}: Request from {random_ip()} token={random_api_key()}',
        
        # 10. Cloud service log (AWS-style)
        lambda: f'{random_timestamp()} AWS_ACCESS_KEY_ID={random_aws_key()} Instance={random_ip()} Action=DescribeInstances',
        
        # 11. Email service log
        lambda: f'[{random_timestamp()}] EmailService: Sent notification to {random_email()} from {random_ip()}',
        
        # 12. Session management
        lambda: f'{random_timestamp()} SessionManager: Created session for {random_email()} (IP: {random_ip()}, TTL: 3600s)',
        
        # 13. Security audit log
        lambda: f'AUDIT [{random_timestamp()}] User={random_email()} Action=DELETE Resource=/api/users/{random.randint(1, 10000)} IP={random_ip()}',
        
        # 14. Load balancer log
        lambda: f'{random_timestamp()} LB: {random_ip()}:80 -> {random_ip()}:8080 status=200 bytes={random.randint(100, 10000)}',
        
        # 15. Cache operation
        lambda: f'[{random_timestamp()}] Redis: SET user:{random_email()} from {random_ip()}',
        
        # 16. File upload
        lambda: f'{random_timestamp()} FileUpload: user={random_email()} file=document.pdf size={random.randint(1000, 999999)} ip={random_ip()}',
        
        # 17. WebSocket connection
        lambda: f'[{random_timestamp()}] WS: Client {random_ip()} connected, user={random_email()}',
        
        # 18. Rate limiting
        lambda: f'{random_timestamp()} RateLimiter: Throttling {random_ip()} for user {random_email()} (100 req/min exceeded)',
        
        # 19. Background job
        lambda: f'[{random_timestamp()}] Worker: Processing job send_email args=["{random_email()}"] scheduled_by={random_ip()}',
        
        # 20. OAuth flow
        lambda: f'{random_timestamp()} OAuth: Authorization code generated for {random_email()} redirect_uri=https://app.com/callback?token={random_api_key()}',
        
        # 21. Password reset
        lambda: f'[{random_timestamp()}] PasswordReset: Token sent to {random_email()} from IP {random_ip()}',
        
        # 22. Credit card validation
        lambda: f'{random_timestamp()} Validator: Checking card {random_credit_card()} for user {random_email()}',
        
        # 23. KYC verification
        lambda: f'[{random_timestamp()}] KYC: Verification requested ssn={random_ssn()} email={random_email()} ip={random_ip()}',
        
        # 24. JSON-like structured log
        lambda: f'{{"timestamp": "{random_iso_timestamp()}", "level": "INFO", "user": "{random_email()}", "ip": "{random_ip()}", "action": "{random.choice(ACTIONS)}"}}',
        
        # 25. Container orchestration
        lambda: f'{random_timestamp()} k8s: Pod {random.choice(SERVICES)}-{random.randint(1, 99)} started on node {random_ip()}',
        
        # 26. CDN access log
        lambda: f'[{random_timestamp()}] CDN: {random_ip()} -> edge-server.cdn.com GET /assets/app.js status=200 referrer=https://example.com user={random_email()}',
        
        # 27. SMS notification
        lambda: f'{random_timestamp()} SMS: Sent verification code to {random_phone()} for user {random_email()}',
        
        # 28. Database connection pool
        lambda: f'[{random_timestamp()}] DBPool: Connection acquired by {random_ip()} for query on user_email={random_email()}',
        
        # 29. GDPR data export
        lambda: f'{random_timestamp()} GDPR: Data export requested by {random_email()} (IP: {random_ip()}, includes: profile, orders, payments {random_credit_card()})',
        
        # 30. IPv6 traffic
        lambda: f'[{random_timestamp()}] IPv6: Connection from {random_ipv6()} user={random_email()} service={random.choice(SERVICES)}',
        
        # 31. Multi-factor authentication
        lambda: f'{random_timestamp()} MFA: Code sent to {random_phone()} for {random_email()} from {random_ip()}',
        
        # 32. Admin action
        lambda: f'[{random_timestamp()}] ADMIN: {random_email()} modified user {random_email()} from {random_ip()}',
        
        # 33. Billing event
        lambda: f'{random_timestamp()} Billing: Invoice generated for {random_email()} card={random_credit_card()} amount=${random.randint(10, 1000)}.{random.randint(0, 99):02d}',
    ]
    
    return formats


def generate_logs(output_path: str, num_lines: int = 1_000_000):
    """
    Generate a log file with diverse formats.
    
    Args:
        output_path: Path to the output log file
        num_lines: Number of log lines to generate (default: 1 million)
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    formats = generate_log_formats()
    
    print(f"Generating {num_lines:,} log lines with {len(formats)} different formats...")
    print(f"Output: {output_path}")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        for i in range(num_lines):
            # Randomly select a log format
            log_generator = random.choice(formats)
            log_line = log_generator()
            f.write(log_line + '\n')
            
            # Progress indicator
            if (i + 1) % 100_000 == 0:
                print(f"  Progress: {i + 1:,} / {num_lines:,} lines ({(i+1)/num_lines*100:.1f}%)")
    
    file_size_mb = output_path.stat().st_size / (1024 * 1024)
    print(f"\n✓ Successfully generated {num_lines:,} log lines")
    print(f"✓ File size: {file_size_mb:.2f} MB")
    print(f"✓ Location: {output_path.absolute()}")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Generate diverse dummy log files for testing sentinel-rs'
    )
    parser.add_argument(
        '-o', '--output',
        default='test_logs.log',
        help='Output log file path (default: test_logs.log)'
    )
    parser.add_argument(
        '-n', '--num-lines',
        type=int,
        default=1_000_000,
        help='Number of log lines to generate (default: 1,000,000)'
    )
    
    args = parser.parse_args()
    
    generate_logs(args.output, args.num_lines)


if __name__ == '__main__':
    main()
