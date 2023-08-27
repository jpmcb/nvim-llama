local config = require("nvim-llama.config")

local repo_url = 'https://github.com/ggerganov/llama.cpp.git'
local target_dir ='~/.local/share/nvim/llama.cpp'
local repo_sha = 'b1095'

local M = {}

--- Check if a file or directory exists at path
-- Attribution: https://stackoverflow.com/questions/1340230/check-if-directory-exists-in-lua
function dir_exists(target_dir)
   local ok, err, code = os.rename(target_dir, target_dir)

   if not ok then
      if code == 13 then
         -- Permission denied, but it exists
         return true
      end
   end

   return ok, err
end

-- Checks if llama.cpp directory exists at expected location
local function clone_repo_command(repo_url, target_dir, sha)
    local ok, err = dir_exists(target_dir)

    if not ok then
        local clone_cmd = string.format("git clone %s %s", repo_url, target_dir)
        local checkout_cmd = string.format("git -C %s checkout %s", target_dir, sha)

        return clone_cmd .. ' && ' .. checkout_cmd
    end

    return
end

local function build_make_command(target_dir, opts)
    local build_string = ''
    local metal_build = 'make'

    if opts.metal_build then
        metal_build = 'LLAMA_METAL=1'
    end

    build_string = metal_build .. ' ' .. build_string

    -- Navigate to the repo directory and build using make
    return string.format("cd %s && %s", target_dir, build_string)
end

function M.rebuild()
    print('Rebuilding llama.cpp')
    build_make(target_dir, config.options)
end

function M.install()
    vim.cmd('vsplit')
    vim.cmd('enew')

    local clone_repo = clone_repo_command(repo_url, target_dir, repo_sha)
    local build_make = build_make_command(target_dir, config.options)
    local commands = clone_repo .. ' && ' .. build_make

    vim.fn.termopen(commands)

    -- There's a UI/UX rough edge here where the opened vsplit window doesn't
    -- automatically scroll to the bottom. I.e., it can be confusing for users
    -- if they don't intuitively scroll to the bottom of the buffer to see build
    -- output from llama.cpp

    vim.cmd('vertical resize 60')
end

return M
