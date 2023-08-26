local M = {}

local function create_floating_window()
    local width = math.floor(vim.o.columns * 0.6)
    local height = math.floor(vim.o.lines * 0.3)

    local row = math.floor((vim.o.lines - height) * 0.5)
    local col = math.floor((vim.o.columns - width) * 0.5)

    local buf = vim.api.nvim_create_buf(false, true)
    local win = vim.api.nvim_open_win(buf, true, {
        relative = 'editor',
        width = width,
        height = height,
        row = row,
        col = col,
        style = 'minimal'
    })

    return buf, win
end

M.interactive_llama = function()
    local buf, win = create_floating_window()

    -- Start terminal in the buffer with your binary
    vim.api.nvim_buf_call(buf, function()
        vim.cmd(string.format('term %s', '~/.local/share/nvim/llama.cpp/main -t 10 -ngl 32 -m ~/.local/share/nvim/llama.cpp/models/codellama-13b.Q4_K_M.gguf --color -c 4096 --temp 0.7 --repeat_penalty 1.1 -n -1 -i -ins'))
    end)
end

vim.cmd [[
  command! Llama lua require'nvim-llama'.interactive_llama()
]]

return M

