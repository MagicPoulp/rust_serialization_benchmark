import re
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

def parse_benchmark_file(file_content):
    """
    Parse benchmark output and extract timing data
    """
    benchmarks = []
    
    # Fixed regular expression that properly captures benchmark names
    # This pattern looks for the benchmark name followed by timing data on the same line
    pattern = r'^([A-Za-z][\w\s\(\)\-]+?)\s+time:\s+\[([0-9.]+)\s*(\w+)\s+([0-9.]+)\s*(\w+)\s+([0-9.]+)\s*(\w+)\]'
    
    matches = re.findall(pattern, file_content, re.MULTILINE)
    
    for match in matches:
        name = match[0].strip()
        
        # Clean up the name - remove any trailing whitespace or unwanted text
        name = re.sub(r'\s+', ' ', name)  # Replace multiple spaces with single space
        
        min_time = float(match[1])
        min_unit = match[2]
        mean_time = float(match[3])
        mean_unit = match[4]
        max_time = float(match[5])
        max_unit = match[6]
        
        # Convert all times to nanoseconds for consistent comparison
        def convert_to_ns(time_val, unit):
            conversions = {
                'ps': 0.001,  # picoseconds to nanoseconds
                'ns': 1,      # nanoseconds
                'µs': 1000,   # microseconds to nanoseconds
                'ms': 1000000 # milliseconds to nanoseconds
            }
            return time_val * conversions.get(unit, 1)
        
        min_ns = convert_to_ns(min_time, min_unit)
        mean_ns = convert_to_ns(mean_time, mean_unit)
        max_ns = convert_to_ns(max_time, max_unit)
        
        benchmarks.append({
            'name': name,
            'min_ns': min_ns,
            'mean_ns': mean_ns,
            'max_ns': max_ns,
            'original_unit': mean_unit,
            'original_mean': mean_time
        })
    
    return benchmarks

