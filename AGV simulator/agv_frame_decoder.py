# agv_frame_decoder.py
# Thư viện để giải mã frame dữ liệu AGV dạng hexa.

# --- Hằng số định nghĩa Frame (cần thiết cho việc giải mã) ---
FRAME_START_BYTE = 0x7A
FRAME_END_BYTE = 0x7F
EXPECTED_FRAME_LENGTH_VALUE = 0x08 
EXPECTED_HEX_STRING_LENGTH = EXPECTED_FRAME_LENGTH_VALUE * 2

class FrameDecodeError(Exception):
    """Lỗi tùy chỉnh cho các vấn đề khi giải mã frame."""
    pass

def decode_hex_frame_to_agv_data(hex_frame: str) -> dict:
    """
    Giải mã một chuỗi hexa thành dữ liệu AGV (agv_id, current_node).
    Message Type vẫn được đọc từ frame nhưng không được trả về trong dictionary.

    Cấu trúc frame (chuỗi hexa 16 ký tự, tương ứng 8 bytes):
    - Byte 0: Frame Start   (0x7A)
    - Byte 1: Frame Length  (0x08 - tổng độ dài frame)
    - Byte 2: Message Type  (được đọc nhưng không trả về)
    - Byte 3-4: Current Node  (2 bytes, big-endian)
    - Byte 5-6: AGV ID        (2 bytes, big-endian)
    - Byte 7: Frame End     (0x7F)

    Args:
        hex_frame (str): Chuỗi hexa đại diện cho frame dữ liệu (ví dụ: "7A0802001100017F").

    Returns:
        dict: Một dictionary chứa {'agv_id': int, 'current_node': int}
              nếu giải mã thành công.
    Raises:
        FrameDecodeError: Nếu frame không hợp lệ.
    """
    if not isinstance(hex_frame, str):
        raise FrameDecodeError("Lỗi giải mã: Đầu vào không phải là chuỗi.")
    
    hex_frame = hex_frame.strip().upper()

    if len(hex_frame) != EXPECTED_HEX_STRING_LENGTH:
        raise FrameDecodeError(
            f"Lỗi giải mã: Độ dài chuỗi hexa không hợp lệ. "
            f"Mong đợi {EXPECTED_HEX_STRING_LENGTH} ký tự, nhận được {len(hex_frame)} ('{hex_frame}')."
        )

    try:
        frame_bytes = bytes.fromhex(hex_frame)
    except ValueError:
        raise FrameDecodeError(
            f"Lỗi giải mã: Chuỗi hexa '{hex_frame}' không hợp lệ (chứa ký tự không phải hexa)."
        )

    if frame_bytes[0] != FRAME_START_BYTE:
        raise FrameDecodeError(
            f"Lỗi giải mã: Byte bắt đầu không hợp lệ. "
            f"Mong đợi {FRAME_START_BYTE:#04x}, nhận được {frame_bytes[0]:#04x}."
        )
    if frame_bytes[-1] != FRAME_END_BYTE:
        raise FrameDecodeError(
            f"Lỗi giải mã: Byte kết thúc không hợp lệ. "
            f"Mong đợi {FRAME_END_BYTE:#04x}, nhận được {frame_bytes[-1]:#04x}."
        )

    frame_length_from_payload = frame_bytes[1]
    if frame_length_from_payload != EXPECTED_FRAME_LENGTH_VALUE:
        raise FrameDecodeError(
            f"Lỗi giải mã: Giá trị Frame Length trong payload không hợp lệ. "
            f"Mong đợi {EXPECTED_FRAME_LENGTH_VALUE:#04x}, nhận được {frame_length_from_payload:#04x}."
        )

    # message_type = int(frame_bytes[2]) # Vẫn đọc byte này nhưng không dùng
    current_node = int.from_bytes(frame_bytes[3:5], byteorder='big')
    agv_id = int.from_bytes(frame_bytes[5:7], byteorder='big')

    return {
        "agv_id": agv_id,
        "current_node": current_node
    }

# --- Phần kiểm tra ---
if __name__ == "__main__":
    print("--- Kiểm tra thư viện agv_frame_decoder (không trả về message_type) ---")
    
    test_frames = {
        "Hợp lệ (AGV 1, Node 17)": "7A0802001100017F", # message_type 0x02 vẫn có trong frame
        "Hợp lệ (AGV 258, Node 513)": "7A0805020101027F", # message_type 0x05 vẫn có trong frame
    }

    for description, frame_str in test_frames.items():
        print(f"\nĐang kiểm tra: {description}")
        print(f"  Input Frame Hexa: '{frame_str}'")
        try:
            data = decode_hex_frame_to_agv_data(frame_str)
            print(f"  Kết quả giải mã: {data}")
            if "AGV 1" in description:
                assert data['agv_id'] == 1 and data['current_node'] == 17
                assert "message_type" not in data # Kiểm tra không có message_type
                print("    => Kiểm tra giá trị (AGV 1, Node 17): OK")
            elif "AGV 258" in description:
                assert data['agv_id'] == 258 and data['current_node'] == 513
                assert "message_type" not in data
                print("    => Kiểm tra giá trị (AGV 258, Node 513): OK")
        except FrameDecodeError as e:
            print(f"  Lỗi giải mã (FrameDecodeError): {e}")
        except Exception as e:
            print(f"  Lỗi không mong muốn: {e}")