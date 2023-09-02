local settings = require("nvim-llama.settings")

local repo_url = 'https://github.com/ggerganov/llama.cpp.git'
local target_dir = vim.fn.expand('$HOME/.local/share/nvim/llama.cpp')
local repo_sha = 'b1095'


-- Check if a file or directory exists at path
-- Attribution: https://stackoverflow.com/questions/1340230/check-if-directory-exists-in-lua
local function dir_exists(target)
   local ok, err, code = os.rename(target, target)

   if not ok then
      if code == 13 then
         -- Permission denied, but it exists
         return true
      end
   end

   return ok, err
end

-- Checks if llama.cpp directory exists at expected location
local function clone_repo_command(url, target, sha)
    local ok, err = dir_exists(target)

    if not ok then
        local clone_cmd = string.format("git clone %s %s", url, target)
        local checkout_cmd = string.format("git -C %s checkout %s", target, sha)

        return clone_cmd .. ' && ' .. checkout_cmd
    end

    return ''
end

local function build_make_command(target)
    local build_string = 'make'
    local metal_build = ''

    print(settings.current.build_metal)
    if settings.current.build_metal then
        metal_build = metal_build .. 'LLAMA_METAL=1 '
    end

    build_string = metal_build .. build_string

    -- Navigate to the repo directory and build using make
    return string.format("cd %s && %s", target, build_string)
end

local M = {}

function M.rebuild()
    print('Rebuilding llama.cpp at sha ' .. repo_sha)
    local command = build_make_command(target_dir)
    vim.fn.termopen(command)
end

function M.install()
    vim.cmd('vsplit')
    vim.cmd('enew')

    local commands = ''
    local clone_repo = clone_repo_command(repo_url, target_dir, repo_sha)
    local build_make = build_make_command(target_dir)
    if clone_repo == '' then
        commands = build_make
    else
        commands = clone_repo .. ' && ' .. build_make
    end

    print(commands)

    vim.fn.termopen(commands)

    -- There's a UI/UX rough edge here where the opened vsplit window doesn't
    -- automatically scroll to the bottom. I.e., it can be confusing for users
    -- if they don't intuitively scroll to the bottom of the buffer to see build
    -- output from llama.cpp

    vim.cmd('vertical resize 60')
end

function M.update()
    local ok, err = dir_exists(target_dir)

    if ok then
        local checkout_cmd = string.format("git -C %s checkout %s", target_dir, repo_sha)
        local output = vim.fn.system(checkout_cmd)
        if vim.v.shell_error ~= 0 then
            print("Error checking out llama.cpp at " .. repo_sha)
            print(output)
        else
            print("Checked out llama.cpp at " .. repo_sha)
        end
    else
        print("could not find llama.cpp directory")
    end

    -- TODO: Rebuild as well?
end

return M
