# agv_frame_encoder.py
# Thư viện để mã hóa và giải mã (trong tương lai) frame dữ liệu AGV dạng hexa.

import struct

# --- Hằng số định nghĩa Frame ---
FRAME_START_BYTE = 0x7A
FRAME_END_BYTE = 0x7F
DEFAULT_MESSAGE_TYPE = 0x02
DEFAULT_FRAME_LENGTH = 0x08 # Tổng độ dài frame cố định là 8 bytes

# Giới hạn giá trị cho các trường dữ liệu (dựa trên số byte)
MAX_VALUE_1_BYTE = 0xFF    # 255
MAX_VALUE_2_BYTES = 0xFFFF # 65535

class FrameEncodeError(Exception):
    """Lỗi tùy chỉnh cho các vấn đề khi mã hóa frame."""
    pass

def encode_agv_data_to_hex_frame(agv_id: int, current_node: int, message_type: int = DEFAULT_MESSAGE_TYPE) -> str | None:
    """
    Mã hóa dữ liệu AGV thành một chuỗi hexa theo cấu trúc frame định sẵn.

    Cấu trúc frame (8 bytes total):
    - Frame Start   : 1 byte (0x7A)
    - Frame Length  : 1 byte (0x08 - tổng độ dài frame)
    - Message Type  : 1 byte
    - Current Node  : 2 bytes (big-endian)
    - AGV ID        : 2 bytes (big-endian)
    - Frame End     : 1 byte (0x7F)

    Args:
        agv_id (int): ID của AGV.
        current_node (int): Node hiện tại của AGV.
        message_type (int, optional): Loại tin nhắn. Mặc định là DEFAULT_MESSAGE_TYPE.

    Returns:
        str | None: Chuỗi hexa đại diện cho frame dữ liệu (ví dụ: "7A0802001100017F"),
                    hoặc None nếu có lỗi.
    
    Raises:
        FrameEncodeError: Nếu giá trị đầu vào không hợp lệ.
    """
    if not (0 <= agv_id <= MAX_VALUE_2_BYTES):
        raise FrameEncodeError(f"Lỗi: agv_id ({agv_id}) nằm ngoài khoảng cho phép (0-{MAX_VALUE_2_BYTES}).")
    if not (0 <= current_node <= MAX_VALUE_2_BYTES):
        raise FrameEncodeError(f"Lỗi: current_node ({current_node}) nằm ngoài khoảng cho phép (0-{MAX_VALUE_2_BYTES}).")
    if not (0 <= message_type <= MAX_VALUE_1_BYTE):
        raise FrameEncodeError(f"Lỗi: message_type ({message_type}) nằm ngoài khoảng cho phép (0-{MAX_VALUE_1_BYTE}).")

    try:
        frame_bytes = bytearray()
        frame_bytes.append(FRAME_START_BYTE)
        frame_bytes.append(DEFAULT_FRAME_LENGTH) # Frame length cố định là 0x08
        frame_bytes.append(message_type)
        
        # Current Node (2 bytes, big-endian)
        frame_bytes.extend(current_node.to_bytes(2, byteorder='big'))
        
        # AGV ID (2 bytes, big-endian)
        frame_bytes.extend(agv_id.to_bytes(2, byteorder='big'))
        
        frame_bytes.append(FRAME_END_BYTE)
        
        # Chuyển bytearray thành chuỗi hexa chữ hoa
        hex_frame = frame_bytes.hex().upper()
        
        return hex_frame

    except Exception as e:
        # Ghi lại lỗi cụ thể hơn nếu cần, nhưng với kiểm tra đầu vào ở trên, lỗi struct.error ít xảy ra hơn
        raise FrameEncodeError(f"Lỗi không xác định khi đóng gói dữ liệu: {e}")

# --- Phần này để kiểm tra nhanh thư viện khi chạy trực tiếp file ---
if __name__ == "__main__":
    print("--- Kiểm tra thư viện agv_frame_encoder ---")
    
    # Ví dụ 1: Dữ liệu hợp lệ
    try:
        agv1_id = 1
        node1 = 17
        hex_frame1 = encode_agv_data_to_hex_frame(agv1_id, node1)
        if hex_frame1:
            print(f"\nVí dụ 1 (Hợp lệ):")
            print(f"  Input: AGV ID={agv1_id}, Current Node={node1}, Message Type={DEFAULT_MESSAGE_TYPE:#04x}")
            print(f"  Frame Hexa: {hex_frame1}")
            print(f"  Frame Hexa (định dạng): {' '.join(hex_frame1[i:i+2] for i in range(0, len(hex_frame1), 2))}")
            # Mong đợi: 7A 08 02 00 11 00 01 7F
    except FrameEncodeError as e:
        print(f"Lỗi ở Ví dụ 1: {e}")

    # Ví dụ 2: current_node quá lớn
    try:
        agv2_id = 2
        node2_invalid = 70000 # Lớn hơn 65535 (0xFFFF)
        print(f"\nVí dụ 2 (current_node không hợp lệ):")
        print(f"  Input: AGV ID={agv2_id}, Current Node={node2_invalid}")
        hex_frame2 = encode_agv_data_to_hex_frame(agv2_id, node2_invalid)
        if hex_frame2:
             print(f"  Frame Hexa: {hex_frame2}")
    except FrameEncodeError as e:
        print(f"  Lỗi: {e}")

    # Ví dụ 3: Thay đổi message_type
    try:
        agv3_id = 3
        node3 = 100
        msg_type3 = 0x05
        hex_frame3 = encode_agv_data_to_hex_frame(agv3_id, node3, msg_type3)
        if hex_frame3:
            print(f"\nVí dụ 3 (Message Type tùy chỉnh):")
            print(f"  Input: AGV ID={agv3_id}, Current Node={node3}, Message Type={msg_type3:#04x}")
            print(f"  Frame Hexa: {hex_frame3}")
            print(f"  Frame Hexa (định dạng): {' '.join(hex_frame3[i:i+2] for i in range(0, len(hex_frame3), 2))}")
            # Mong đợi: 7A 08 05 00 64 00 03 7F (100 dez = 0x64 hex)
    except FrameEncodeError as e:
        print(f"Lỗi ở Ví dụ 3: {e}")