def decode_mqtt_hex_payload(hex_payload):
    # Convert hex string to list of integers
    hex_bytes = [int(b, 16) for b in hex_payload.split()]
    
    # Extract frame start, frame length, message type
    frame_start = hex_bytes[0]
    frame_length = hex_bytes[1]
    message_type = hex_bytes[2]
    
    # Commands start from index 3
    commands_bytes = hex_bytes[3:]
    
    # Each command is 5 bytes, decode each command
    commands = []
    for i in range(0, len(commands_bytes), 5):
        cmd_bytes = commands_bytes[i:i+5]
        if len(cmd_bytes) < 5:
            break
            
        # Decode LSB order for first 2 bytes for first_node
        first_node = cmd_bytes[0] + (cmd_bytes[1] << 8)
        
        # 3rd byte is action
        action = cmd_bytes[2]
        
        # 4th and 5th bytes for wait_time (LSB order)
        wait_time = cmd_bytes[3] + (cmd_bytes[4] << 8)
        
        # Convert wait_time to float seconds (assuming unit is milliseconds)
        wait_time_sec = wait_time / 1000.0
        
        # Add command as array [first_node, action, wait_time_sec]
        commands.append([first_node, action, wait_time_sec])
    
    print(f"Signal Type: {message_type}")
    print(f"Frame Length: {frame_length}")
    print("Commands:")
    for i, cmd in enumerate(commands, 1):
        print(f"Command {i}: {cmd}")
    
    return commands

# Example usage with the provided hex payload
hex_payload = "7A 40 03 01 00 02 00 00 04 00 03 00 00 05 00 01 00 00 08 00 01 00 00 0B 00 01 00 00 10 00 01 00 00 0B 00 01 00 00 08 00 02 00 00 05 00 01 00 00 04 00 03 00 00 03 00 01 00 00 00 00 00 00 00 7F"

decoded_commands = decode_mqtt_hex_payload(hex_payload)
print("\nDecoded Commands:")
print(decoded_commands)
print(decoded_commands[0][0])  # Example to access the first command's action


