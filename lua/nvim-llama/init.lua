local window = require("nvim-llama.window")
local settings = require("nvim-llama.settings")
local llama_cpp = require('nvim-llama.install')

local M = {}

M.interactive_llama = function()
    local buf, win = window.create_floating_window()

    -- Start terminal in the buffer with your binary
    vim.api.nvim_buf_call(buf, function()
        vim.cmd(string.format('term %s', '~/.local/share/nvim/llama.cpp/main -t 10 -ngl 32 -m ~/.local/share/nvim/llama.cpp/models/codellama-13b.Q4_K_M.gguf --color -c 4096 --temp 0.7 --repeat_penalty 1.1 -n -1 -i -ins'))
    end)
end

local function set_commands()
    vim.api.nvim_create_user_command("Llama", function()
        M.interactive_llama()
    end, {})

    vim.api.nvim_create_user_command("LlamaInstall", function()
        llama_cpp.install()
    end, {})

    vim.api.nvim_create_user_command("LlamaRebuild", function()
        llama_cpp.rebuild()
    end, {})

    vim.api.nvim_create_user_command("LlamaUpdate", function()
        llama_cpp.update()
    end, {})
end

function M.setup(config)
    if config then
        settings.set(config)
    end

    set_commands()
end

return M
