
fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Tell Cargo that if the .proto file changes, to rerun this build script.
    println!("cargo:rerun-if-changed=proto/data.proto");

    // Configure prost_build to compile our .proto file.
    // The `compile_protos` function takes a list of .proto files
    // and a list of directories to search for imports.
    prost_build::compile_protos(&["proto/data.proto"], &["./proto/"])?;

    Ok(())
}
