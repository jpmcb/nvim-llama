# 🦙 nvim-llama

_[Llama 2](https://ai.meta.com/llama/) and [llama.cpp](https://github.com/ggerganov/llama.cpp/) interfaces for Neovim_

🏗️ 👷 Warning! Under active development!! 👷 🚧

# Installation

Use your favorite package manager to install the plugin:

### Packer

```lua
  use 'jpmcb/nvim-llama'
```

### lazy.nvim

```lua
{
    'jpmcb/nvim-llama'
}
```

### vim-plug

```lua
Plug 'jpmcb/nvim-llama'
```

# Setup & configuration

In your `init.vim`, setup the plugin:

```lua
require('nvim-llama').setup {}
```

You can provide the following optional configuration table to the `setup` function:

```lua
local defaults = {
    -- See plugin debugging logs
    debug = false,

    -- Build llama.cpp for GPU acceleration on Apple M chip devices.
    -- If you are using an Apple M1/M2 laptop, it is highly recommended to
    -- use this since, depending on the model, may drastically increase performance.
    build_metal = false,
}
```

# Models

Llama.cpp supports an incredible number of models.

To start using one, you'll need to download an appropriately sized model that
is supported by llama.cpp.

The 13B GGUF CodeLlama model is a really good place to start:
https://huggingface.co/TheBloke/CodeLlama-13B-GGUF

In order to use a model, it must be in the `llama.cpp/models/` directory which
is expected to be found at `~/.local/share/llama.cpp/models`.

The following script can be useful for downloading a model to that directory:

```sh
LLAMA_CPP="~/.local/share/nvim/llama.cpp"
MODEL="codellama-13b.Q4_K_M.gguf"

pushd "${LLAMA_CPP}"
    if [ ! -f models/${MODEL} ]; then
        curl -L "https://huggingface.co/TheBloke/CodeLlama-13B-GGUF/resolve/main/${MODEL}" -o models/${MODEL}
    fi
popd
```

In the future, this project may provide the capability to download models automatically.

# License

This project is dual licensed under [MIT](./LICENSE.txt) (first party plugin code)
and the [Llama 2 license](./LICENSE.llama.txt).
By using this plugin, you agree to both terms and assert you have already have
[your own non-transferable license for Llama 2 from Meta AI](https://ai.meta.com/resources/models-and-libraries/llama-downloads/).
