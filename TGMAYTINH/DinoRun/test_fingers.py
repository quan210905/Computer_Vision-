import cv2
import mediapipe as mp

mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

cap = cv2.VideoCapture(0)
hands = mp_hands.Hands(max_num_hands=1)

def count_fingers(hand_landmarks):
    tips = [8, 12, 16, 20]  # Đầu ngón trỏ, giữa, áp út, út
    count = 0

    # 4 ngón tay (trừ ngón cái)
    for tip in tips:
        if hand_landmarks.landmark[tip].y < hand_landmarks.landmark[tip - 2].y:
            count += 1

    # Ngón cái
    if hand_landmarks.landmark[4].x < hand_landmarks.landmark[3].x:
        count += 1

    return count

while True:
    ret, frame = cap.read()
    frame = cv2.flip(frame, 1)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(rgb)

    finger_count = 0

    if result.multi_hand_landmarks:
        for hand in result.multi_hand_landmarks:
            mp_draw.draw_landmarks(frame, hand, mp_hands.HAND_CONNECTIONS)
            finger_count = count_fingers(hand)

    # Hiển thị số ngón tay
    cv2.putText(frame, f"Fingers: {finger_count}", (10, 50),
                cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 3)

    cv2.imshow("Finger Counter", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()