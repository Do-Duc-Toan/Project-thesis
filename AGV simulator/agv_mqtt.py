# agv_mqtt.py
import paho.mqtt.client as mqtt
import time
import json

from agv_frame_encoder import encode_agv_data_to_hex_frame, FrameEncodeError, DEFAULT_MESSAGE_TYPE

class AGVMQTTClient:
    def __init__(self, broker_address, port, agv_id, initial_node=None):
        self.broker_address = broker_address
        self.port = port
        self.agv_id = int(agv_id) 
        self.client_id = f'agv-client-{self.agv_id}-{int(time.time())}'
        self.publish_topic = f"agv_data/{self.agv_id}" # Change your topic name here
        self.subscribe_topic = f"agv_route/{self.agv_id}" # Change your topic name here
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, client_id=self.client_id)
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect
        
        if initial_node is not None:
            try:
                self.current_node = int(initial_node)
            except ValueError:
                print(f"AGV {self.agv_id}: Lỗi - initial_node '{initial_node}' không phải là số nguyên. Đặt current_node = 0.")
                self.current_node = 0 
        else:
            self.current_node = 0 

        self.new_route_callback = None

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print(f"AGV {self.agv_id}: Connected to MQTT Broker at {self.broker_address}:{self.port}")
            client.subscribe(self.subscribe_topic)
            print(f"AGV {self.agv_id}: Subscribed to topic '{self.subscribe_topic}'")
        else:
            print(f"AGV {self.agv_id}: Failed to connect to MQTT Broker, return code {rc}")

    def _on_disconnect(self, client, userdata, rc):
        print(f"AGV {self.agv_id}: Disconnected from MQTT Broker with result code {rc}.")

    def _on_message(self, client, userdata, msg):
        # Phần này của AGV client (simulator) là để nhận lệnh từ controller.
        # Hiện tại controller đang gửi JSON, nên phần giải mã này vẫn giữ nguyên.
        print(f"AGV {self.agv_id}: Received message on topic '{msg.topic}': {msg.payload.decode()}")
        try:
            payload_data = json.loads(msg.payload.decode()) # Giả sử controller vẫn gửi JSON
            # motion_state = payload_data.get("motion_state") # Lấy từ JSON nếu controller gửi

            if callable(self.new_route_callback):
                # Truyền toàn bộ payload_data để callback có thể lấy motion_state, next_node, etc.
                self.new_route_callback(self.agv_id, payload_data.get("next_node"), payload_data)
            else:
                debug_message = f"AGV {self.agv_id}: Message on '{msg.topic}' issue. "
                if not callable(self.new_route_callback):
                    debug_message += "The new_route_callback is NOT set or not callable. "
                print(debug_message)

        except json.JSONDecodeError:
            print(f"AGV {self.agv_id}: Error decoding JSON from topic '{msg.topic}'. Payload: {msg.payload.decode()}")
        except Exception as e:
            print(f"AGV {self.agv_id}: Error processing message from '{msg.topic}': {e}")

    def connect(self):
        try:
            self.client.connect(self.broker_address, self.port, keepalive=60)
            self.client.loop_start()
            print(f"AGV {self.agv_id}: MQTT client loop started.")
        except ConnectionRefusedError:
            print(f"AGV {self.agv_id}: Connection refused. Ensure MQTT broker is running at {self.broker_address}:{self.port}")
        except Exception as e:
            print(f"AGV {self.agv_id}: Could not connect to MQTT Broker: {e}")

    def disconnect(self):
        if self.client.is_connected():
            self.client.loop_stop()
            self.client.disconnect()
        print(f"AGV {self.agv_id}: Disconnected from MQTT broker.")

    def publish_current_node(self, node_id: int, message_type: int = DEFAULT_MESSAGE_TYPE):
        """
        Mã hóa và gửi thông tin node hiện tại của AGV (dưới dạng frame hexa) lên MQTT.
        Simulator hoặc hệ thống điều khiển sẽ gọi hàm này khi AGV đến một node mới.

        Args:
            node_id (int): ID của node hiện tại mà AGV đang ở.
            message_type (int, optional): Loại tin nhắn cho frame. 
                                         Mặc định là DEFAULT_MESSAGE_TYPE từ agv_frame_encoder.
        """
        try:
            self.current_node = int(node_id) # Đảm bảo node_id là int
        except ValueError:
            print(f"AGV {self.agv_id}: Lỗi - node_id '{node_id}' không phải là số nguyên. Không thể publish.")
            return

        try:
            # Sử dụng hàm mã hóa từ thư viện agv_frame_encoder
            # message_type có thể được truyền vào hoặc dùng mặc định
            hex_payload_to_send = encode_agv_data_to_hex_frame(
                agv_id=self.agv_id,
                current_node=self.current_node,
                message_type=message_type # Hoặc một message_type cụ thể nếu bạn muốn phân biệt
            )

            if hex_payload_to_send is None:
                # Lỗi đã được in ra bởi encode_agv_data_to_hex_frame nếu nó trả về None do FrameEncodeError
                # Hoặc bạn có thể print thêm ở đây nếu muốn
                print(f"AGV {self.agv_id}: Không thể tạo frame hexa để publish.")
                return

            if self.client.is_connected():
                # Gửi chuỗi hexa trực tiếp. MQTT client sẽ tự động encode thành UTF-8 (mặc định)
                # nếu payload là string.
                result = self.client.publish(self.publish_topic, hex_payload_to_send, qos=1)
                
                if result.rc == mqtt.MQTT_ERR_SUCCESS:
                    # In ra chuỗi hexa
                    formatted_hex_for_log = ' '.join(hex_payload_to_send[i:i+2] for i in range(0, len(hex_payload_to_send), 2))
                    print(f"AGV {self.agv_id}: Published HEX '{formatted_hex_for_log}' to topic '{self.publish_topic}'")
                else:
                    print(f"AGV {self.agv_id}: Failed to publish HEX to '{self.publish_topic}', result code {result.rc}")
            else:
                print(f"AGV {self.agv_id}: Cannot publish HEX, MQTT client not connected.")
        
        except FrameEncodeError as fee: 
            print(f"AGV {self.agv_id}: Lỗi khi mã hóa frame để publish: {fee}")
        except Exception as e:
            print(f"AGV {self.agv_id}: Lỗi không xác định khi publishing message: {e}")

    def set_new_route_callback(self, callback):
        self.new_route_callback = callback

