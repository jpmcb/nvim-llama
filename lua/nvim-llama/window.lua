local M = {}

M.create_floating_window = function ()
    local width = math.floor(vim.o.columns * 0.6)
    local height = math.floor(vim.o.lines * 0.8)

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

return M

