local os = require('os')
local home = os.getenv('HOME')

-- Check if a file or directory exists at a given path
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

local M = {}

function M.prepare()
    local ollama_dir = home .. '/.ollama'
    local ok, err = dir_exists(ollama_dir)
    if not ok then
        os.execute('mkdir ' .. ollama_dir)
        print('Created .ollama directory at ' .. ollama_dir)
    end
end

function M.restart()
    M.prepare()
    local restart_command = "docker restart nvim-llama"

    local handle, err = io.popen(restart_command)
    local result = handle:read("*a")
    handle:close()

    if err then
        error("Failed to restart Ollama container: " .. err)
    end
end

function M.start()
    M.prepare()
    local start_command = "docker run -d -p 11434:11434 -v " .. home .. "/.ollama:/root/.ollama --name nvim-llama ollama/ollama"
    local handle, err = io.popen(start_command)
    local result = handle:read("*a")
    handle:close()

    if err then
        error("Failed to start Ollama container: " .. err)
    end
end

function M.run(model)
    return "docker exec -it nvim-llama ollama run " .. model
end

function M.list()
    return "docker exec -it nvim-llama ollama list"
end

return M
