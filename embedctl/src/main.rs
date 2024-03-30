mod constants;
pub mod directories;
mod prompt;

use anyhow::Result;
use ollama_rs::Ollama;
use qdrant_client::prelude::*;
use qdrant_client::qdrant::vectors_config::Config;
use qdrant_client::qdrant::{
    Condition, CreateCollection, Filter, SearchPoints, VectorParams, VectorsConfig,
};
use serde_json::json;

use clap::{App, Arg};

use constants::{AUTHOR, VERSION};

use crate::constants::{
    EMBEDDINGS_DIMENSION, OLLAMA_DEFAULT_HOST, OLLAMA_DEFAULT_PORT, QDRANT_DEFAULT_HOST,
    QDRANT_DEFAULT_PORT,
};
use crate::directories::get_embeddable_files;
use crate::prompt::{TEST_CONTENTS, TEST_EMBEDDING};

#[tokio::main]
async fn main() -> Result<()> {
    let cli = App::new("Nvim-llama Embeddings Controller")
        .version(VERSION)
        .author(AUTHOR)
        .about(
            "An embedding utility for use with qdrant, ollama, and the nvim-llama Neovim extension",
        )
        .arg(
            Arg::with_name("directory")
                .short("d")
                .long("directory")
                .value_name("DIRECTORY")
                .help("The path to the directory to do embeddings on")
                .required(true)
                .takes_value(true),
        )
        .get_matches();

    let dir_path = cli.value_of("directory").unwrap();
    let files = get_embeddable_files(dir_path);
    println!("files: {:?}", files);

    // Example of top level client
    // You may also use tonic-generated client from `src/qdrant.rs`
    let client =
        QdrantClient::from_url(format!("{}:{}", QDRANT_DEFAULT_HOST, QDRANT_DEFAULT_PORT).as_str())
            .build()?;

    let collections_list = client.list_collections().await?;
    dbg!(collections_list);

    let collection_name = "code";
    client.delete_collection(collection_name).await?;

    client
        .create_collection(&CreateCollection {
            collection_name: collection_name.into(),
            vectors_config: Some(VectorsConfig {
                config: Some(Config::Params(VectorParams {
                    size: EMBEDDINGS_DIMENSION as u64,
                    distance: Distance::Cosine.into(),
                    ..Default::default()
                })),
            }),
            ..Default::default()
        })
        .await?;

    let collection_info = client.collection_info(collection_name).await?;
    dbg!(collection_info);

    // --------------------------------------------
    // OLLAMA

    // By default it will connect to localhost:11434
    let ollama = Ollama::default();

    // For custom values:
    let ollama = Ollama::new(OLLAMA_DEFAULT_HOST.to_string(), OLLAMA_DEFAULT_PORT);

    let embedding_model = "all-minilm".to_string();
    let embedding_prompt = TEST_CONTENTS.to_string();
    let embedding_resp = ollama
        .generate_embeddings(embedding_model, embedding_prompt, None)
        .await
        .unwrap();

    let payload: Payload = json!(
        {
            "file name": "qdrant.rs",
            "file contents": TEST_CONTENTS,
        }
    )
    .try_into()
    .unwrap();

    // Convert Vec<f64> to Vec<f32>
    let embeddings_32: Vec<f32> = embedding_resp
        .embeddings
        .into_iter()
        .map(|x| x as f32)
        .collect();

    let point = vec![PointStruct::new(0, embeddings_32, payload)];
    client
        .upsert_points_blocking(collection_name, None, point, None)
        .await?;

    let question_32: Vec<f32> = TEST_EMBEDDING.into_iter().map(|x| x as f32).collect();

    let search_result = client
        .search_points(&SearchPoints {
            collection_name: collection_name.into(),
            vector: question_32,
            limit: 10,
            with_payload: Some(true.into()),
            ..Default::default()
        })
        .await?;

    dbg!(&search_result);

    Ok(())
}
