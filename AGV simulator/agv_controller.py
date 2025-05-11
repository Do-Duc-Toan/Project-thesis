import paho.mqtt.client as mqtt
import json
import time
import threading
import sys
import traceback # Để in traceback đầy đủ nếu có lỗi khác

try:
    # Đảm bảo import đúng tên hàm và lớp lỗi từ file decoder của bạn
    from agv_frame_decoder import decode_hex_frame_to_agv_data, FrameDecodeError
except ImportError:
    print("LỖI: Không thể import thư viện agv_frame_decoder.py.")
    sys.exit(1)


MQTT_BROKER = "localhost" # MQTT broker address
MQTT_PORT = 1883
AGV_DATA_TOPIC_PREFIX = "agv_data/"
AGV_ROUTE_TOPIC_PREFIX = "agv_route/"
NUMBER_OF_AGVS = 3

current_agv_nodes = {}
data_lock = threading.Lock()

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Controller: Connected to MQTT Broker!")
        sys.stdout.flush()
        client.subscribe(f"{AGV_DATA_TOPIC_PREFIX}#")
        print(f"Controller: Subscribed to topics under '{AGV_DATA_TOPIC_PREFIX}#'")
        sys.stdout.flush()
    else:
        print(f"Controller: Failed to connect, return code {rc}\n")
        sys.stdout.flush()

def on_message(client, userdata, msg):
    topic = msg.topic
    raw_payload_bytes = msg.payload
    hex_payload_received = ""

    print("\n-------------------------")
    sys.stdout.flush()

    try:
        hex_payload_received = raw_payload_bytes.decode('utf-8')
        print(f"Topic: {topic}")
        print(f"Raw Payload (Hex String): {hex_payload_received}")
        sys.stdout.flush()

        decoded_data = decode_hex_frame_to_agv_data(hex_payload_received)
        
        agv_id = decoded_data.get("agv_id")
        current_node = decoded_data.get("current_node")
        # message_type không còn được trả về từ decode_hex_frame_to_agv_data

        # Kiểm tra xem agv_id và current_node có thực sự được trả về không
        if agv_id is None or current_node is None:
            print(f"[MQTT Callback] Controller: Lỗi - Dữ liệu giải mã bị thiếu agv_id hoặc current_node.")
            print(f"[MQTT Callback] Decoded data: {decoded_data}")
            sys.stdout.flush()
            raise ValueError("Dữ liệu giải mã từ frame bị thiếu trường cần thiết.")

        with data_lock:
            current_agv_nodes[int(agv_id)] = int(current_node)
        
        # Sửa dòng print để không còn dùng message_type
        print(f"Information: AGV {agv_id} is at node {current_node}.")
        
    except FrameDecodeError as fde:
        print(f"Controller: Lỗi giải mã frame: '{hex_payload_received}'. Chi tiết: {fde}")
    except UnicodeDecodeError:
        print(f"Controller: Lỗi giải mã payload - không phải UTF-8. Payload bytes: {raw_payload_bytes}")
    except Exception as e:
        print(f"Controller: Lỗi không xác định khi xử lý message (payload '{hex_payload_received}'):")
        traceback.print_exc()
    # finally:
    #     print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>\n")
    #     sys.stdout.flush()

