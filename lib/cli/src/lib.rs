mod commands;

use anyhow::Result;
use clap::Parser;

#[derive(Parser)]
#[command(name = "nvllamactl")]
#[command(bin_name = "nvllamactl")]
enum NvLlamaCtl {
    Generate(GenerateArgs),
}

#[derive(clap::ValueEnum, Clone, Debug, Default)]
enum Clients {
    #[default]
    Ollama,

    OpenAI,
}

#[derive(Parser, Debug)]
#[command(version, about, long_about = None)]
struct GenerateArgs {
    #[arg(long, short, default_value_t, value_enum)]
    use_client: Clients,

    #[arg(long, short)]
    filepath: String,

    #[arg(long, short)]
    line_num: usize,

    #[arg(long, short)]
    starting_block_line_num: usize,

    #[arg(long, short)]
    ending_block_line_num: usize,
}

/// Run the Nvim_llama control utility
pub async fn cli_run() -> Result<()> {
    let cli_args = NvLlamaCtl::parse();

    match cli_args {
        NvLlamaCtl::Generate(args) => {
            commands::generate::generate_command(
                args.use_client,
                &args.filepath,
                args.line_num,
                args.starting_block_line_num,
                args.ending_block_line_num,
            )
            .await?;
        }
    }

    Ok(())
}
