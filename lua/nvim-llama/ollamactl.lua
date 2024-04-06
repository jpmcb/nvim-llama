local M = {}

-- Function to call CLI with current line and surrounding block
local function callOllamactl(filepath, line, block_start, block_end)
	local cmd = string.format(
		"~/.nvim-llama/bin/nvllamactl generate -f %s -l %s -s %s -e %s -u open-ai",
		filepath,
		line,
		block_start,
		block_end
	)
	print(cmd)

	return vim.fn.system(cmd)
end

local function findBlockBounds()
	local cursor = vim.api.nvim_win_get_cursor(0)
	local cursor_line = cursor[1]
	local block_start = 0
	local block_end = vim.fn.line("$")

	if cursor_line - 5 > block_start then
		block_start = cursor_line - 5
	end

	if cursor_line + 5 < block_end then
		block_end = cursor_line + 5
	end

	return cursor_line, block_start, block_end
end

-- Function to display suggestions
function M.displaySuggestions()
	-- Get current line and surrounding block
	local cursor_line, block_start, block_end = findBlockBounds()
	local filepath = vim.fn.bufname("%")

	-- Call CLI and capture output
	local output = callOllamactl(filepath, cursor_line, block_start, block_end)

	-- Display suggestions
	--if output and #output > 0 then
	---- Show suggestions in a floating window
	--local buf = vim.api.nvim_create_buf(false, true)
	--vim.api.nvim_buf_set_option(buf, "bufhidden", "wipe")
	--vim.pi.nvim_buf_set_lines(buf, 0, -1, false, output)
	--local opts = {
	--style = "minimal",
	--relative = "cursor",
	--row = 1,
	--col = 0,
	--width = math.max(unpack(vim.tbl_map(function(l)
	--return #l
	--end, output))) + 4,
	--height = #output,
	--focusable = false,
	--}
	--local win = vim.api.nvim_open_win(buf, false, opts)
	--vim.api.nvim_win_set_option(win, "winblend", 10)
	--end
end

local bufnr = vim.api.nvim_create_buf(false, true) -- Create a new buffer for the window
local win_id = nil -- Keep track of the window ID

local suggestions_open = false

function M.toggle_window()
	if suggestions_open then
		-- Close the horizontal split window
		vim.cmd("silent! :q") -- Closes the current window. Adjust if you have a more complex setup.
		suggestions_open = false
	else
		-- Open a new horizontal split window at the bottom
		local height = 10 -- Height of the suggestions window
		vim.cmd("botright split")
		vim.cmd("resize " .. height)
		vim.api.nvim_win_set_buf(0, bufnr) -- Set the current window to display the buffer with suggestions
		suggestions_open = true
	end
end

--function M.toggle_window()
--if win_id and vim.api.nvim_win_is_valid(win_id) then
---- If the window exists and is valid, close it
--vim.api.nvim_win_close(win_id, true)
--win_id = nil
--else
---- Otherwise, create and show the window
--local width = vim.api.nvim_get_option("columns") - 4 -- Window width
--local height = 10 -- Window height
--local opts = {
--relative = "editor",
--width = width,
--height = height,
--col = 2,
--row = vim.api.nvim_get_option("lines") - height - 2,
--anchor = "SW",
--style = "minimal",
--border = "rounded",
--}
--win_id = vim.api.nvim_open_win(bufnr, true, opts)
--end
--end

function M.set_keymaps()
	vim.api.nvim_buf_set_keymap(
		bufnr,
		"n",
		"<Enter>",
		":lua accept_suggestion()<CR>",
		{ noremap = true, silent = true }
	)
	vim.api.nvim_buf_set_keymap(bufnr, "n", "<Esc>", ":lua toggle_window()<CR>", { noremap = true, silent = true })
end

function M.show_suggestions(suggestions)
	vim.api.nvim_buf_set_lines(bufnr, 0, -1, false, suggestions)
end

function M.accept_suggestion()
	-- Get the current line number in the buffer
	local line_num = vim.api.nvim_win_get_cursor(win_id)[1]
	local lines = vim.api.nvim_buf_get_lines(bufnr, line_num - 1, line_num, false)
	if #lines == 0 then
		return
	end -- No selection made

	local selected_suggestion = lines[1]
	-- Now `selected_suggestion` contains the text of the chosen suggestion
	-- Assuming you want to insert the suggestion at the current cursor position in the active buffer

	local current_buf = vim.api.nvim_get_current_buf()
	local cursor_pos = vim.api.nvim_win_get_cursor(0)
	local row, col = cursor_pos[1], cursor_pos[2]

	-- Insert the suggestion. This example simply inserts the text at the current cursor position.
	vim.api.nvim_buf_set_text(current_buf, row - 1, col, row - 1, col, { selected_suggestion })
end

function M.setup()
	vim.api.nvim_create_user_command("TestLlama", function()
		M.displaySuggestions()
	end, {})

	vim.api.nvim_create_user_command("LlamaToggle", function()
		M.toggle_window()
	end, {})
end

return M
