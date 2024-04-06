use anyhow::Result;
use nvim_llama_cli::cli_run;

#[tokio::main]
async fn main() -> Result<()> {
    cli_run().await?;
    Ok(())
}
