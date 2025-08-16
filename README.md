# Author

Thierry Vilmart

2025

# Overview

Here lies a simple Rust project using the Criterion tool to benchmark statistically using multiple runs.


We benchmarked serializing using Prost, or Rkyv, two widely used libraries for serialization of structures. Prost uses protofuf, and rkyv uses zero-copy direct serialization.


The Rust code was written in detail by the author. The python script to make the plot was produce by Claude AI.


In conclusion, Rkyv is known for performance, and showed better results in our benchmark, negligibly faster for mutation, and read access, and significatly faster for serializing and deserializing. The well-known key feature of rkyv consists in the zero-copy buffer, and it helps slightly for deserializing and data access. But it does not make a difference between serializing and deserializing. The speed-up compared to prost is due to how memory is managed, as is explained by the Claude AI in the code below.

![Here lies the performance difference explained by Claude AI](https://github.com/MagicPoulp/rust_serialization_benchmark/blob/main/SPEED_ANALYSIS.md)

# Dependencies

On Debian 13


Python is used in a post-processing step to create plots.

```bash
apt-get install rustup build-essential protobuf-compiler gnuplot python3-venv
python3 -m venv /home/python/env1
source /home/python/env1/bin/activate
pip install pandas matplotlib
cargo bench > doc/benchmark_results1.txt 2>&1
python3 plot.py
firefox benchmark_plot.png
```

# Run

cargo bench

# Results

The difference can be seen clearly on the bottom left plot on the image below.


The results were run on a powerful system, running Debian stable.


Here are the numbers.


Prost Serialization                     2.42 ms

Rkyv Serialization                    363.26 µs


Prost Deserialization                   1.71 ms

Rkyv Deserialization                  171.26 µs


Prost Mutation                        952.00 ns

Rkyv Mutation                         923.99 ns


Prost Read Access                     274.31 ps

Rkyv Zero-Copy Access                 269.65 ps


![Here lies the plot image from the script](https://github.com/MagicPoulp/rust_serialization_benchmark/blob/main/benchmark_plot.png)


![Here lies the content of the cargo bench output](https://github.com/MagicPoulp/rust_serialization_benchmark/blob/main/doc/benchmark_results1.txt)