def create_histograms(benchmarks):
    """
    Create histograms for benchmark data
    """
    # Create a DataFrame for easier manipulation
    df = pd.DataFrame(benchmarks)
    
    # Set up the plot
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('Rust Serialization Benchmark Results - Prost vs Rkyv Performance Comparison', fontsize=16, fontweight='bold')
    
    # Separate benchmarks by type
    prost_benchmarks = df[df['name'].str.contains('Prost', case=False)]
    rkyv_benchmarks = df[df['name'].str.contains('Rkyv', case=False)]
    
    # Colors for different libraries
    prost_color = '#FF6B6B'  # Red
    rkyv_color = '#4ECDC4'   # Teal
    
    # 1. Mean Times Comparison (Log Scale)
    ax1.bar(range(len(df)), df['mean_ns'], 
            color=[prost_color if 'Prost' in name else rkyv_color for name in df['name']])
    ax1.set_yscale('log')
    ax1.set_title('Mean Execution Times (Log Scale)', fontweight='bold')
    ax1.set_ylabel('Time (nanoseconds)')
    ax1.set_xticks(range(len(df)))
    ax1.set_xticklabels(df['name'], rotation=45, ha='right', fontsize=8)
    ax1.grid(True, alpha=0.3)
    
    # Add value labels on bars
    for i, (name, mean_ns, orig_mean, orig_unit) in enumerate(zip(df['name'], df['mean_ns'], df['original_mean'], df['original_unit'])):
        ax1.text(i, mean_ns, f'{orig_mean:.2f}{orig_unit}', 
                ha='center', va='bottom', rotation=90, fontsize=7)
    
    # 2. Error Bars Plot (Min, Mean, Max)
    x_pos = np.arange(len(df))
    ax2.errorbar(x_pos, df['mean_ns'], 
                yerr=[df['mean_ns'] - df['min_ns'], df['max_ns'] - df['mean_ns']],
                fmt='o', capsize=5, capthick=2, markersize=6,
                color='darkblue', ecolor='lightblue', alpha=0.8)
    ax2.set_yscale('log')
    ax2.set_title('Performance Range (Min-Mean-Max)', fontweight='bold')
    ax2.set_ylabel('Time (nanoseconds)')
    ax2.set_xticks(x_pos)
    ax2.set_xticklabels(df['name'], rotation=45, ha='right', fontsize=8)
    ax2.grid(True, alpha=0.3)
    
    # 3. Library Comparison
    if len(prost_benchmarks) > 0 and len(rkyv_benchmarks) > 0:
        bar_width = 0.35
        prost_x = np.arange(len(prost_benchmarks))
        rkyv_x = np.arange(len(rkyv_benchmarks))
        
        # Find common operation types for comparison
        prost_ops = [name.replace('Prost ', '') for name in prost_benchmarks['name']]
        rkyv_ops = [name.replace('Rkyv ', '').replace('Rkyv Zero-Copy Access', 'Read Access') 
                   for name in rkyv_benchmarks['name']]
        
        ax3.bar(prost_x, prost_benchmarks['mean_ns'], bar_width, 
               label='Prost', color=prost_color, alpha=0.8)
        ax3.bar(rkyv_x + bar_width, rkyv_benchmarks['mean_ns'], bar_width, 
               label='Rkyv', color=rkyv_color, alpha=0.8)
        
        ax3.set_yscale('log')
        ax3.set_title('Library Performance Comparison', fontweight='bold')
        ax3.set_ylabel('Time (nanoseconds)')
        ax3.set_xlabel('Benchmark Type')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        
        # Set x-tick labels to show operation types
        all_ops = prost_ops + rkyv_ops
        ax3.set_xticks(np.arange(len(all_ops)))
        ax3.set_xticklabels(all_ops, rotation=45, ha='right', fontsize=8)
    
    # 4. Performance Categories
    # Group by operation type
    operations = {}
    for _, row in df.iterrows():
        op_type = row['name'].split()[-1] if len(row['name'].split()) > 1 else row['name']
        if 'Serialization' in row['name']:
            op_type = 'Serialization'
        elif 'Deserialization' in row['name']:
            op_type = 'Deserialization'
        elif 'Mutation' in row['name']:
            op_type = 'Mutation'
        elif 'Access' in row['name'] or 'Read' in row['name']:
            op_type = 'Access'
        
        if op_type not in operations:
            operations[op_type] = []
        operations[op_type].append(row['mean_ns'])
    
    # Create box plot for different operations
    op_names = list(operations.keys())
    op_data = [operations[op] for op in op_names]
    
    box_plot = ax4.boxplot(op_data, tick_labels=op_names, patch_artist=True)
    ax4.set_yscale('log')
    ax4.set_title('Performance Distribution by Operation Type', fontweight='bold')
    ax4.set_ylabel('Time (nanoseconds)')
    ax4.grid(True, alpha=0.3)
    
    # Color the boxes
    colors = ['#FF9999', '#66B2FF', '#99FF99', '#FFD700']
    for patch, color in zip(box_plot['boxes'], colors[:len(box_plot['boxes'])]):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    
    plt.tight_layout()
    plt.savefig('benchmark_plot.png', dpi=300, bbox_inches='tight')
    
    return df

