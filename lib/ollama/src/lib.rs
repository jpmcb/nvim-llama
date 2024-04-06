use anyhow::Result;
use nvim_llama_prompting::DEFAULT_PROMPT_TEMPLATE;
use nvim_llama_utils::extract_line_and_block;
use ollama_rs::{generation::completion::request::GenerationRequest, Ollama};
use serde::Serialize;
use tinytemplate::TinyTemplate;

#[derive(Serialize)]
struct Prompt {
    context: String,
    current_line: String,
    surrounding_lines: String,
}

pub struct NvimOllamaClient {
    client: Ollama,
}

impl NvimOllamaClient {
    pub fn new(host: String, port: u16) -> NvimOllamaClient {
        NvimOllamaClient {
            client: Ollama::new(host, port),
        }
    }

    pub async fn generate_embedding(&self, text: String) -> Result<Vec<f32>> {
        let embedding_model = "all-minilm".to_string();
        let embedding_resp = self
            .client
            .generate_embeddings(embedding_model, text, None)
            .await?;

        // Convert Vec<f64> to Vec<f32>
        let embeddings_32: Vec<f32> = embedding_resp
            .embeddings
            .into_iter()
            .map(|x| x as f32)
            .collect();

        Ok(embeddings_32)
    }

    pub async fn generate_code(
        &self,
        filename: &str,
        context: &str,
        current_line_num: usize,
        start_block_line_num: usize,
        end_block_line_num: usize,
    ) -> Result<String> {
        let (line, block) = extract_line_and_block(
            filename,
            current_line_num,
            start_block_line_num,
            end_block_line_num,
        )?;

        // TODO - check if model already pulled down.
        // if not, attempt to pull it.
        let model = "mistral:latest".to_string();

        let mut tt = TinyTemplate::new();
        let _ = tt.add_template("default-prompt", DEFAULT_PROMPT_TEMPLATE);

        let prompt = Prompt {
            context: context.to_string(),
            current_line: line,
            surrounding_lines: block,
        };

        let rendered = tt.render("default-prompt", &prompt).unwrap();

        let res = self
            .client
            .generate(GenerationRequest::new(model, rendered))
            .await?;

        // TODO - sometimes the model produces output like:
        // ```language
        // code
        // ```
        // which is abit annoying. Look at post processing the output to get rid of:
        // - surrounding newlines
        // - surrounding backticks and metadata

        Ok(res.response)
    }

    pub async fn generate_text(&self, context: &str, text: &str) -> Result<String> {
        // TODO - need to come back and actually implement this.
        //
        let model = "mistral:latest".to_string();

        let mut tt = TinyTemplate::new();
        let _ = tt.add_template("default-prompt", DEFAULT_PROMPT_TEMPLATE);

        let prompt = Prompt {
            context: context.to_string(),
            current_line: 0.to_string(),
            surrounding_lines: text.to_string(),
        };

        let rendered = tt.render("default-prompt", &prompt).unwrap();

        let res = self
            .client
            .generate(GenerationRequest::new(model, rendered))
            .await?;

        Ok(res.response)
    }
}