# ... (Các hàm get_user_command và command_input_loop giữ nguyên như trước) ...
def get_user_command(agv_id_to_command):
    print(f"\n--- Enter command for AGV {agv_id_to_command} ---")
    sys.stdout.flush()
    motion_state = -1
    next_node = 0 
    direction_change = 0 

    while True:
        try:
            motion_state_str = input(f"  Enter Motion State for AGV {agv_id_to_command} (0:IDLE, 1:MOVING, 2:WAITING): ")
            sys.stdout.flush()
            motion_state = int(motion_state_str)
            if motion_state not in [0, 1, 2]:
                raise ValueError("Invalid motion state. Must be 0, 1, or 2.")
            break
        except ValueError as e:
            print(f"Error: {e}. Please enter a valid integer.")
            sys.stdout.flush()

    if motion_state == 1: 
        while True:
            try:
                next_node_str = input(f"  Enter Next Node for AGV {agv_id_to_command} (e.g., '10'): ")
                sys.stdout.flush()
                next_node = int(next_node_str.strip())
                break
            except ValueError as e:
                print(f"Error: {e}. Please enter a single valid node number (e.g., '10').")
                sys.stdout.flush()

        while True:
            try:
                direction_change_str = input(f"  Enter Direction Change for AGV {agv_id_to_command} (0:STRAIGHT, 1:AROUND, 2:LEFT, 3:RIGHT): ")
                sys.stdout.flush()
                direction_change = int(direction_change_str)
                if direction_change not in [0, 1, 2, 3]:
                    raise ValueError("Invalid direction change. Must be 0, 1, 2, or 3.")
                break
            except ValueError as e:
                print(f"Error: {e}. Please enter a valid integer.")
                sys.stdout.flush()
    else: 
        print(f"  Motion state is {motion_state}. No further input needed for next_node or direction_change.")
        sys.stdout.flush()
        
    command_payload = {
        "motion_state": motion_state,
        "next_node": next_node,
        "direction_change": direction_change
    }
    return command_payload

def command_input_loop(client):
    time.sleep(1) 
    print("\nController: Type AGV ID (e.g., '1') to command, or 'quit' to exit.")
    sys.stdout.flush()
    
    running = True
    while running:
        with data_lock:
            if current_agv_nodes:
                print("\nCurrent AGV Status:")
                for agv_id_status, node_status in sorted(current_agv_nodes.items()):
                    print(f"  AGV {agv_id_status} is at node {node_status}")
        sys.stdout.flush()
        
        try:
            action = input("> Controller action: ") 
            sys.stdout.flush()
        except EOFError: 
            print("Controller: No input stream, exiting command loop.")
            running = False; continue
        except KeyboardInterrupt: 
            print("\nController: Keyboard interrupt detected. Exiting...")
            running = False; continue
        
        if action.lower() == 'quit':
            print("Controller: Exiting..."); running = False; continue
        
        try:
            target_agv_id = int(action)
            if not (1 <= target_agv_id <= NUMBER_OF_AGVS): 
                print(f"Controller: Invalid AGV ID. Please enter a number between 1 and {NUMBER_OF_AGVS}.")
                sys.stdout.flush(); continue

            command_to_send = get_user_command(target_agv_id)
            publish_topic = f"{AGV_ROUTE_TOPIC_PREFIX}{target_agv_id}"
            
            client.publish(publish_topic, json.dumps(command_to_send), qos=1)
            print(f"Controller: Sent command to AGV {target_agv_id} on topic '{publish_topic}': {json.dumps(command_to_send)}")
            print("------------------------------------")
            sys.stdout.flush()

        except ValueError: 
            print("Controller: Invalid input. Please enter a valid AGV ID (number) or 'quit'.")
            sys.stdout.flush()
        except Exception as e: 
            print(f"Controller: An error occurred: {e}")
            sys.stdout.flush()

if __name__ == "__main__":
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, client_id=f"agv_controller_fallback_{int(time.time())}")
    client.on_connect = on_connect
    client.on_message = on_message

    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
    except Exception as e:
        print(f"Controller: Could not connect to MQTT Broker: {e}")
        sys.stdout.flush(); exit()

    client.loop_start() 

    try:
        command_input_loop(client) 
    except Exception as e: 
        print(f"Error in command input loop: {e}")
        sys.stdout.flush()
    finally: 
        print("Controller: Shutting down MQTT client...")
        sys.stdout.flush()
        client.loop_stop()
        client.disconnect()
        print("Controller: Disconnected and shutdown.")
        sys.stdout.flush()