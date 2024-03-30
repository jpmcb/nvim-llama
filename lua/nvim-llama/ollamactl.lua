local M = {}

-- Function to call CLI with current line and surrounding block
local function callOllamactl(context, line, block_start, block_end, filepath)
	local cmd = string.format(
		'~/.nvim-llama/bin/ollamactl -c "%s" -l %s -s %s -e %s -f %s',
		context,
		line,
		block_start,
		block_end,
		filepath
	)
	print(cmd)
	return vim.fn.systemlist(cmd)
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
local function displaySuggestions()
	-- Get current line and surrounding block
	local cursor_line, block_start, block_end = findBlockBounds()
	local filepath = vim.fn.bufname("%")

	-- Call CLI and capture output
	local output = callOllamactl("", cursor_line, block_start, block_end, filepath)

	-- Display suggestions
	if output and #output > 0 then
		-- Show suggestions in a floating window
		local buf = vim.api.nvim_create_buf(false, true)
		vim.api.nvim_buf_set_option(buf, "bufhidden", "wipe")
		vim.api.nvim_buf_set_lines(buf, 0, -1, false, output)
		local opts = {
			style = "minimal",
			relative = "cursor",
			row = 1,
			col = 0,
			width = math.max(unpack(vim.tbl_map(function(l)
				return #l
			end, output))) + 4,
			height = #output,
			focusable = false,
		}
		local win = vim.api.nvim_open_win(buf, false, opts)
		vim.api.nvim_win_set_option(win, "winblend", 10)
	end
end

function M.setCommand()
	vim.api.nvim_create_user_command("TestLlama", function()
		displaySuggestions()
	end, {})
end

return M
