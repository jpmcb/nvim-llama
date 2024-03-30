mod constants;
mod ollama;
mod prompt;

use clap::{App, Arg};
use ollama::generate_ollama;

use crate::constants::{AUTHOR, VERSION};

#[tokio::main]
async fn main() {
    let cli = App::new("Nvim-llama Ollama Controller")
        .version(VERSION)
        .author(AUTHOR)
        .about(
            "A controller utility for Ollama to be used with ollama and the nvim-llama Neovim extension",
        )
        .arg(
            Arg::with_name("filepath")
                .short("f")
                .long("filepath")
                .value_name("FILEPATH")
                .help("The path to the file")
                .required(true)
                .takes_value(true),
        )
        .arg(
            Arg::with_name("context")
                .short("c")
                .long("context")
                .value_name("CONTEXT")
                .help("The given code context")
                .required(true)
                .takes_value(true),
        )
        .arg(
            Arg::with_name("current-line-num")
                .short("l")
                .long("current-line")
                .value_name("CURRENT_LINE")
                .help("The current code line number")
                .required(true)
                .takes_value(true),
        )
        .arg(
            Arg::with_name("starting-block-line-num")
                .short("s")
                .long("starting-block-line-num")
                .value_name("STARTING_BLOCK_LINE_NUM")
                .help("The starting line number for the surrounding block")
                .required(true)
                .takes_value(true),
        )
        .arg(
            Arg::with_name("ending-block-line-num")
                .short("e")
                .long("ending-block-line-num")
                .value_name("ENDING_BLOCK_LINE_NUM")
                .help("The ending line number for the queried block")
                .required(true)
                .takes_value(true),
        )
        .get_matches();

    let filepath = cli.value_of("filepath").unwrap();
    let context = cli.value_of("context").unwrap();
    let current = cli
        .value_of("current-line-num")
        .unwrap()
        .parse::<usize>()
        .unwrap();
    let start = cli
        .value_of("starting-block-line-num")
        .unwrap()
        .parse::<usize>()
        .unwrap();
    let end = cli
        .value_of("ending-block-line-num")
        .unwrap()
        .parse::<usize>()
        .unwrap();

    generate_ollama(filepath, context, current, start, end).await
}
