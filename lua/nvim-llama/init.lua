local window = require("nvim-llama.window")

local llama = {}

llama.interactive_llama = function()
    local buf, win = window.create_floating_window()

    -- Start terminal in the buffer with your binary
    vim.api.nvim_buf_call(buf, function()
        vim.cmd(string.format('term %s', '~/.local/share/nvim/llama.cpp/main -t 10 -ngl 32 -m ~/.local/share/nvim/llama.cpp/models/codellama-13b.Q4_K_M.gguf --color -c 4096 --temp 0.7 --repeat_penalty 1.1 -n -1 -i -ins'))
    end)
end

vim.cmd [[
  command! Llama lua require'nvim-llama'.interactive_llama()
  command! LlamaInstall lua require'nvim-llama.install'.install()
  command! LlamaRebuild lua require'nvim-llama.rebuild'.rebuild()
]]

return llama
