use anyhow::Result;
use nvim_llama_prompting::DEFAULT_PROMPT_TEMPLATE;
use nvim_llama_utils::extract_line_and_block;
use openai_api_rs::v1::{
    api::Client as OpenAiClient,
    chat_completion::{self, ChatCompletionRequest},
    common::{GPT4, TEXT_EMBEDDING_3_SMALL},
    completion::CompletionRequest,
    embedding::EmbeddingRequest as OpenAiEmbeddingRequest,
};
use serde::Serialize;
use tinytemplate::TinyTemplate;

#[derive(Serialize)]
struct Prompt {
    context: String,
    current_line: String,
    surrounding_lines: String,
}

pub struct NvimOpenAiClient {
    client: OpenAiClient,
}

impl NvimOpenAiClient {
    pub fn new(apiKey: String) -> NvimOpenAiClient {
        // TODO - need to slurp up an env var for the openAI key
        // env::var("OPENAI_API_KEY").unwrap().to_string()

        NvimOpenAiClient {
            client: OpenAiClient::new(apiKey),
        }
    }

    pub async fn generate_embedding(&self, text: String) -> Result<Vec<f32>> {
        let mut req = OpenAiEmbeddingRequest::new(TEXT_EMBEDDING_3_SMALL.to_string(), text);
        // The dimensions returned by text-embedding-3-small
        req.dimensions = Some(1536);
        let result = self.client.embedding(req)?;

        // check if length of embedding is messed up: should just be 1 since we're only sending
        // a single embedding request

        Ok(result.data[0].embedding.clone())
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
        let mut tt = TinyTemplate::new();
        let _ = tt.add_template("default-prompt", DEFAULT_PROMPT_TEMPLATE);

        let prompt = Prompt {
            context: context.to_string(),
            current_line: line,
            surrounding_lines: block,
        };

        let rendered = tt.render("default-prompt", &prompt).unwrap();
        let req = ChatCompletionRequest::new(
            GPT4.to_string(),
            vec![chat_completion::ChatCompletionMessage {
                role: chat_completion::MessageRole::user,
                content: chat_completion::Content::Text(rendered),
                name: None,
            }],
        );

        let result = self.client.chat_completion(req)?;

        match result.choices[0].message.content.clone() {
            Some(s) => Ok(s),
            None => Ok("no response.".to_string()),
        }
    }

    pub async fn generate_text(&self, context: &str, text: &str) -> Result<String> {
        let req = CompletionRequest::new(GPT4.to_string(), text.to_string());
        let result = self.client.completion(req)?;

        Ok(result.choices[0].text.clone())
    }
}
