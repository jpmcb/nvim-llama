local M = {}

M.namespace = vim.api.nvim_create_namespace("nvim-llama")

local defaults = {
    -- See plugin debugging logs
    debug = false,

    -- Build llama.cpp for GPU acceleration on Apple M chip devices.
    -- If you are using an Apple M1/M2 laptop, it is highly recommended to
    -- use this since, depending on the model, may drastically increase performance.
    build_metal = false,
}

M.current = defaults

function M.set(opts)
  M.current = vim.tbl_deep_extend("force", defaults, opts or {})
end

return M
