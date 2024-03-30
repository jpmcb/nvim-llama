use std::{
    fs::File,
    io::{self, BufRead, BufReader},
};

use ollama_rs::{generation::completion::request::GenerationRequest, Ollama};
use serde::Serialize;
use tinytemplate::TinyTemplate;

use crate::prompt::DEFAULT_PROMPT_TEMPLATE;

#[derive(Serialize)]
struct Prompt {
    context: String,
    current_line: String,
    surrounding_lines: String,
}

/// Extracts and returns the specified line and a block of lines from a file.
///
/// # Arguments
///
/// * `filename` - A string slice that holds the name of the file.
/// * `line_number` - The line number of interest.
/// * `start_block` - The starting line number of the block.
/// * `end_block` - The ending line number of the block.
///
/// # Returns
///
/// This function returns a `Result` containing a tuple of two `String`s:
/// - The first `String` is the content of the specified line.
/// - The second `String` is the concatenated content of the block, from `start_block` to `end_block`.
/// If an error occurs, the function returns an `io::Error`.
fn extract_line_and_block(
    filename: &str,
    line_number: usize,
    start_block: usize,
    end_block: usize,
) -> Result<(String, String), io::Error> {
    // Open the file.
    let file = File::open(filename)?;
    let reader = BufReader::new(file);

    // Variables to store the line and block contents.
    let mut line_content = String::new();
    let mut block_content = String::new();

    // Enumerate over the lines of the file.
    for (index, line) in reader.lines().enumerate() {
        let current_line_number = index + 1; // Adjust for 0-based indexing.
        let line = line?;

        // Check if this is the line of interest.
        if current_line_number == line_number {
            line_content = line.clone();
        }

        // Check if this line is within the block of interest.
        if current_line_number >= start_block && current_line_number <= end_block {
            block_content.push_str(&line);
            block_content.push('\n'); // Add a newline to separate the lines in the block.
        }

        // Early exit if we've passed the end block.
        if current_line_number > end_block && !line_content.is_empty() {
            break;
        }
    }

    Ok((line_content, block_content))
}

pub async fn generate_ollama(
    filename: &str,
    context: &str,
    current_line_num: usize,
    start_block_line_num: usize,
    end_block_line_num: usize,
) {
    let (line, block) = match extract_line_and_block(
        filename,
        current_line_num,
        start_block_line_num,
        end_block_line_num,
    ) {
        Err(e) => {
            println!("Error! {}", e);
            return;
        }
        Ok((line, block)) => {
            println!("line: {}", line);
            println!("block: {}", block);
            (line, block)
        }
    };

    // create the ollama client
    let ollama = Ollama::new("http://localhost".to_string(), 11434);

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

    let res = ollama
        .generate(GenerationRequest::new(model, rendered))
        .await;

    match res {
        Err(e) => {
            println!("Error! {}", e);
        }
        Ok(res) => {
            println!("Response: {}", res.response);
        }
    }

    // TODO - sometimes the model produces output like:
    // ```language
    // code
    // ```
    // which is abit annoying. Look at post processing the output to get rid of:
    // - surrounding newlines
    // - surrounding backticks and metadata
}
