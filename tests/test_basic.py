"""
Comprehensive tests for sentinel-rs log anonymization engine.

Tests cover:
- Basic PII scrubbing functionality
- File I/O operations
- Error handling
- Performance benchmarking
- Edge cases
"""

import pytest
import tempfile
from pathlib import Path
import sentinel_rs


class TestScrubText:
    """Tests for scrub_text function (in-memory string scrubbing)."""
    
    def test_scrub_email(self):
        """Test email address scrubbing."""
        text = "Contact us at support@example.com for help"
        rules = {r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b': '[EMAIL]'}
        result = sentinel_rs.scrub_text(text, rules)
        assert result == "Contact us at [EMAIL] for help"
    
    def test_scrub_ip(self):
        """Test IP address scrubbing."""
        text = "Connection from 192.168.1.100"
        rules = {r'\b(?:\d{1,3}\.){3}\d{1,3}\b': '[IP]'}
        result = sentinel_rs.scrub_text(text, rules)
        assert result == "Connection from [IP]"
    
    def test_scrub_credit_card(self):
        """Test credit card number scrubbing."""
        text = "Card: 1234-5678-9012-3456"
        rules = {r'\b(?:\d{4}[-\s]?){3}\d{4}\b': '[CREDIT_CARD]'}
        result = sentinel_rs.scrub_text(text, rules)
        assert result == "Card: [CREDIT_CARD]"
    
    def test_scrub_ssn(self):
        """Test SSN scrubbing."""
        text = "SSN: 123-45-6789"
        rules = {r'\b\d{3}-\d{2}-\d{4}\b': '[SSN]'}
        result = sentinel_rs.scrub_text(text, rules)
        assert result == "SSN: [SSN]"
    
    def test_scrub_phone(self):
        """Test phone number scrubbing."""
        text = "Call +1-555-123-4567 for support"
        rules = {r'\+?1[-.]?\d{3}[-.]?\d{3}[-.]?\d{4}': '[PHONE]'}
        result = sentinel_rs.scrub_text(text, rules)
        assert result == "Call [PHONE] for support"
    
    def test_multiple_patterns(self):
        """Test scrubbing multiple PII types in one string."""
        text = "User john@example.com logged in from 10.0.0.1 with card 1234-5678-9012-3456"
        rules = {
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b': '[EMAIL]',
            r'\b(?:\d{1,3}\.){3}\d{1,3}\b': '[IP]',
            r'\b(?:\d{4}[-\s]?){3}\d{4}\b': '[CREDIT_CARD]',
        }
        result = sentinel_rs.scrub_text(text, rules)
        assert '[EMAIL]' in result
        assert '[IP]' in result
        assert '[CREDIT_CARD]' in result
        assert 'john@example.com' not in result
        assert '10.0.0.1' not in result
        assert '1234-5678-9012-3456' not in result
    
    def test_no_pii(self):
        """Test that clean text remains unchanged."""
        text = "This is a clean log line with no PII"
        rules = {r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b': '[EMAIL]'}
        result = sentinel_rs.scrub_text(text, rules)
        assert result == text
    
    def test_empty_string(self):
        """Test empty string handling."""
        text = ""
        rules = {r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b': '[EMAIL]'}
        result = sentinel_rs.scrub_text(text, rules)
        assert result == ""
    
    def test_invalid_regex(self):
        """Test that invalid regex patterns raise appropriate errors."""
        text = "test@example.com"
        rules = {r'[invalid(regex': '[EMAIL]'}  # Invalid regex
        with pytest.raises(Exception):  # Should raise PyIOError
            sentinel_rs.scrub_text(text, rules)


class TestScrubLogsParallel:
    """Tests for scrub_logs_parallel function (file-based scrubbing)."""
    
    def test_basic_file_scrubbing(self):
        """Test basic file scrubbing functionality."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.log"
            output_path = Path(tmpdir) / "output.log"
            
            # Create test input file
            test_lines = [
                "User alice@example.com logged in\n",
                "Connection from 192.168.1.1\n",
                "Payment with card 1234-5678-9012-3456\n",
            ]
            input_path.write_text(''.join(test_lines))
            
            # Scrub the file
            rules = {
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b': '[EMAIL]',
                r'\b(?:\d{1,3}\.){3}\d{1,3}\b': '[IP]',
                r'\b(?:\d{4}[-\s]?){3}\d{4}\b': '[CREDIT_CARD]',
            }
            lines_processed = sentinel_rs.scrub_logs_parallel(
                str(input_path), str(output_path), rules
            )
            
            # Verify results
            assert lines_processed == 3
            assert output_path.exists()
            
            output_content = output_path.read_text()
            assert '[EMAIL]' in output_content
            assert '[IP]' in output_content
            assert '[CREDIT_CARD]' in output_content
            assert 'alice@example.com' not in output_content
            assert '192.168.1.1' not in output_content
            assert '1234-5678-9012-3456' not in output_content
    
    def test_large_file(self):
        """Test with a larger file (10k lines)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "large_input.log"
            output_path = Path(tmpdir) / "large_output.log"
            
            # Create larger test file
            with open(input_path, 'w') as f:
                for i in range(10000):
                    f.write(f"User user{i}@example.com logged in from 192.168.1.{i % 256}\n")
            
            rules = {
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b': '[EMAIL]',
                r'\b(?:\d{1,3}\.){3}\d{1,3}\b': '[IP]',
            }
            
            lines_processed = sentinel_rs.scrub_logs_parallel(
                str(input_path), str(output_path), rules
            )
            
            assert lines_processed == 10000
            assert output_path.exists()
            
            # Verify no emails in output
            output_content = output_path.read_text()
            assert '@example.com' not in output_content
            assert '[EMAIL]' in output_content
            assert '[IP]' in output_content
    
    def test_empty_file(self):
        """Test with an empty file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "empty.log"
            output_path = Path(tmpdir) / "empty_output.log"
            
            input_path.write_text('')
            
            rules = {r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b': '[EMAIL]'}
            lines_processed = sentinel_rs.scrub_logs_parallel(
                str(input_path), str(output_path), rules
            )
            
            assert lines_processed == 0
            assert output_path.exists()
    
    def test_nonexistent_input(self):
        """Test error handling for nonexistent input file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "nonexistent.log"
            output_path = Path(tmpdir) / "output.log"
            
            rules = {r'test': '[TEST]'}
            
            with pytest.raises(Exception):  # Should raise PyIOError
                sentinel_rs.scrub_logs_parallel(str(input_path), str(output_path), rules)
    
    def test_comprehensive_rules(self):
        """Test with comprehensive set of patterns."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.log"
            output_path = Path(tmpdir) / "output.log"
            
            test_content = """
User: alice@example.com
IP: 192.168.1.1
Card: 1234-5678-9012-3456
SSN: 123-45-6789
            """.strip()
            
            input_path.write_text(test_content)
            
            rules = {
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b': '[EMAIL]',
                r'\b(?:\d{1,3}\.){3}\d{1,3}\b': '[IP]',
                r'\b(?:\d{4}[-\s]?){3}\d{4}\b': '[CREDIT_CARD]',
                r'\b\d{3}-\d{2}-\d{4}\b': '[SSN]',
            }
            
            lines_processed = sentinel_rs.scrub_logs_parallel(
                str(input_path), str(output_path), rules
            )
            
            assert lines_processed > 0
            output_content = output_path.read_text()
            
            # Verify PII is scrubbed
            assert 'alice@example.com' not in output_content
            assert '[EMAIL]' in output_content
            assert '[IP]' in output_content
            assert '[CREDIT_CARD]' in output_content
            assert '[SSN]' in output_content


class TestScrubLogsMmap:
    """Tests for scrub_logs_mmap function (memory-mapped file scrubbing)."""
    
    def test_mmap_basic(self):
        """Test basic memory-mapped file scrubbing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.log"
            output_path = Path(tmpdir) / "output.log"
            
            test_lines = [
                "User bob@example.com logged in\n",
                "Connection from 10.0.0.1\n",
            ]
            input_path.write_text(''.join(test_lines))
            
            rules = {
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b': '[EMAIL]',
                r'\b(?:\d{1,3}\.){3}\d{1,3}\b': '[IP]',
            }
            
            lines_processed = sentinel_rs.scrub_logs_mmap(
                str(input_path), str(output_path), rules
            )
            
            assert lines_processed == 2
            output_content = output_path.read_text()
            assert '[EMAIL]' in output_content
            assert '[IP]' in output_content
            assert 'bob@example.com' not in output_content


class TestBenchmark:
    """Tests for the Benchmark class."""
    
    def test_benchmark_initialization(self):
        """Test Benchmark class initialization."""
        rules = {r'test': '[REPLACED]'}
        benchmark = sentinel_rs.Benchmark(rules)
        assert benchmark.rules is not None
        assert len(benchmark.rules) > 0
    
    def test_benchmark_with_custom_rules(self):
        """Test Benchmark with custom rules."""
        custom_rules = {r'test': '[REPLACED]'}
        benchmark = sentinel_rs.Benchmark(rules=custom_rules)
        assert benchmark.rules == custom_rules
    
    def test_rust_implementation(self):
        """Test Rust implementation through Benchmark."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "test.log"
            output_path = Path(tmpdir) / "output.log"
            
            # Create small test file
            test_content = "\n".join([
                f"User user{i}@test.com from 10.0.0.{i}"
                for i in range(100)
            ])
            input_path.write_text(test_content)
            
            rules = {
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b': '[EMAIL]',
                r'\b(?:\d{1,3}\.){3}\d{1,3}\b': '[IP]',
            }
            benchmark = sentinel_rs.Benchmark(rules)
            rust_time, rust_lines = benchmark.scrub_logs_rust(
                str(input_path), str(output_path)
            )
            
            assert rust_lines == 100
            assert rust_time > 0
            assert output_path.exists()
    
    def test_python_implementation(self):
        """Test Python implementation through Benchmark."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "test.log"
            output_path = Path(tmpdir) / "output.log"
            
            # Create small test file
            test_content = "\n".join([
                f"User user{i}@test.com from 10.0.0.{i}"
                for i in range(100)
            ])
            input_path.write_text(test_content)
            
            rules = {
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b': '[EMAIL]',
                r'\b(?:\d{1,3}\.){3}\d{1,3}\b': '[IP]',
            }
            benchmark = sentinel_rs.Benchmark(rules)
            python_time, python_lines = benchmark.scrub_logs_python(
                str(input_path), str(output_path)
            )
            
            assert python_lines == 100
            assert python_time > 0
            assert output_path.exists()
    
    def test_benchmark_run(self):
        """Test full benchmark comparison."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "test.log"
            
            # Create test file
            test_content = "\n".join([
                f"[2024-01-01 12:00:00] User user{i}@test.com logged in from 192.168.1.{i % 256}"
                for i in range(1000)
            ])
            input_path.write_text(test_content)
            
            rules = {
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b': '[EMAIL]',
                r'\b(?:\d{1,3}\.){3}\d{1,3}\b': '[IP]',
            }
            benchmark = sentinel_rs.Benchmark(rules)
            results = benchmark.run(str(input_path))
            
            # Verify results structure
            assert 'rust_time' in results
            assert 'python_time' in results
            assert 'speedup' in results
            assert 'rust_lines' in results
            assert 'python_lines' in results
            
            # Verify both processed same number of lines
            assert results['rust_lines'] == results['python_lines']
            assert results['rust_lines'] == 1000
            
            # Rust should be faster (speedup > 1)
            # Note: For small files, the difference might be minimal
            assert results['speedup'] >= 0  # Just verify it's calculated




class TestEdgeCases:
    """Tests for edge cases and special scenarios."""
    
    def test_unicode_content(self):
        """Test with Unicode content."""
        text = "Usuario: user@example.com, IP: 192.168.1.1, 日本語テスト"
        rules = {
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b': '[EMAIL]',
            r'\b(?:\d{1,3}\.){3}\d{1,3}\b': '[IP]',
        }
        result = sentinel_rs.scrub_text(text, rules)
        assert '[EMAIL]' in result
        assert '[IP]' in result
        assert '日本語テスト' in result  # Should preserve non-PII Unicode
    
    def test_overlapping_patterns(self):
        """Test with potentially overlapping regex patterns."""
        text = "Contact: admin@192.168.1.1.com"
        rules = {
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b': '[EMAIL]',
            r'\b(?:\d{1,3}\.){3}\d{1,3}\b': '[IP]',
        }
        result = sentinel_rs.scrub_text(text, rules)
        # Email pattern should match first and replace the whole thing
        assert '[EMAIL]' in result
    
    def test_very_long_line(self):
        """Test with very long log lines."""
        # Create a line with 10k characters
        long_line = "A" * 5000 + " user@example.com " + "B" * 5000
        rules = {r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b': '[EMAIL]'}
        result = sentinel_rs.scrub_text(long_line, rules)
        assert '[EMAIL]' in result
        assert 'user@example.com' not in result
        assert len(result) < len(long_line)  # Should be shorter due to replacement


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
