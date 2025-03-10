local M = {}

M.namespace = vim.api.nvim_create_namespace("nvim-llama")

local defaults = {
    -- See plugin debugging logs
    debug = false,
    docker = true,
    ollama_host = "localhost",
    ollama_port = "11434",

    -- the model to use with Ollama.
    model = 'llama3',
}

M.current = defaults

function M.set(opts)
  M.current = vim.tbl_deep_extend("force", defaults, opts or {})
end

return M
