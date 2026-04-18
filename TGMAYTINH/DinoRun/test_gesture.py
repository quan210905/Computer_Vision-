import cv2
import mediapipe as mp

mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

cap = cv2.VideoCapture(0)
hands = mp_hands.Hands(max_num_hands=1)

def count_fingers(hand_landmarks):
    tips = [8, 12, 16, 20]
    count = 0
    for tip in tips:
        if hand_landmarks.landmark[tip].y < hand_landmarks.landmark[tip - 2].y:
            count += 1
    if hand_landmarks.landmark[4].x < hand_landmarks.landmark[3].x:
        count += 1
    return count

def get_action(finger_count):
    actions = {
        0: "SHIELD",    # Nắm tay → phòng thủ
        1: "MOVE",      # 1 ngón → di chuyển
        2: "JUMP",      # 2 ngón → nhảy
        3: "FIREBALL",  # 3 ngón → bắn fireball
        5: "ROAR",      # Mở cả tay → skill mạnh
    }
    return actions.get(finger_count, "IDLE")

while True:
    ret, frame = cap.read()
    frame = cv2.flip(frame, 1)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(rgb)

    finger_count = 0
    action = "IDLE"

    if result.multi_hand_landmarks:
        for hand in result.multi_hand_landmarks:
            mp_draw.draw_landmarks(frame, hand, mp_hands.HAND_CONNECTIONS)
            finger_count = count_fingers(hand)
            action = get_action(finger_count)

    # Hiển thị
    cv2.putText(frame, f"Fingers: {finger_count}", (10, 50),
                cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 2)
    cv2.putText(frame, f"Action: {action}", (10, 100),
                cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 200, 255), 2)

    cv2.imshow("Gesture Test", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()