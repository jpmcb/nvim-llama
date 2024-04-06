use anyhow::Result;
use nvim_llama_constants::EMBEDDINGS_DIMENSION;
use qdrant_client::prelude::*;
use qdrant_client::qdrant::vectors_config::Config;
use qdrant_client::qdrant::{CreateCollection, VectorParams, VectorsConfig};
use serde_json::json;

pub struct NvimQdrantClient {
    client: QdrantClient,
}

impl NvimQdrantClient {
    pub fn new(host: String, port: u16) -> Result<NvimQdrantClient> {
        let client = QdrantClient::from_url(format!("{}:{}", host, port).as_str()).build()?;
        Ok(NvimQdrantClient { client })
    }

    pub async fn upsert_embedding(&self, embedding: Vec<f32>) -> Result<()> {
        let collection_name = "code";
        self.client.delete_collection(collection_name).await?;

        self.client
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

        let collection_info = self.client.collection_info(collection_name).await?;
        dbg!(collection_info);

        let payload: Payload = json!(
            {
                "foo": "Bar",
                "bar": 12,
                "baz": {
                    "qux": "quux"
                }
            }
        )
        .try_into()
        .unwrap();

        let point = vec![PointStruct::new(0, embedding, payload)];
        self.client
            .upsert_points_blocking(collection_name, None, point, None)
            .await?;

        Ok(())
    }
}
