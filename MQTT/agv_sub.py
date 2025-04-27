import paho.mqtt.client as mqtt
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# MQTT Configuration
MQTT_BROKER = "192.168.102.11"
MQTT_PORT = 1883
MQTT_KEEPALIVE = 60
MQTT_TOPIC = "AGVRoute/#"  # Using wildcard to receive all AGVRoute messages

def bytes_to_hex(byte_array):
    """Convert bytes to a hex string representation with spaces between bytes"""
    if isinstance(byte_array, bytes) or isinstance(byte_array, bytearray):
        return ' '.join(f'{b:02X}' for b in byte_array)
    return ""

def decode_mqtt_hex_payload(payload):
    """Decode binary payload directly"""
    try:
        # Convert payload to list of integers
        hex_bytes = list(payload)
        
        # Extract frame start, frame length, message type
        frame_start = hex_bytes[0]
        frame_length = hex_bytes[1]
        message_type = hex_bytes[2]
        
        # Check start and end markers
        if frame_start != 122:  # 0x7A
            logger.error(f"Invalid start mark: {frame_start}, expected 122")
            return None
            
        if hex_bytes[-1] != 127:  # 0x7F
            logger.error(f"Invalid end mark: {hex_bytes[-1]}, expected 127")
            return None
        
        # Commands start from index 3
        commands_bytes = hex_bytes[3:-1]  # Exclude end marker
        
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
        
        logger.info(f"Signal Type: {message_type}")
        logger.info(f"Frame Length: {frame_length}")
        logger.info("Commands:")
        for i, cmd in enumerate(commands, 1):
            logger.info(f"Command {i}: {cmd}")
        
        return commands
    except Exception as e:
        logger.error(f"Error decoding payload: {e}")
        return None

# MQTT callback functions
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logger.info(f"Connected with result code {rc}")
        # Subscribe to the topic when connection is established
        client.subscribe(MQTT_TOPIC)
        logger.info(f"Subscribed to topic: {MQTT_TOPIC}")
    else:
        logger.error(f"Failed to connect with result code {rc}")

def on_message(client, userdata, msg):
    logger.info(f"Received message on topic {msg.topic}")
    try:
        # Get the raw binary payload
        payload = msg.payload
        
        # Convert to hex string for logging
        hex_payload = bytes_to_hex(payload)
        logger.info(f"Received hex payload: {hex_payload}")
        
        # Decode the binary payload
        decoded_commands = decode_mqtt_hex_payload(payload)
        
        if decoded_commands:
            logger.info("Decoded Commands:")
            logger.info(decoded_commands)
        else:
            logger.warning("Failed to decode the payload")
            
    except Exception as e:
        logger.error(f"Error processing message: {e}")

def start_mqtt_client():
    # MQTT client setup
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    # Connect to the MQTT broker
    logger.info(f"Connecting to {MQTT_BROKER}:{MQTT_PORT}")
    
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, MQTT_KEEPALIVE)
        # Start the network loop to process network traffic and callbacks
        client.loop_forever()
    except Exception as e:
        logger.error(f"Error connecting to MQTT broker: {e}")

if __name__ == "__main__":
    logger.info("Starting MQTT Decoder")
    start_mqtt_client()
