import cv2
import numpy as np

print('Librerías leídas')

cap = cv2.VideoCapture(0)
cap.set(3, 640)
cap.set(4, 480)

if not cap.isOpened():
    print("No se pudo abrir la cámara")
    exit()

# =========================
# RANGOS HSV
# =========================
amarillo_osc = np.array([25, 70, 120])
amarillo_cla = np.array([30, 255, 255])

rojo_osc = np.array([8, 50, 120])
rojo_cla = np.array([10, 255, 255])

verde_osc = np.array([49, 70, 80])
verde_cla = np.array([70, 255, 255])

azul_osc = np.array([90, 60, 0])
azul_cla = np.array([121, 255, 255])

# Diccionario de colores
colores = {
    "Amarillo": (amarillo_osc, amarillo_cla),
    "Rojo":     (rojo_osc, rojo_cla),
    "Verde":    (verde_osc, verde_cla),
    "Azul":     (azul_osc, azul_cla)
}

AREA_MIN = 5000  # filtro de ruido

# =========================
# LOOP PRINCIPAL
# =========================
while True:
    ret, frame = cap.read()
    if not ret:
        print("Error al leer la cámara")
        break

    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    for nombre, (bajo, alto) in colores.items():
        mask = cv2.inRange(hsv, bajo, alto)

        # findContours devuelve (contornos, jerarquía)
        contornos, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for c in contornos:
            area = cv2.contourArea(c)
            if area > AREA_MIN:

                # Evitar división entre cero
                M = cv2.moments(c)
                if M["m00"] == 0:
                    continue

                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])

                # Dibujar punto y etiqueta
                cv2.circle(frame, (cx, cy), 7, (255,255,255), -1)
                cv2.putText(frame, nombre, (cx - 20, cy - 20),
                            cv2.FONT_HERSHEY_DUPLEX, 2, (255,255,255), 2)

    cv2.imshow("Video", frame)
    key = cv2.waitKey(1)

    if key == 27:  # ESC
        break

cap.release()
cv2.destroyAllWindows()
