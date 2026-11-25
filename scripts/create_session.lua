local session_key = KEYS[1]
local user_id = ARGV[1]
local ttl = tonumber(ARGV[2])

redis.call("SET", session_key, user_id, "EX", ttl)

return 1
