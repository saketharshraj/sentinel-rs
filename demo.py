#!/usr/bin/env python3
"""
Demo script for sentinel-rs log anonymization engine.

This script demonstrates:
1. Generating sample logs
2. Scrubbing PII from logs
3. Benchmarking Rust vs Python performance
"""

import sys
from pathlib import Path
import sentinel_rs


def demo_text_scrubbing():
    """Demonstrate in-memory text scrubbing."""
    print("=" * 70)
    print("DEMO 1: In-Memory Text Scrubbing")
    print("=" * 70)
    
    samples = [
        "User john.doe123@gmail.com logged in from 192.168.1.100",
        "Payment processed: Card 1234-5678-9012-3456, Amount: $99.99",
        "API request with token: Bearer abc123def456ghi789xyz",
        "Contact support at +1-555-123-4567 or support@company.com",
        "SSN verification: 123-45-6789 for user alice@example.org",
    ]
    
    # Define patterns for your use case
    rules = {
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b': '[EMAIL]',
        r'\b(?:\d{1,3}\.){3}\d{1,3}\b': '[IP]',
        r'\b(?:\d{4}[-\s]?){3}\d{4}\b': '[CREDIT_CARD]',
        r'\b\d{3}-\d{2}-\d{4}\b': '[SSN]',
        r'\+?1[-.]?\d{3}[-.]?\d{3}[-.]?\d{4}': '[PHONE]',
        r'Bearer\s+[A-Za-z0-9\-._~+/]+=*': 'Bearer [TOKEN]',
    }
    
    for i, text in enumerate(samples, 1):
        print(f"\n{i}. Original:")
        print(f"   {text}")
        scrubbed = sentinel_rs.scrub_text(text, rules)
        print(f"   Scrubbed:")
        print(f"   {scrubbed}")
    
    print()


def demo_file_scrubbing():
    """Demonstrate file-based scrubbing."""
    print("=" * 70)
    print("DEMO 2: File-Based Scrubbing")
    print("=" * 70)
    
    # Create a small test file
    test_file = Path("demo_input.log")
    scrubbed_file = Path("demo_output.log")
    
    print(f"\nCreating test log file: {test_file}")
    
    test_logs = [
        "[2024-01-01 10:00:00] INFO: User alice@example.com logged in from 192.168.1.100",
        "[2024-01-01 10:01:00] INFO: User bob@company.org logged in from 10.0.0.50",
        "[2024-01-01 10:02:00] WARN: Failed login attempt for charlie@test.net from 203.0.113.42",
        "[2024-01-01 10:03:00] INFO: Payment processed for card 4532-1234-5678-9010",
        "[2024-01-01 10:04:00] DEBUG: API request from 172.16.0.1",
        "[2024-01-01 10:05:00] ERROR: Database connection failed from 192.168.1.200",
        "[2024-01-01 10:06:00] INFO: User verification: SSN 987-65-4321 for user@domain.com",
        "[2024-01-01 10:07:00] INFO: OAuth token: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",
    ]
    
    with open(test_file, 'w') as f:
        f.write('\n'.join(test_logs) + '\n')
    
    rules = {
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b': '[EMAIL]',
        r'\b(?:\d{1,3}\.){3}\d{1,3}\b': '[IP]',
        r'\b(?:\d{4}[-\s]?){3}\d{4}\b': '[CREDIT_CARD]',
        r'\b\d{3}-\d{2}-\d{4}\b': '[SSN]',
        r'Bearer\s+[A-Za-z0-9\-._~+/]+=*': 'Bearer [TOKEN]',
    }
    
    print(f"Scrubbing logs...")
    lines_processed = sentinel_rs.scrub_logs_parallel(
        str(test_file),
        str(scrubbed_file),
        rules
    )
    
    print(f"✓ Processed {lines_processed} lines")
    print(f"✓ Output written to: {scrubbed_file}")
    
    # Show comparison
    print(f"\n--- Original (first 3 lines) ---")
    with open(test_file) as f:
        for i, line in enumerate(f, 1):
            if i > 3:
                break
            print(f"{i}. {line.rstrip()}")
    
    print(f"\n--- Scrubbed (first 3 lines) ---")
    with open(scrubbed_file) as f:
        for i, line in enumerate(f, 1):
            if i > 3:
                break
            print(f"{i}. {line.rstrip()}")
    
    # Cleanup
    test_file.unlink()
    scrubbed_file.unlink()
    print(f"\n✓ Cleanup complete\n")


