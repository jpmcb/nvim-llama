local window = require("nvim-llama.window")
local settings = require("nvim-llama.settings")
local ollama = require("nvim-llama.ollama")
local ollamactl = require("nvim-llama.ollamactl")

local M = {}

M.interactive_llama = function()
	local command = ollama.run(settings.current.model)

	window.create_chat_window()
	vim.fn.termopen(command)
end

local function trim(s)
	return s:match("^%s*(.-)%s*$")
end

local function set_commands()
	vim.api.nvim_create_user_command("Llama", function()
		M.interactive_llama()
	end, {})
end

local function is_docker_installed()
	local handle = io.popen("docker --version 2>&1")
	local result = handle:read("*a")
	handle:close()

	return result:match("Docker version")
end

local function is_docker_running()
	local handle = io.popen("docker info > /dev/null 2>&1; echo $?")
	local result = handle:read("*a")
	handle:close()

	return result:match("0\n")
end

local function check_docker()
	if not is_docker_installed() then
		error("Docker is not installed. Docker is required for nvim-llama")
		return false
	end

	if not is_docker_running() then
		error("Docker is not running. ")
		return false
	end

	return true
end

local function async(command, args, callback)
	vim.loop.spawn(command, { args = args }, function(code)
		if code == 0 then
			callback(true)
		else
			callback(false)
		end
	end)
end

local function is_container_running()
	local command = string.format("docker ps --filter 'name=^/nvim-llama$' --format '{{.Names}}'")
	local handle = io.popen(command)
	local result = trim(handle:read("*a"))
	handle:close()

	return result == "nvim-llama"
end

local function check_ollama_container()
	local container_name = "nvim-llama"

	local exists_command = string.format("docker ps -a --filter 'name=^/nvim-llama$' --format '{{.Names}}'")
	local exists_handle = io.popen(exists_command)
	local exists_result = trim(exists_handle:read("*a"))
	exists_handle:close()

	if exists_result == "nvim-llama" then
		if not is_container_running() then
			-- Remove the stopped container and re-run a new one
			local handle = io.popen("docker rm " .. container_name)
			handle:close()
			ollama.start()
		end
	else
		-- start a new container as non by name exists
		ollama.start()
	end

	return true
end

function M.setup(config)
	if config then
		settings.set(config)
	end

	local status, err = pcall(check_docker)
	if not status then
		print("Error checking docker status: " .. err)
	end

	status, err = pcall(check_ollama_container)
	if not status then
		print("Error checking docker status: " .. err)
	end

	set_commands()
	ollamactl.setup()
end

return M
