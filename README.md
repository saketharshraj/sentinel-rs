# Sentinel-RS 🦀

**High-performance pattern matching engine for Python, powered by Rust.**

Process millions of log lines per second with parallel regex matching. Perfect for log anonymization, data sanitization, and any large-scale text transformation task.

[![PyPI](https://img.shields.io/pypi/v/sentinel-rs.svg)](https://pypi.org/project/sentinel-rs/)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Why Sentinel-RS?

✅ **10-50x faster** than pure Python regex processing  
✅ **True parallelism** - uses all CPU cores, bypasses Python's GIL  
✅ **Pattern agnostic** - define any regex patterns you need  
✅ **Memory efficient** - buffered I/O and memory-mapped file support  
✅ **Zero overhead** - native Rust speed with Pythonic API  

## Installation

```bash
pip install sentinel-rs
```

## Quick Start

### Basic Usage

```python
import sentinel_rs

# Define your patterns
rules = {
    r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b': '[EMAIL]',
    r'\b(?:\d{1,3}\.){3}\d{1,3}\b': '[IP]',
    r'password=\S+': 'password=***',
}

# Process a single string
text = "User admin@example.com logged in from 192.168.1.1"
result = sentinel_rs.scrub_text(text, rules)
print(result)
# Output: "User [EMAIL] logged in from [IP]"

# Process a file (uses all CPU cores automatically)
lines = sentinel_rs.scrub_logs_parallel(
    'application.log',
    'application_scrubbed.log',
    rules
)
print(f"Processed {lines:,} lines")
```

### For Large Files (> 1GB)

```python
import sentinel_rs

# Use memory-mapped I/O for better performance on huge files
lines = sentinel_rs.scrub_logs_mmap(
    'huge_logfile.log',
    'huge_logfile_scrubbed.log',
    rules
)
```

## Use Cases

### Log Anonymization (PII Scrubbing)

```python
import sentinel_rs

# Remove personally identifiable information from logs
pii_rules = {
    r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b': '[EMAIL]',
    r'\b(?:\d{1,3}\.){3}\d{1,3}\b': '[IP]',
    r'\b(?:\d{4}[-\s]?){3}\d{4}\b': '[CREDIT_CARD]',
    r'\b\d{3}-\d{2}-\d{4}\b': '[SSN]',
    r'\+?1[-.]?\d{3}[-.]?\d{3}[-.]?\d{4}': '[PHONE]',
}

sentinel_rs.scrub_logs_parallel('logs/app.log', 'logs/app_clean.log', pii_rules)
```

### Custom Business Data Redaction

```python
import sentinel_rs

# Mask your internal identifiers and codes
custom_rules = {
    r'EMPLOYEE-\d{6}': '[EMP_ID]',
    r'PROJECT-[A-Z]{3}-\d{4}': '[PROJECT]',
    r'INTERNAL-KEY-[A-Z0-9]{16}': '[SECRET]',
}

sentinel_rs.scrub_logs_parallel('internal.log', 'redacted.log', custom_rules)
```

### API Response Sanitization

```python
import sentinel_rs

# Remove sensitive data from API responses before logging
api_rules = {
    r'"api_key":\s*"[^"]+': '"api_key": "[REDACTED]',
    r'"token":\s*"[^"]+': '"token": "[REDACTED]',
    r'"password":\s*"[^"]+': '"password": "[REDACTED]',
}

clean_response = sentinel_rs.scrub_text(api_response, api_rules)
```

### Format Conversion

```python
import sentinel_rs

# Transform date formats, standardize patterns, etc.
conversion_rules = {
    r'\d{2}/\d{2}/\d{4}': '[DATE]',
    r'\$\d+\.\d{2}': '[AMOUNT]',
}

sentinel_rs.scrub_logs_parallel('raw.log', 'normalized.log', conversion_rules)
```

## API Reference

### Core Functions

#### `scrub_text(text: str, rules: dict) -> str`

Process a single string in memory.

**Parameters:**
- `text`: Input string to process
- `rules`: Dictionary mapping regex patterns to replacement strings

**Returns:** Transformed string

**Example:**
```python
result = sentinel_rs.scrub_text(
    "Contact: user@example.com",
    {r'\S+@\S+': '[EMAIL]'}
)
```

#### `scrub_logs_parallel(input_path: str, output_path: str, rules: dict) -> int`

Process a file using parallel execution across all CPU cores.

**Parameters:**
- `input_path`: Path to input file
- `output_path`: Path to output file
- `rules`: Dictionary mapping regex patterns to replacement strings

**Returns:** Number of lines processed

**Best for:** Files < 1GB, general use

#### `scrub_logs_mmap(input_path: str, output_path: str, rules: dict) -> int`

Process a file using memory-mapped I/O for maximum performance.

**Parameters:**
- `input_path`: Path to input file
- `output_path`: Path to output file
- `rules`: Dictionary mapping regex patterns to replacement strings

**Returns:** Number of lines processed

**Best for:** Files > 1GB, memory-constrained environments

### Benchmarking

```python
from sentinel_rs import Benchmark

rules = {r'@\S+': '@[HIDDEN]', r'\d+\.\d+\.\d+\.\d+': '[IP]'}
benchmark = Benchmark(rules)
results = benchmark.run('test.log')

print(f"Rust:   {results['rust_time']:.3f}s")
print(f"Python: {results['python_time']:.3f}s") 
print(f"Speedup: {results['speedup']:.2f}x")
```

## Performance

Typical performance on modern hardware (M1/Ryzen/Intel i7+):

| File Size | Lines | Pure Python | Sentinel-RS | Speedup |
|-----------|-------|-------------|-------------|---------|
| 10 MB     | 100K  | 2.5s        | 0.15s       | **16x** |
| 100 MB    | 1M    | 25s         | 1.2s        | **20x** |
| 1 GB      | 10M   | 250s        | 11s         | **22x** |

*Performance scales linearly with CPU core count*

## Pattern Examples

### Common PII Patterns

```python
# Email addresses
r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'

# IPv4 addresses  
r'\b(?:\d{1,3}\.){3}\d{1,3}\b'

# IPv6 addresses
r'\b(?:[A-Fa-f0-9]{1,4}:){7}[A-Fa-f0-9]{1,4}\b'

# Credit cards (basic)
r'\b(?:\d{4}[-\s]?){3}\d{4}\b'

# US Social Security Numbers
r'\b\d{3}-\d{2}-\d{4}\b'

# US Phone numbers
r'\+?1[-.]?\d{3}[-.]?\d{3}[-.]?\d{4}'

# API Keys (32+ alphanumeric)
r'\b[A-Za-z0-9]{32,}\b'

# AWS Access Keys
r'AKIA[0-9A-Z]{16}'

# Bearer tokens
r'Bearer\s+[A-Za-z0-9\-._~+/]+=*'

# JWT tokens
r'eyJ[A-Za-z0-9-_=]+\.eyJ[A-Za-z0-9-_=]+\.[A-Za-z0-9-_.+/=]+'
```

### URL Sanitization

```python
# Remove query parameters with sensitive keys
r'(https?://[^?]+)\?.*(?:token|key|password|secret)=[^&\s]+'

# Mask credentials in URLs
r'://[^:]+:[^@]+@'  # Replace with '://[CREDENTIALS]@'
```

## Demo & Testing

### Run the Demo

```bash
python demo.py
```

The demo showcases:
1. In-memory text scrubbing
2. File processing
3. Performance benchmarking (Rust vs Python)
4. Custom pattern examples

### Generate Test Data

```bash
# Generate 1 million diverse log lines
python scripts/generate_logs.py -n 1000000 -o test.log

# Generate smaller test file
python scripts/generate_logs.py -n 10000 -o small.log
```

### Run Tests

```bash
pytest tests/ -v
```

## How It Works

Sentinel-RS is built on three key technologies:

1. **PyO3** - Rust bindings for Python (zero-copy data transfer)
2. **Rayon** - Data parallelism library (automatic work distribution)
3. **Regex** - Rust's optimized regex engine

**Flow:**
```
Python defines patterns → PyO3 bridge → Rust compiles regex → 
Rayon parallelizes across cores → Process millions of lines → 
Return results to Python
```

The engine is **completely pattern-agnostic** - it doesn't know what PII is or what you're matching. You define all the logic in Python, and Rust provides the speed.

## Requirements

- Python 3.8+
- Any platform (Linux, macOS, Windows)
- Multi-core CPU recommended for maximum performance

## Development

### Build from Source

```bash
# Install Rust (if not already installed)
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Install maturin
pip install maturin

# Build in development mode
maturin develop

# Build for release (optimized)
maturin develop --release
```

### Project Structure

```
sentinel-rs/
├── src/lib.rs           # Rust core (pattern matching engine)
├── sentinel_rs/         # Python package
│   └── __init__.py      # Python wrapper & utilities
├── tests/               # Test suite
├── scripts/             # Utility scripts
└── demo.py             # Interactive demo
```

## Contributing

Contributions welcome! Areas for improvement:

- Additional optimization techniques
- Support for more file formats
- Better error messages
- Documentation improvements

## License

MIT License - see LICENSE file for details.

## Acknowledgments

Built with:
- [PyO3](https://github.com/PyO3/pyo3) - Rust-Python bindings
- [Maturin](https://github.com/PyO3/maturin) - Build tool
- [Rayon](https://github.com/rayon-rs/rayon) - Data parallelism
- [Regex](https://github.com/rust-lang/regex) - Rust regex engine

## Security Note

⚠️ **Important:** This library performs pattern matching based on the regex rules YOU provide. It's your responsibility to:

- Test patterns thoroughly before production use
- Ensure patterns match your specific data formats
- Validate that scrubbed data meets your compliance requirements
- Handle false positives/negatives appropriately

Always test with non-production data first!

---

**Made with ❤️ and 🦀 Rust**

For questions, issues, or feature requests, please open an issue on GitHub.