def demo_benchmark():
    """Demonstrate performance benchmarking."""
    print("=" * 70)
    print("DEMO 3: Performance Benchmarking (Rust vs Python)")
    print("=" * 70)
    
    test_file = Path("benchmark_test.log")
    
    # Generate a test file with 10,000 lines
    print(f"\nGenerating test file with 10,000 lines...")
    
    import random
    log_templates = [
        lambda i: f"[2024-01-01 10:00:{i%60:02d}] INFO: User user{i}@example.com logged in from 192.168.{i%256}.{i%256}",
        lambda i: f"[2024-01-01 10:00:{i%60:02d}] WARN: Failed login for test{i}@domain.org from 10.{i%256}.{i%256}.{i%256}",
        lambda i: f"[2024-01-01 10:00:{i%60:02d}] INFO: Payment card {1000+i%9000}-{1000+i%9000}-{1000+i%9000}-{1000+i%9000}",
        lambda i: f"[2024-01-01 10:00:{i%60:02d}] DEBUG: API key check: {''.join(chr(65 + (i*j)%26) for j in range(32))}",
    ]
    
    with open(test_file, 'w') as f:
        for i in range(10000):
            template = random.choice(log_templates)
            f.write(template(i) + '\n')
    
    print(f"✓ Test file created: {test_file} ({test_file.stat().st_size / 1024:.1f} KB)")
    
    # Run benchmark
    print(f"\nRunning benchmark...")
    print("(This compares parallel Rust implementation vs single-threaded Python)\n")
    
    rules = {
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b': '[EMAIL]',
        r'\b(?:\d{1,3}\.){3}\d{1,3}\b': '[IP]',
    }
    benchmark = sentinel_rs.Benchmark(rules)
    results = benchmark.run(str(test_file))
    
    # Cleanup
    test_file.unlink()
    Path(str(test_file) + '.rust.scrubbed').unlink(missing_ok=True)
    Path(str(test_file) + '.python.scrubbed').unlink(missing_ok=True)
    print(f"\n✓ Cleanup complete\n")


def demo_custom_rules():
    """Demonstrate custom rule definition."""
    print("=" * 70)
    print("DEMO 4: Custom PII Detection Rules")
    print("=" * 70)
    
    # Define custom rules for a specific use case
    custom_rules = {
        # Match employee IDs (format: EMP-12345)
        r'\bEMP-\d{5}\b': '[EMPLOYEE_ID]',
        
        # Match project codes (format: PRJ-ABC-123)
        r'\bPRJ-[A-Z]{3}-\d{3}\b': '[PROJECT_CODE]',
        
        # Match internal server IPs (10.x.x.x)
        r'\b10\.\d{1,3}\.\d{1,3}\.\d{1,3}\b': '[INTERNAL_IP]',
        
        # Still mask emails
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b': '[EMAIL]',
    }
    
    test_logs = [
        "Employee EMP-12345 accessed server 10.20.30.40",
        "Project PRJ-ABC-123 was assigned to alice@company.com",
        "EMP-67890 sent email from 10.50.60.70 to bob@partner.org",
        "Meeting notes for PRJ-XYZ-999 shared with team@company.com",
    ]
    
    print("\nCustom Rules:")
    for pattern, replacement in custom_rules.items():
        print(f"  {pattern[:50]:50} -> {replacement}")
    
    print("\nScrubbing with custom rules:\n")
    for i, log in enumerate(test_logs, 1):
        print(f"{i}. Original:")
        print(f"   {log}")
        scrubbed = sentinel_rs.scrub_text(log, custom_rules)
        print(f"   Scrubbed:")
        print(f"   {scrubbed}")
        print()


def main():
    """Run all demos."""
    print("\n" + "=" * 70)
    print("  SENTINEL-RS: High-Performance Log Anonymization Demo")
    print("=" * 70)
    print()
    
    try:
        demo_text_scrubbing()
        demo_file_scrubbing()
        demo_benchmark()
        demo_custom_rules()
        
        print("=" * 70)
        print("  All demos completed successfully! ✓")
        print("=" * 70)
        print()
        print("Next steps:")
        print("  1. Generate larger test files: python scripts/generate_logs.py")
        print("  2. Run tests: pytest tests/test_basic.py -v")
        print("  3. Check out the README.md for more examples")
        print()
        
    except ImportError as e:
        print(f"\n❌ Error: {e}")
        print("\nPlease build the package first:")
        print("  maturin develop --release")
        print()
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