def main():
    # Updated benchmark data with new sample
    benchmark_data = """   Compiling rust_serialization_benchmark v0.1.0 (/home/thierry/repos/rust_serialization_benchmark)
    Finished `bench` profile [optimized] target(s) in 4.94s
     Running unittests src/main.rs (target/release/deps/rust_serialization_benchmark-ca70eef4b2624af0)

running 0 tests

test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s

     Running benches/serialization_benchmark.rs (target/release/deps/serialization_benchmark-7711d257b3012b6b)
Benchmarking Prost Serialization
Benchmarking Prost Serialization: Warming up for 3.0000 s
Benchmarking Prost Serialization: Collecting 100 samples in estimated 5.0138 s (2300 iterations)
Benchmarking Prost Serialization: Analyzing
Prost Serialization     time:   [2.3089 ms 2.4155 ms 2.5337 ms]
                        change: [+6.4033% +11.600% +17.250%] (p = 0.00 < 0.05)
                        Performance has regressed.
Found 22 outliers among 100 measurements (22.00%)
  3 (3.00%) high mild
  19 (19.00%) high severe

Benchmarking Prost Deserialization
Benchmarking Prost Deserialization: Warming up for 3.0000 s

Warning: Unable to complete 100 samples in 5.0s. You may wish to increase target time to 9.7s, enable flat sampling, or reduce sample count to 50.
Benchmarking Prost Deserialization: Collecting 100 samples in estimated 9.6951 s (5050 iterations)
Benchmarking Prost Deserialization: Analyzing
Prost Deserialization   time:   [1.6980 ms 1.7081 ms 1.7192 ms]
                        change: [−3.0550% −1.3583% +1.0413%] (p = 0.29 > 0.05)
                        No change in performance detected.
Found 7 outliers among 100 measurements (7.00%)
  5 (5.00%) high mild
  2 (2.00%) high severe

Benchmarking Prost Mutation
Benchmarking Prost Mutation: Warming up for 3.0000 s
Benchmarking Prost Mutation: Collecting 100 samples in estimated 5.7773 s (10k iterations)
Benchmarking Prost Mutation: Analyzing
Prost Mutation          time:   [901.78 ns 952.00 ns 1.0335 µs]
                        change: [−99.858% −63.252% +198.36%] (p = 0.58 > 0.05)
                        No change in performance detected.
Found 26 outliers among 100 measurements (26.00%)
  10 (10.00%) low severe
  6 (6.00%) low mild
  5 (5.00%) high mild
  5 (5.00%) high severe

Benchmarking Prost Read Access
Benchmarking Prost Read Access: Warming up for 3.0000 s
Benchmarking Prost Read Access: Collecting 100 samples in estimated 5.0000 s (17B iterations)
Benchmarking Prost Read Access: Analyzing
Prost Read Access       time:   [267.98 ps 274.31 ps 281.13 ps]
                        change: [−0.4056% +0.9049% +2.4908%] (p = 0.24 > 0.05)
                        No change in performance detected.
Found 14 outliers among 100 measurements (14.00%)
  1 (1.00%) high mild
  13 (13.00%) high severe

Benchmarking Rkyv Serialization
Benchmarking Rkyv Serialization: Warming up for 3.0000 s
Benchmarking Rkyv Serialization: Collecting 100 samples in estimated 7.6230 s (10k iterations)
Benchmarking Rkyv Serialization: Analyzing
Rkyv Serialization      time:   [362.22 µs 363.26 µs 364.43 µs]
                        change: [−62.330% −58.096% −53.460%] (p = 0.00 < 0.05)
                        Performance has improved.
Found 8 outliers among 100 measurements (8.00%)
  5 (5.00%) high mild
  3 (3.00%) high severe

Benchmarking Rkyv Deserialization
Benchmarking Rkyv Deserialization: Warming up for 3.0000 s
Benchmarking Rkyv Deserialization: Collecting 100 samples in estimated 5.2227 s (30k iterations)
Benchmarking Rkyv Deserialization: Analyzing
Rkyv Deserialization    time:   [171.02 µs 171.26 µs 171.59 µs]
                        change: [−19.534% −16.102% −12.666%] (p = 0.00 < 0.05)
                        Performance has improved.
Found 15 outliers among 100 measurements (15.00%)
  5 (5.00%) high mild
  10 (10.00%) high severe

Benchmarking Rkyv Mutation
Benchmarking Rkyv Mutation: Warming up for 3.0000 s
Benchmarking Rkyv Mutation: Collecting 100 samples in estimated 5.8701 s (15k iterations)
Benchmarking Rkyv Mutation: Analyzing
Rkyv Mutation           time:   [889.63 ns 923.99 ns 977.41 ns]
Found 15 outliers among 100 measurements (15.00%)
  9 (9.00%) low severe
  4 (4.00%) low mild
  1 (1.00%) high mild
  1 (1.00%) high severe

Benchmarking Rkyv Zero-Copy Access
Benchmarking Rkyv Zero-Copy Access: Warming up for 3.0000 s
Benchmarking Rkyv Zero-Copy Access: Collecting 100 samples in estimated 5.0000 s (19B iterations)
Benchmarking Rkyv Zero-Copy Access: Analyzing
Rkyv Zero-Copy Access   time:   [264.04 ps 269.65 ps 276.07 ps]
                        change: [−16.508% −13.918% −11.431%] (p = 0.00 < 0.05)
                        Performance has improved.
Found 16 outliers among 100 measurements (16.00%)
  5 (5.00%) high mild
  11 (11.00%) high severe
"""
    
    # To use with a file, replace the above with:
    # with open('your_benchmark_file.txt', 'r') as f:
    #     benchmark_data = f.read()
    
    # Parse the benchmark data
    benchmarks = parse_benchmark_file(benchmark_data)
    
    # Print summary
    print("Parsed Benchmarks:")
    print("-" * 50)
    for bench in benchmarks:
        print(f"{bench['name']:<35} {bench['original_mean']:>8.2f} {bench['original_unit']}")
    
    # Create visualizations
    df = create_histograms(benchmarks)
    
    return df

if __name__ == "__main__":
    df = main()
