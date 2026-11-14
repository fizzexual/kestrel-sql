"""Fresh143: identical index kernels/timers with typed wide-integer text output."""
from pathlib import Path
R=Path('D:/Codex/Kestrel/work')
def put(name,text):
    p=R/name;assert not p.exists(),name;p.write_text(text.replace('\r\n','\n').rstrip()+'\n',encoding='utf-8',newline='\n')
template=(R/'index_profile_142.template.rs').read_text().replace('use serde_json::json;\n','')
output='''#[derive(Serialize)]
struct Output<'a> {
    trial: u32,
    workload: &'a str,
    seed: usize,
    variant: &'a str,
    rows: usize,
    columns: usize,
    repetitions: usize,
    elapsed_ns: u128,
    input_sha256: &'a str,
    indexes: &'a [Index],
    legacy_profile: &'a Stages,
    all_checks_passed: bool,
    index_kernel_only: bool,
    #[serde(rename = "archive_IO_sync_ACK_excluded")]
    archive_io_sync_ack_excluded: bool,
    input_generation_sort_sha_excluded: bool,
    profile_outside_primary_timer: bool,
}

// Serialize typed fields directly to JSON text. Converting through Value would
// reject exact i128 prefix sums beyond the Value Number range in this build.
fn encode_output(output: &Output<'_>) -> String {
    serde_json::to_string(output).unwrap()
}

'''
template=template.replace('fn main() {',output+'fn main() {',1)
start=template.index('    println!("{}", json!(');end=template.index('\n}\n',start)
template=template[:start]+'''    let output = Output {
        trial: 143, workload: shape, seed, variant: &args[3],
        rows: 32768, columns: 3, repetitions: REPETITIONS, elapsed_ns,
        input_sha256: &input_sha256, indexes: &result, legacy_profile: &stages,
        all_checks_passed: true, index_kernel_only: true,
        archive_io_sync_ack_excluded: true,
        input_generation_sort_sha_excluded: true, profile_outside_primary_timer: true,
    };
    println!("{}", encode_output(&output));'''+template[end:]
test='''    #[test]
    fn typed_output_preserves_wide_positive_and_negative_i128_prefixes() {
        let indexes = legacy(&[vec![i64::MAX; 4097], vec![i64::MIN; 4097]]);
        let stages = Stages::default();
        let output = Output {
            trial: 143, workload: "wide-output-test", seed: 5, variant: "candidate",
            rows: 4097, columns: 2, repetitions: 16, elapsed_ns: 1,
            input_sha256: "test", indexes: &indexes, legacy_profile: &stages,
            all_checks_passed: true, index_kernel_only: true,
            archive_io_sync_ack_excluded: true,
            input_generation_sort_sha_excluded: true, profile_outside_primary_timer: true,
        };
        let json = encode_output(&output);
        assert!(json.contains("\\"prefix\\":[0,37778931862957161705472,37788155234994016481279]"));
        assert!(json.contains("\\"prefix\\":[0,-37778931862957161709568,-37788155234994016485376]"));
    }
'''
template=template.replace('    #[test]\n    fn extrema_reuse_matches_',test+'    #[test]\n    fn extrema_reuse_matches_',1)
put('index_profile_143.template.rs',template)
prep=(R/'prepare_index_profile_142.py').read_text().replace('142','143')
prep=prep.replace("load(R/'work/phase141-storage-cleanup-proof.json')['completed141_stores_closed']", "load(R/'work/profile142-storage-cleanup-proof.json')['complete']")
prep=prep.replace("load(R/'work/phase141-publication-proof.json')['private_main']", "load(R/'work/profile142-remote-save-proof.json')['head']")
prep=prep.replace("'Two fresh example-only tests normal debug/release", "'Three fresh example-only tests normal debug/release, including exact wide-i128 typed JSON output")
prep=prep.replace("'research':['https://doc.rust-lang.org/std/hint/fn.black_box.html']", "'research':['https://doc.rust-lang.org/std/hint/fn.black_box.html','https://docs.rs/serde_json/latest/serde_json/value/struct.Serializer.html','https://docs.rs/serde_json/latest/src/serde_json/ser.rs.html']")
prep=prep.replace("'source_merging_120_not_adopted':True", "'source_merging_120_not_adopted':True,'prior142_output_failure_preserved':True,'only_output_serializer_changed_vs142_outside_timer':True")
put('prepare_index_profile_143.py',prep)
for old,new in [('prepare_profile142.ps1','prepare_profile143.ps1'),('prepare_profile142_build.ps1','prepare_profile143_build.ps1'),('launch_build_profile142.ps1','launch_build_profile143.ps1')]:put(new,(R/old).read_text().replace('142','143'))
build=(R/'build_index_profile_142.py').read_text().replace('142','143').replace("row['fresh_kernel_tests']==2", "row['fresh_kernel_tests']==3").replace("'fresh_kernel_tests':4", "'fresh_kernel_tests':6")
put('build_index_profile_143.py',build)
for old,new in [('index_reference_142.py','index_reference_143.py'),('audit_index_profile_142.py','audit_index_profile_143.py'),('audit_lifecycle_profile142.py','audit_lifecycle_profile143.py')]:
    text=(R/old).read_text().replace('142','143')
    if old.startswith('audit_index'):text=text.replace('assert len(workers)==3','assert len(workers)==2')
    put(new,text)
derive=(R/'derive_index_harness_142.py').read_text().replace('142','143')
# The new started checkpoint is appended only after its actual build proof.
derive=derive.replace("First wrapper sandbox", "Prior142 wrapper sandbox")
put('derive_index_harness_143.py',derive)
print('Fresh143 templates/harness sources prepared; no library/kernel/timer operation changed',flush=True)
