#!/usr/bin/env python3
"""
Comprehensive benchmark suite for sentinel-rs.

Compares Rust vs Python performance across different:
- File sizes (10K to 10M lines)
- Pattern complexities (simple to complex regex)
- Number of patterns

Generates performance graphs and summary statistics.
"""

import sys
import os
import time
import tempfile
from pathlib import Path
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import sentinel_rs

try:
    import matplotlib.pyplot as plt
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    print("⚠️  matplotlib not found. Install with: pip install matplotlib")
    print("   Continuing without graphs...\n")


class BenchmarkSuite:
    """Comprehensive benchmark suite for sentinel-rs."""
    
    def __init__(self, output_dir="benchmarks/results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.results = []
        
    def generate_test_data(self, num_lines, output_path):
        """Generate test log data."""
        print(f"  Generating {num_lines:,} lines of test data...")
        
        log_templates = [
            lambda i: f"[2024-01-{(i%28)+1:02d} 10:{i%60:02d}:{i%60:02d}] INFO: User user{i}@example.com logged in from 192.168.{i%256}.{i%256}",
            lambda i: f"[2024-01-{(i%28)+1:02d} 10:{i%60:02d}:{i%60:02d}] ERROR: Failed payment for card {1000+i%9000}-{1000+i%9000}-{1000+i%9000}-{1000+i%9000}",
            lambda i: f"[2024-01-{(i%28)+1:02d} 10:{i%60:02d}:{i%60:02d}] DEBUG: API request from 10.{i%256}.{i%256}.{i%256} token=KEY{i:08d}",
            lambda i: f"[2024-01-{(i%28)+1:02d} 10:{i%60:02d}:{i%60:02d}] WARN: SSN verification {100+i%900}-{10+i%90}-{1000+i%9000} for user{i}@test.com",
        ]
        
        with open(output_path, 'w') as f:
            for i in range(num_lines):
                template = log_templates[i % len(log_templates)]
                f.write(template(i) + '\n')
    
    def benchmark_file_size(self, sizes=[1000, 5000, 10000, 50000, 100000, 500000, 1000000]):
        """Benchmark different file sizes."""
        print("\n" + "="*70)
        print("BENCHMARK 1: File Size Scaling")
        print("="*70)
        
        rules = {
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b': '[EMAIL]',
            r'\b(?:\d{1,3}\.){3}\d{1,3}\b': '[IP]',
            r'\b(?:\d{4}[-\s]?){3}\d{4}\b': '[CARD]',
            r'\b\d{3}-\d{2}-\d{4}\b': '[SSN]',
        }
        
        results = []
        
        with tempfile.TemporaryDirectory() as tmpdir:
            for size in sizes:
                print(f"\nTesting {size:,} lines...")
                
                input_file = Path(tmpdir) / f"input_{size}.log"
                rust_output = Path(tmpdir) / f"rust_{size}.log"
                python_output = Path(tmpdir) / f"python_{size}.log"
                
                # Generate data
                self.generate_test_data(size, input_file)
                file_size_mb = input_file.stat().st_size / (1024 * 1024)
                
                # Benchmark Rust
                benchmark = sentinel_rs.Benchmark(rules)
                rust_time, rust_lines = benchmark.scrub_logs_rust(str(input_file), str(rust_output))
                print(f"  Rust:   {rust_time:.3f}s ({rust_lines/rust_time:,.0f} lines/sec)")
                
                # Benchmark Python
                python_time, python_lines = benchmark.scrub_logs_python(str(input_file), str(python_output))
                print(f"  Python: {python_time:.3f}s ({python_lines/python_time:,.0f} lines/sec)")
                
                speedup = python_time / rust_time if rust_time > 0 else 0
                print(f"  Speedup: {speedup:.2f}x")
                
                results.append({
                    'lines': size,
                    'file_size_mb': file_size_mb,
                    'rust_time': rust_time,
                    'python_time': python_time,
                    'speedup': speedup,
                    'rust_throughput': rust_lines / rust_time if rust_time > 0 else 0,
                    'python_throughput': python_lines / python_time if python_time > 0 else 0,
                })
        
        self.results.append({
            'benchmark': 'file_size_scaling',
            'results': results
        })
        
        return results
    
    def benchmark_pattern_complexity(self):
        """Benchmark different pattern complexities."""
        print("\n" + "="*70)
        print("BENCHMARK 2: Pattern Complexity")
        print("="*70)
        
        pattern_sets = {
            'Simple (1 pattern)': {
                r'@\S+': '@[HIDDEN]',
            },
            'Medium (5 patterns)': {
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b': '[EMAIL]',
                r'\b(?:\d{1,3}\.){3}\d{1,3}\b': '[IP]',
                r'\b(?:\d{4}[-\s]?){3}\d{4}\b': '[CARD]',
                r'\b\d{3}-\d{2}-\d{4}\b': '[SSN]',
                r'KEY\d+': '[API_KEY]',
            },
            'Complex (10 patterns)': {
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b': '[EMAIL]',
                r'\b(?:\d{1,3}\.){3}\d{1,3}\b': '[IP]',
                r'\b(?:\d{4}[-\s]?){3}\d{4}\b': '[CARD]',
                r'\b\d{3}-\d{2}-\d{4}\b': '[SSN]',
                r'KEY\d+': '[API_KEY]',
                r'Bearer\s+[A-Za-z0-9\-._~+/]+=*': 'Bearer [TOKEN]',
                r'password[=:]\S+': 'password=[REDACTED]',
                r'token[=:]\S+': 'token=[REDACTED]',
                r'\b[A-Z]{2,}\d{6,}\b': '[ID]',
                r'\$\d+\.\d{2}': '$[AMOUNT]',
            }
        }
        
        results = []
        test_size = 100000
        
        with tempfile.TemporaryDirectory() as tmpdir:
            input_file = Path(tmpdir) / "input.log"
            self.generate_test_data(test_size, input_file)
            
            for name, rules in pattern_sets.items():
                print(f"\nTesting: {name}")
                
                rust_output = Path(tmpdir) / "rust_out.log"
                python_output = Path(tmpdir) / "python_out.log"
                
                benchmark = sentinel_rs.Benchmark(rules)
                rust_time, _ = benchmark.scrub_logs_rust(str(input_file), str(rust_output))
                python_time, _ = benchmark.scrub_logs_python(str(input_file), str(python_output))
                
                speedup = python_time / rust_time if rust_time > 0 else 0
                
                print(f"  Rust:   {rust_time:.3f}s")
                print(f"  Python: {python_time:.3f}s")
                print(f"  Speedup: {speedup:.2f}x")
                
                results.append({
                    'name': name,
                    'num_patterns': len(rules),
                    'rust_time': rust_time,
                    'python_time': python_time,
                    'speedup': speedup,
                })
        
        self.results.append({
            'benchmark': 'pattern_complexity',
            'results': results
        })
        
        return results
    
    def generate_graphs(self):
        """Generate performance graphs."""
        if not HAS_MATPLOTLIB:
            print("\n⚠️  Skipping graph generation (matplotlib not available)")
            return
        
        print("\n" + "="*70)
        print("GENERATING GRAPHS")
        print("="*70)
        
        # Graph 1: File Size Scaling
        file_size_data = next((r for r in self.results if r['benchmark'] == 'file_size_scaling'), None)
        if file_size_data:
            self._generate_file_size_graph(file_size_data['results'])
        
        # Graph 2: Pattern Complexity
        complexity_data = next((r for r in self.results if r['benchmark'] == 'pattern_complexity'), None)
        if complexity_data:
            self._generate_complexity_graph(complexity_data['results'])
        
        # Graph 3: Combined comparison
        if file_size_data:
            self._generate_comparison_graph(file_size_data['results'])
    
    def _generate_file_size_graph(self, results):
        """Generate file size scaling graph."""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
        
        lines = [r['lines'] for r in results]
        rust_times = [r['rust_time'] for r in results]
        python_times = [r['python_time'] for r in results]
        speedups = [r['speedup'] for r in results]
        
        # Graph 1: Execution time
        ax1.plot(lines, rust_times, 'o-', label='Rust', color='#CE422B', linewidth=2, markersize=8)
        ax1.plot(lines, python_times, 's-', label='Python', color='#3776AB', linewidth=2, markersize=8)
        ax1.set_xlabel('Number of Lines', fontsize=12, fontweight='bold')
        ax1.set_ylabel('Time (seconds)', fontsize=12, fontweight='bold')
        ax1.set_title('Execution Time vs File Size', fontsize=14, fontweight='bold')
        ax1.legend(fontsize=11)
        ax1.grid(True, alpha=0.3)
        ax1.set_xscale('log')
        ax1.set_yscale('log')
        
        # Graph 2: Speedup
        ax2.plot(lines, speedups, 'o-', color='#10B981', linewidth=2, markersize=8)
        ax2.axhline(y=1, color='gray', linestyle='--', alpha=0.5)
        ax2.set_xlabel('Number of Lines', fontsize=12, fontweight='bold')
        ax2.set_ylabel('Speedup (x times faster)', fontsize=12, fontweight='bold')
        ax2.set_title('Rust Speedup over Python', fontsize=14, fontweight='bold')
        ax2.grid(True, alpha=0.3)
        ax2.set_xscale('log')
        
        # Add speedup annotations
        for i, (line, speedup) in enumerate(zip(lines, speedups)):
            if i % 2 == 0:  # Annotate every other point
                ax2.annotate(f'{speedup:.1f}x', 
                           xy=(line, speedup), 
                           xytext=(10, 10),
                           textcoords='offset points',
                           fontsize=9,
                           bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.7))
        
        plt.tight_layout()
        output_path = self.output_dir / 'performance_scaling.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"  ✓ Saved: {output_path}")
        plt.close()
    
    def _generate_complexity_graph(self, results):
        """Generate pattern complexity graph."""
        fig, ax = plt.subplots(figsize=(10, 6))
        
        names = [r['name'] for r in results]
        rust_times = [r['rust_time'] for r in results]
        python_times = [r['python_time'] for r in results]
        
        x = range(len(names))
        width = 0.35
        
        bars1 = ax.bar([i - width/2 for i in x], rust_times, width, label='Rust', color='#CE422B')
        bars2 = ax.bar([i + width/2 for i in x], python_times, width, label='Python', color='#3776AB')
        
        ax.set_xlabel('Pattern Complexity', fontsize=12, fontweight='bold')
        ax.set_ylabel('Time (seconds)', fontsize=12, fontweight='bold')
        ax.set_title('Performance vs Pattern Complexity (100K lines)', fontsize=14, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(names)
        ax.legend(fontsize=11)
        ax.grid(True, alpha=0.3, axis='y')
        
        # Add value labels on bars
        for bars in [bars1, bars2]:
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{height:.2f}s',
                       ha='center', va='bottom', fontsize=9)
        
        plt.tight_layout()
        output_path = self.output_dir / 'pattern_complexity.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"  ✓ Saved: {output_path}")
        plt.close()
    
    def _generate_comparison_graph(self, results):
        """Generate throughput comparison graph."""
        fig, ax = plt.subplots(figsize=(10, 6))
        
        lines = [r['lines'] for r in results]
        rust_throughput = [r['rust_throughput'] for r in results]
        python_throughput = [r['python_throughput'] for r in results]
        
        ax.plot(lines, rust_throughput, 'o-', label='Rust', color='#CE422B', linewidth=2, markersize=8)
        ax.plot(lines, python_throughput, 's-', label='Python', color='#3776AB', linewidth=2, markersize=8)
        
        ax.set_xlabel('Number of Lines', fontsize=12, fontweight='bold')
        ax.set_ylabel('Throughput (lines/second)', fontsize=12, fontweight='bold')
        ax.set_title('Processing Throughput Comparison', fontsize=14, fontweight='bold')
        ax.legend(fontsize=11)
        ax.grid(True, alpha=0.3)
        ax.set_xscale('log')
        
        # Format y-axis with comma separator
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{int(x):,}'))
        
        plt.tight_layout()
        output_path = self.output_dir / 'throughput_comparison.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"  ✓ Saved: {output_path}")
        plt.close()
    
    def save_json_results(self):
        """Save results to JSON."""
        output_path = self.output_dir / 'benchmark_results.json'
        with open(output_path, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"\n✓ Results saved to: {output_path}")
    
    def print_summary(self):
        """Print summary statistics."""
        print("\n" + "="*70)
        print("BENCHMARK SUMMARY")
        print("="*70)
        
        file_size_data = next((r for r in self.results if r['benchmark'] == 'file_size_scaling'), None)
        if file_size_data:
            results = file_size_data['results']
            avg_speedup = sum(r['speedup'] for r in results) / len(results)
            max_speedup = max(r['speedup'] for r in results)
            max_throughput = max(r['rust_throughput'] for r in results)
            
            print(f"\nFile Size Scaling:")
            print(f"  Average Speedup:        {avg_speedup:.2f}x")
            print(f"  Maximum Speedup:        {max_speedup:.2f}x")
            print(f"  Peak Throughput (Rust): {max_throughput:,.0f} lines/sec")
            
            # Show detailed table
            print(f"\n  {'Lines':<12} {'File Size':<12} {'Rust Time':<12} {'Python Time':<12} {'Speedup':<10}")
            print(f"  {'-'*12} {'-'*12} {'-'*12} {'-'*12} {'-'*10}")
            for r in results:
                print(f"  {r['lines']:<12,} {r['file_size_mb']:<11.2f}MB {r['rust_time']:<11.3f}s {r['python_time']:<11.3f}s {r['speedup']:<9.2f}x")


def main():
    """Run comprehensive benchmarks."""
    print("="*70)
    print("SENTINEL-RS COMPREHENSIVE BENCHMARK SUITE")
    print("="*70)
    print("\nThis will take several minutes...")
    print("Testing file sizes from 1K to 1M lines")
    print()
    
    suite = BenchmarkSuite()
    
    # Run benchmarks
    suite.benchmark_file_size()
    suite.benchmark_pattern_complexity()
    
    # Generate visualizations
    suite.generate_graphs()
    
    # Save results
    suite.save_json_results()
    
    # Print summary
    suite.print_summary()
    
    print("\n" + "="*70)
    print("✅ BENCHMARKING COMPLETE!")
    print("="*70)
    print(f"\nResults saved in: benchmarks/results/")
    print("  - performance_scaling.png")
    print("  - pattern_complexity.png")
    print("  - throughput_comparison.png")
    print("  - benchmark_results.json")
    print()


if __name__ == '__main__':
    main()
