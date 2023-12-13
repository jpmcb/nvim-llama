local M = {}

M.create_chat_window = function ()
    -- Split the window vertically and set size
    vim.cmd("vsplit")
    vim.cmd("vertical resize 80")

    -- Open a new buffer in the split window
    local buf = vim.api.nvim_create_buf(false, true)
    vim.api.nvim_win_set_buf(0, buf)

    -- Set a few options for the new buffer
    vim.api.nvim_win_set_option(0, 'number', false)
    vim.api.nvim_win_set_option(0, 'relativenumber', false)

    return buf
end

return M
