r"""
Sentinel-RS: High-Performance Pattern Matching Engine

A Rust-powered Python library for fast regex-based text transformation.
Process millions of log lines with parallel processing and zero GIL overhead.

Define your own regex patterns for any use case:
- Log anonymization (PII scrubbing)
- Data sanitization
- Format conversion
- Custom text transformations

The engine is completely pattern-agnostic - you define what to match!
"""

from .sentinel_rs import scrub_logs_parallel, scrub_logs_mmap, scrub_text
import re
import time
from pathlib import Path
from typing import Dict, Tuple


__version__ = "0.1.0"
__all__ = ["scrub_logs_parallel", "scrub_logs_mmap", "scrub_text", "Benchmark"]


class Benchmark:
    """
    Benchmark class to compare Rust vs Python implementations.
    
    This class provides methods to benchmark the performance difference
    between the Rust-powered implementation and a pure Python implementation
    using the standard library's re module.
    
    Example:
        >>> rules = {r'email@\S+': '[EMAIL]', r'\d+\.\d+\.\d+\.\d+': '[IP]'}
        >>> benchmark = Benchmark(rules)
        >>> results = benchmark.run('input.log')
        >>> print(f"Rust: {results['rust_time']:.3f}s, Python: {results['python_time']:.3f}s")
        >>> print(f"Speedup: {results['speedup']:.2f}x")
    """
    
    def __init__(self, rules: Dict[str, str]):
        """
        Initialize the benchmark with your regex patterns.
        
        Args:
            rules: Dictionary mapping regex patterns to replacement strings.
        """
        self.rules = rules
        
    def scrub_logs_python(self, input_path: str, output_path: str) -> Tuple[float, int]:
        """
        Pure Python implementation of log scrubbing (single-threaded).
        
        Args:
            input_path: Path to input log file
            output_path: Path to output scrubbed log file
            
        Returns:
            Tuple of (execution_time, lines_processed)
        """
        # Compile regex patterns
        compiled_rules = [(re.compile(pattern), replacement) 
                         for pattern, replacement in self.rules.items()]
        
        start_time = time.perf_counter()
        
        lines_processed = 0
        with open(input_path, 'r', encoding='utf-8', errors='ignore') as infile, \
             open(output_path, 'w', encoding='utf-8') as outfile:
            
            for line in infile:
                scrubbed = line
                for pattern, replacement in compiled_rules:
                    scrubbed = pattern.sub(replacement, scrubbed)
                outfile.write(scrubbed)
                lines_processed += 1
        
        elapsed = time.perf_counter() - start_time
        return elapsed, lines_processed
    
    def scrub_logs_rust(self, input_path: str, output_path: str, use_mmap: bool = False) -> Tuple[float, int]:
        """
        Rust implementation of log scrubbing (multi-threaded).
        
        Args:
            input_path: Path to input log file
            output_path: Path to output scrubbed log file
            use_mmap: If True, uses memory-mapped file for better performance on large files
            
        Returns:
            Tuple of (execution_time, lines_processed)
        """
        start_time = time.perf_counter()
        
        if use_mmap:
            lines_processed = scrub_logs_mmap(input_path, output_path, self.rules)
        else:
            lines_processed = scrub_logs_parallel(input_path, output_path, self.rules)
        
        elapsed = time.perf_counter() - start_time
        return elapsed, lines_processed
    
    def run(
        self, 
        input_path: str, 
        output_rust_path: str = None, 
        output_python_path: str = None,
        use_mmap: bool = False
    ) -> Dict[str, float]:
        """
        Run both implementations and compare performance.
        
        Args:
            input_path: Path to input log file
            output_rust_path: Path for Rust output (default: input_path + '.rust.scrubbed')
            output_python_path: Path for Python output (default: input_path + '.python.scrubbed')
            use_mmap: If True, uses memory-mapped file for Rust implementation
            
        Returns:
            Dictionary with benchmark results including times and speedup factor
        """
        input_path = Path(input_path)
        
        if output_rust_path is None:
            output_rust_path = str(input_path.with_suffix(input_path.suffix + '.rust.scrubbed'))
        if output_python_path is None:
            output_python_path = str(input_path.with_suffix(input_path.suffix + '.python.scrubbed'))
        
        print("Running Rust implementation...")
        rust_time, rust_lines = self.scrub_logs_rust(str(input_path), output_rust_path, use_mmap)
        print(f"  Completed: {rust_lines:,} lines in {rust_time:.3f}s ({rust_lines/rust_time:,.0f} lines/sec)")
        
        print("\nRunning Python implementation...")
        python_time, python_lines = self.scrub_logs_python(str(input_path), output_python_path)
        print(f"  Completed: {python_lines:,} lines in {python_time:.3f}s ({python_lines/python_time:,.0f} lines/sec)")
        
        speedup = python_time / rust_time if rust_time > 0 else 0
        
        print(f"\n{'='*60}")
        print(f"RESULTS:")
        print(f"  Rust:   {rust_time:.3f}s")
        print(f"  Python: {python_time:.3f}s")
        print(f"  Speedup: {speedup:.2f}x faster with Rust")
        print(f"{'='*60}")
        
        return {
            'rust_time': rust_time,
            'python_time': python_time,
            'speedup': speedup,
            'rust_lines': rust_lines,
            'python_lines': python_lines,
            'rust_throughput': rust_lines / rust_time if rust_time > 0 else 0,
            'python_throughput': python_lines / python_time if python_time > 0 else 0,
        }


