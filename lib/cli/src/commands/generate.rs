use anyhow::Result;
use nvim_llama_constants::{OLLAMA_DEFAULT_HOST, OLLAMA_DEFAULT_PORT};

use crate::Clients;

pub async fn generate_command(
    client: Clients,
    filepath: &str,
    line_num: usize,
    starting_block_line_num: usize,
    ending_block_line_num: usize,
) -> Result<()> {
    match client {
        Clients::Ollama => {
            // perform a similarity, cosign search for embedding

            let ollama_client = nvim_llama_ollama::NvimOllamaClient::new(
                OLLAMA_DEFAULT_HOST.to_string(),
                OLLAMA_DEFAULT_PORT,
            );

            let generated_text = ollama_client
                .generate_code(
                    filepath,
                    "",
                    line_num,
                    starting_block_line_num,
                    ending_block_line_num,
                )
                .await?;

            print!("{}", generated_text);

            Ok(())
        }

        Clients::OpenAI => {
            let openai_client = nvim_llama_openai_client::NvimOpenAiClient::new("".to_string(), 0);

            let generate_text = openai_client
                .generate_code(
                    filepath,
                    "",
                    line_num,
                    starting_block_line_num,
                    ending_block_line_num,
                )
                .await?;

            println!("{}", generate_text);

            Ok(())
        }
    }
}
