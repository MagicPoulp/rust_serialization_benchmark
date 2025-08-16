use criterion::{criterion_group, criterion_main, Criterion};
use prost::Message;
use std::hint::black_box;

// Include the generated Rust code from `data.proto`
// The `build.rs` script creates this file in `OUT_DIR`.
include!(concat!(env!("OUT_DIR"), "/benchmark.rs"));

// Helper function to create a new `Data` struct with some data
fn create_data() -> Data {
    let mut digits: Vec<i32> = Vec::new(); // Declare a mutable vector
    for i in 0..10_000 {
        digits.push((i % 10) as i32); // Pushes the last digit of 'i' to the vector
    }
    Data {
        long_vector1: vec![1; 50_000],
        name: "Test name to try".to_string(),
        id: 12345,
        long_vector2: digits,
        items: vec!["item1".to_string(), "item2".to_string(), "item3".to_string()],
    }
}

// Helper function to mutate a `Data` struct
fn mutate_data(data: &mut Data) {
    data.id = 54321;
    data.items.push("new_item".to_string());
}

// Helper function to access data from a `Data` struct
fn access_data(data: &Data) -> usize {
    data.name.len() + data.items.len()
}

// All benchmark functions must be in this format
pub fn serialization_benchmark(c: &mut Criterion) {
    let data = create_data();
    c.bench_function("serialization", |b| {
        b.iter(|| black_box(data.encode_to_vec())) // Benchmark the serialization time
    });
}

pub fn deserialization_benchmark(c: &mut Criterion) {
    let data = create_data();
    let encoded = data.encode_to_vec();
    c.bench_function("deserialization", |b| {
        b.iter(|| black_box(Data::decode(&*encoded))) // Benchmark the deserialization time
    });
}

pub fn mutation_benchmark(c: &mut Criterion) {
    c.bench_function("mutation", |b| {
        b.iter_batched(
            create_data, // Setup: create a fresh `Data` struct for each iteration
            |mut data| black_box(mutate_data(&mut data)), // Action: benchmark the mutation
            criterion::BatchSize::SmallInput,
        )
    });
}

pub fn access_benchmark(c: &mut Criterion) {
    let data = create_data();
    c.bench_function("read_access", |b| {
        b.iter(|| black_box(access_data(&data))) // Benchmark the read/access time
    });
}

// Define the Criterion benchmark groups
criterion_group!(
    benches,
    serialization_benchmark,
    deserialization_benchmark,
    mutation_benchmark,
    access_benchmark
);

// This macro generates the `main` function for the benchmark harness.
criterion_main!(benches);
