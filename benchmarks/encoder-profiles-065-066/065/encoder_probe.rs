//! Fixed-input CPU serializer/allocation models, never a database benchmark.
use serde::ser::{SerializeMap, Serializer};
use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;
use std::hint::black_box;
use std::io::{self, Write};
use std::time::Instant;
include!("released_encoder_models.rs");

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct OwnedCatalog {
    generation: u64,
    receipt_base: Option<u64>,
    table: String,
    columns: Vec<String>,
    segments: Vec<String>,
    batches: BTreeMap<String, BatchRecord>,
}

fn encode(value: &CatalogOutput<'_>, mode: &str, output: &mut Vec<u8>, exact: usize) {
    match mode {
        "baseline" => *output = serde_json::to_vec(value).unwrap(),
        "reserve_exact" => {
            *output = Vec::with_capacity(exact);
            serde_json::to_writer(&mut *output, value).unwrap();
        }
        "reuse" => {
            output.clear();
            serde_json::to_writer(&mut *output, value).unwrap();
        }
        _ => panic!("unknown mode"),
    }
}

fn self_test() {
    let strings = [
        "plain",
        "quote\"slash\\",
        "line\n\ttab\r",
        "snowman\u{2603}",
        "null\0control\u{1}",
        "\u{2028}\u{2029}",
    ];
    let mut checks = 0;
    for (index, text) in strings.iter().enumerate() {
        let mut committed = BTreeMap::new();
        committed.insert(
            format!("old:{text}"),
            BatchRecord {
                digest: [index as u8; 32],
                rows: usize::MAX,
                generation: u64::MAX,
            },
        );
        let added = BTreeMap::from([(
            format!("new:{text}"),
            BatchRecord {
                digest: [255; 32],
                rows: 0,
                generation: 0,
            },
        )]);
        let columns = vec![text.to_string(), "value".into()];
        let segments = vec![format!("segment:{text}")];
        for use_committed in [false, true] {
            let value = CatalogOutput {
                generation: u64::MAX,
                receipt_base: if use_committed { None } else { Some(0) },
                table: text,
                columns: &columns,
                segments: &segments,
                batches: CombinedBatches {
                    committed: use_committed.then_some(&committed),
                    added: &added,
                },
            };
            let expected = serde_json::to_vec(&value).unwrap();
            let mut output = Vec::new();
            for mode in ["baseline", "reserve_exact", "reuse", "reuse"] {
                encode(&value, mode, &mut output, expected.len());
                assert_eq!(output, expected);
                let parsed: serde_json::Value = serde_json::from_slice(&output).unwrap();
                assert_eq!(parsed["table"].as_str().unwrap(), *text);
                checks += 1;
            }
        }
    }
    println!(
        "{}",
        serde_json::json!({"self_test":true,"byte_equality_and_json_checks":checks,"wide_integers_and_escaped_unicode":true})
    );
}

struct CapacityTrace {
    bytes: Vec<u8>,
    events: Vec<(usize, usize, usize)>,
}
impl Write for CapacityTrace {
    fn write(&mut self, data: &[u8]) -> io::Result<usize> {
        let before = self.bytes.capacity();
        let length = self.bytes.len();
        self.bytes.extend_from_slice(data);
        if self.bytes.capacity() != before {
            self.events.push((length, before, self.bytes.capacity()));
        }
        Ok(data.len())
    }
    fn flush(&mut self) -> io::Result<()> {
        Ok(())
    }
}

fn main() {
    let args: Vec<_> = std::env::args().collect();
    if args.get(1).is_some_and(|v| v == "--self-test") {
        self_test();
        return;
    }
    let expected = std::fs::read(args.get(1).expect("input JSON path")).unwrap();
    let mode = args.get(2).expect("mode");
    let repetitions: usize = args.get(3).expect("repetitions").parse().unwrap();
    assert!((2..=128).contains(&repetitions));
    let last_id = args.get(4).expect("last receipt ID");
    let mut input: OwnedCatalog = serde_json::from_slice(&expected).unwrap();
    assert!(input.receipt_base.is_none());
    let receipts = input.batches.len();
    let added = BTreeMap::from([(last_id.clone(), input.batches.remove(last_id).unwrap())]);
    let value = CatalogOutput {
        generation: input.generation,
        receipt_base: input.receipt_base,
        table: &input.table,
        columns: &input.columns,
        segments: &input.segments,
        batches: CombinedBatches {
            committed: Some(&input.batches),
            added: &added,
        },
    };
    if mode == "--trace" {
        let mut records = Vec::new();
        for (name, capacity) in [
            ("baseline128", 128),
            ("reserve_exact", expected.len()),
            ("reuse_first", 0),
        ] {
            let mut trace = CapacityTrace {
                bytes: Vec::with_capacity(capacity),
                events: Vec::new(),
            };
            serde_json::to_writer(&mut trace, &value).unwrap();
            assert_eq!(trace.bytes, expected);
            records.push(serde_json::json!({"model":name,"initial_capacity":capacity,"final_capacity":trace.bytes.capacity(),"capacity_growths":trace.events,
                "not_allocator_call_counts":true,"excluded_from_all_timed_samples":true}));
            if name == "reuse_first" {
                trace.bytes.clear();
                trace.events.clear();
                serde_json::to_writer(&mut trace, &value).unwrap();
                assert_eq!(trace.bytes, expected);
                records.push(serde_json::json!({"model":"reuse_warm","final_capacity":trace.bytes.capacity(),"capacity_growths":trace.events,
                    "not_allocator_call_counts":true,"excluded_from_all_timed_samples":true}));
            }
        }
        println!(
            "{}",
            serde_json::json!({"trace":true,"receipt_count":receipts,"input_bytes":expected.len(),"records":records})
        );
        return;
    }
    let mut reused = Vec::new();
    let mut samples = Vec::new();
    let mut capacities = Vec::new();
    for _ in 0..repetitions {
        let mut output = if mode == "reuse" {
            std::mem::take(&mut reused)
        } else {
            Vec::new()
        };
        let started = Instant::now();
        encode(black_box(&value), mode, &mut output, expected.len());
        samples.push(started.elapsed().as_secs_f64() * 1000.0);
        assert_eq!(output, expected, "stored bytes differ");
        black_box(&output);
        capacities.push(output.capacity());
        if mode == "reuse" {
            reused = output;
        }
    }
    println!(
        "{}",
        serde_json::json!({"profiled_engine_version":"0.3.16","encoder_model_only":true,"mode":mode,"receipt_count":receipts,
        "input_bytes":expected.len(),"repetitions":repetitions,"raw_ms":samples,"capacities":capacities,"every_output_matches_original_catalog_bytes":true,
        "first_reuse_allocation_inside_first_timer":true,"no_database_publication":true})
    );
}
