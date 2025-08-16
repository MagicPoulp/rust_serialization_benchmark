use criterion::{criterion_group, criterion_main, Criterion};
use prost::Message;
use std::hint::black_box;
use rkyv::{Archive, Deserialize, Serialize};
use rkyv::{api::high::to_bytes_with_alloc, ser::allocator::Arena};

use rkyv::access_unchecked;
use rkyv::Archived;
use rkyv::rancor::Error;

// Include the generated Rust code from `data.proto`
// Note: This line requires your build script to generate this file.
include!(concat!(env!("OUT_DIR"), "/benchmark.rs"));

#[derive(Archive, Serialize, Deserialize, Debug, PartialEq, Clone)]
pub struct RkyvData {
    pub long_vector1: Vec<i32>,
    pub name: String,
    pub id: i32,
    pub long_vector2: Vec<i32>,
    pub items: Vec<String>,
}

fn create_prost_data() -> Data {
    let mut digits: Vec<i32> = Vec::new();
    for i in 0..10_000 {
        digits.push((i % 10) as i32);
    }
    Data {
        long_vector1: vec![1; 500_000],
        name: "Test name to try".to_string(),
        id: 12345,
        long_vector2: digits,
        items: vec!["item1".to_string(), "item2".to_string(), "item3".to_string()],
    }
}

fn create_rkyv_data() -> RkyvData {
    let mut digits: Vec<i32> = Vec::new();
    for i in 0..10_000 {
        digits.push((i % 10) as i32);
    }
    RkyvData {
        long_vector1: vec![1; 500_000],
        name: "Test name to try".to_string(),
        id: 12345,
        long_vector2: digits,
        items: vec!["item1".to_string(), "item2".to_string(), "item3".to_string()],
    }
}

fn mutate_prost_data(data: &mut Data) {
    data.id = 54321;
    data.items.push("new_item".to_string());
}

fn mutate_rkyv_data(data: &mut RkyvData) {
    data.id = 54321;
    data.items.push("new_item".to_string());
}

fn access_prost_data(data: &Data) {
    // Access an element that is not at the very beginning or end
    data.long_vector2[data.long_vector2.len() / 2];
}

fn access_rkyv_archived_data(data: &Archived<RkyvData>) {
    // Access an element that is not at the very beginning or end
    // Archived vectors can be indexed directly like slices
    data.long_vector2[data.long_vector2.len() / 2];
}

// --- Prost Benchmarks ---
pub fn prost_serialization_benchmark(c: &mut Criterion) {
    let data = create_prost_data();
    c.bench_function("Prost Serialization", |b| {
        b.iter(|| black_box(data.encode_to_vec()))
    });
}

pub fn prost_deserialization_benchmark(c: &mut Criterion) {
    let data = create_prost_data();
    let encoded = data.encode_to_vec();
    c.bench_function("Prost Deserialization", |b| {
        b.iter(|| black_box(Data::decode(&*encoded).unwrap()))
    });
}

pub fn prost_mutation_benchmark(c: &mut Criterion) {
    c.bench_function("Prost Mutation", |b| {
        b.iter_batched(
            create_prost_data,
            |mut data| black_box(mutate_prost_data(&mut data)),
            criterion::BatchSize::SmallInput,
        )
    });
}

pub fn prost_access_benchmark(c: &mut Criterion) {
    let data = create_prost_data();
    c.bench_function("Prost Read Access", |b| {
        b.iter(|| black_box(access_prost_data(&data)))
    });
}

// --- Rkyv Benchmarks ---
pub fn rkyv_serialization_benchmark(c: &mut Criterion) {
    let data = create_rkyv_data();
    c.bench_function("Rkyv Serialization", |b| {
        b.iter_batched(
            || (data.clone(), Arena::new()),
            |(value, mut arena)| {
                black_box(to_bytes_with_alloc::<_, Error>(&value, arena.acquire()).unwrap());
            },
            criterion::BatchSize::SmallInput,
        )
    });
}

pub fn rkyv_deserialization_benchmark(c: &mut Criterion) {
    let data = create_rkyv_data();
    let mut arena = Arena::new();
    let encoded = to_bytes_with_alloc::<_, Error>(&data, arena.acquire()).unwrap();

    c.bench_function("Rkyv Deserialization", |b| {
        b.iter(|| black_box(rkyv::from_bytes::<RkyvData, Error>(&*encoded).unwrap()))
    });
}


pub fn rkyv_mutation_benchmark(c: &mut Criterion) {
    c.bench_function("Rkyv Mutation", |b| {
        b.iter_batched(
            create_rkyv_data,
            |mut data| black_box(mutate_rkyv_data(&mut data)),
            criterion::BatchSize::SmallInput,
        )
    });
}

pub fn rkyv_zero_copy_access_benchmark(c: &mut Criterion) {
    let data = create_rkyv_data();
    let mut arena = Arena::new();
    let encoded = to_bytes_with_alloc::<_, Error>(&data, arena.acquire()).unwrap();

    let archived_data = unsafe { access_unchecked::<Archived<RkyvData>>(&encoded) };

    c.bench_function("Rkyv Zero-Copy Access", |b| {
        b.iter(|| black_box(access_rkyv_archived_data(archived_data)))
    });
}

// Define the Criterion benchmark groups
criterion_group!(
    benches,
    prost_serialization_benchmark,
    prost_deserialization_benchmark,
    prost_mutation_benchmark,
    prost_access_benchmark,
    rkyv_serialization_benchmark,
    rkyv_deserialization_benchmark,
    rkyv_mutation_benchmark,
    rkyv_zero_copy_access_benchmark,
);

// This macro generates the `main` function for the benchmark harness.
criterion_main!(benches);
