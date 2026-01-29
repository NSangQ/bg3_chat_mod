-- BG3 Chat Mod - Main Script
-- Requires Norbyte's Script Extender v56+

Ext.Utils.Print("[BG3ChatMod] Loaded successfully.")

-- Configuration
local chatInputFile = "bg3_chat_input.json"
local chatOutputFile = "bg3_chat_output.json"
local lastProcessedTime = 0
local targetLanguage = "Korean" -- Options: "Korean", "English", "Spanish", etc.

-- Helper: Get the main player UUID
local function GetPlayerUuid()
    return Osi.GetHostCharacter()
end

-- Helper: Calculate distance between two entities
local function GetDistance(uuid1, uuid2)
    local pos1 = Ext.Entity.Get(uuid1).Translate
    local pos2 = Ext.Entity.Get(uuid2).Translate
    
    local dx = pos1[1] - pos2[1]
    local dy = pos1[2] - pos2[2]
    local dz = pos1[3] - pos2[3]
    
    return math.sqrt(dx*dx + dy*dy + dz*dz)
end

-- Helper: Find the closest party member (excluding self)
local function GetClosestCompanion(playerUuid)
    local party = Osi.DB_PartyMembers:Get(nil)
    local closestUuid = nil
    local minDist = 999999
    
    for i, entry in pairs(party) do
        local memberUuid = entry[1]
        if memberUuid ~= playerUuid then
            local dist = GetDistance(playerUuid, memberUuid)
            if dist < minDist then
                minDist = dist
                closestUuid = memberUuid
            end
        end
    end
    
    return closestUuid
end

-- Helper: Get Entity Name
local function GetName(uuid)
    -- Try to get the translated display name
    local name = Osi.GetDisplayName(uuid)
    if not name or name == "" then
        -- Fallback to internal template name if translation fails
        name = Ext.Entity.Get(uuid).DisplayName
    end
    return name
end

-- Main Chat Handler
local function OnChatInput(idx, message)
    -- Check for prefix
    if string.sub(message, 1, 4) ~= "/ai " then
        return
    end

    local playerUuid = GetPlayerUuid()
    local userContent = string.sub(message, 5)
    
    -- 1. Identify Target (Closest Companion)
    local targetUuid = GetClosestCompanion(playerUuid)
    
    if not targetUuid then
        Ext.Utils.Print("[BG3ChatMod] No companion found nearby.")
        return
    end

    local targetName = GetName(targetUuid)
    Ext.Utils.Print("[BG3ChatMod] Conversing with: " .. targetName)

    -- 2. Gather Real Context
    local attitude = Osi.GetAttitude(targetUuid, playerUuid) or 0
    local region = "Unknown"
    local entity = Ext.Entity.Get(targetUuid)
    
    if entity and entity.Level then
        region = entity.Level.LevelName -- e.g., "WLD_Main_A"
    end
    
    local inCombat = (Osi.IsInCombat(targetUuid) == 1)
    
    -- 3. Prepare Data
    local payload = {
        speaker = targetName,       -- The character we want the AI to be
        user = "Player",            -- The player's name (could get real name too)
        content = userContent,      -- What the player typed
        context = {
            language = targetLanguage, -- Added Language Preference
            approval = attitude,
            location = region,
            in_combat = inCombat,
            is_romanced = (Osi.IsTagged(targetUuid, "d2165b4d-5c62-432a-a035-779836337340") == 1), -- Check generic dating tag (Example UUID)
            target_uuid = targetUuid -- Pass UUID for potential callback
        },
        timestamp = Ext.Utils.MonotonicTime()
    }

    -- 4. Write to File
    Ext.IO.SaveFile(chatInputFile, Ext.Json.Stringify(payload))
    Ext.Utils.Print("[BG3ChatMod] Request sent to AI.")
end

-- Register Chat Listener
-- Note: 'InputConsole' is often used for commands. 
-- If relying on in-game chat box, we hook into the game's UI functions or verify SE's Chat event.
-- For reliability in this prototype, we treat it as a Console Command via Script Extender Console 
-- OR we try to hook the UI. Let's assume standard Lua console listener first for safety.
Ext.RegisterConsoleCommand("ai", function(cmd, ...)
    local args = {...}
    local message = "/ai " .. table.concat(args, " ")
    OnChatInput(nil, message)
end)

-- Polling for Response (Simple implementation)
local function CheckResponse()
    local content = Ext.IO.LoadFile(chatOutputFile)
    if content and content ~= "" then
        local data = Ext.Json.Parse(content)
        if data and data.response and data.timestamp ~= lastProcessedTime then
            
            -- Display Overhead Text
            if data.context and data.context.target_uuid then
                Osi.ShowOverheadText(data.context.target_uuid, data.response)
                Ext.Utils.Print("[AI] " .. data.speaker .. ": " .. data.response)
            end
            
            lastProcessedTime = data.timestamp
        end
    end
end

-- Register Tick for Polling (Low frequency to save performance)
Ext.Events.Tick:Subscribe(function(e)
    if e.Time.Time % 60 == 0 then -- Check roughly every second (assuming 60 ticks/sec)
        CheckResponse()
    end
end)