if __name__ == "__main__":
    
    print("--- Chạy thử nghiệm AGVMQTTClient (không kết nối broker thật) ---")
    
    # Tạo một mock callback
    def mock_route_handler(agv_id, next_node, full_payload):
        print(f"[MOCK SIM] AGV {agv_id} nhận lệnh. Next Node: {next_node}. Payload: {full_payload}")

    # Khởi tạo client (sẽ không kết nối thật)
    test_agv_id_client = AGVMQTTClient("localhost", 1883, agv_id=99, initial_node=1)
    test_agv_id_client.set_new_route_callback(mock_route_handler) # Đặt callback

    print("\nThử publish node 5, message type 0x02 (mặc định):")
    test_agv_id_client.publish_current_node(node_id=5) 
    # Mong đợi: 7A0802000500637F (99 dec = 63 hex)
    # Sẽ thấy print ra lỗi không kết nối, và nếu kết nối thì sẽ print frame hexa.

    print("\nThử publish node 10, message type 0x0A:")
    test_agv_id_client.publish_current_node(node_id=10, message_type=0x0A)
    # Mong đợi: 7A080A000A00637F

    # Thử publish với node_id không hợp lệ (quá lớn)
    print("\nThử publish node_id quá lớn (70000):")
    test_agv_id_client.publish_current_node(node_id=70000)

    print("\n--- Kết thúc thử nghiệm AGVMQTTClient ---")