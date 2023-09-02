#!/bin/bash

# This is an example convenience script to demonstrate downloading the 13b GGUF 
# model for llama.cpp from Huggingface.
#
# It drops the model into the expected directory for nvim-llama and llama.cpp to
# be able to utilize it

LLAMA_CPP_CLONE="~/.local/share/nvim/llama.cpp"
MODEL="codellama-13b.Q4_K_M.gguf"

pushd "${LLAMA_CPP_CLONE}"
    if [ ! -f models/${MODEL} ]; then
        curl -L "https://huggingface.co/TheBloke/CodeLlama-13B-GGUF/resolve/main/${MODEL}" -o models/${MODEL}
    fi
popd
