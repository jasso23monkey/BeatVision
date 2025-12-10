import cv2
import numpy as np

# ============================
# Funciones auxiliares
# ============================
def nada(x):
    pass

# ============================
# Configuración de la cámara
# ============================
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH,  640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

# Intenta desactivar el balance de blancos automático (Usando el valor numérico 70)
# Si tu OpenCV no lo soporta, esta línea simplemente no hará efecto.
cap.set(70, 0.0) 

# Intenta desactivar la exposición automática (Usando el valor numérico 39)
# 0.25 = modo manual/prioridad de apertura; 1.0 = modo manual/fijo
cap.set(39, 0.25)

# Propiedades más comunes
cap.set(cv2.CAP_PROP_SATURATION, 150)  # Fija la saturación a un valor medio/alto
cap.set(cv2.CAP_PROP_BRIGHTNESS, 100)  # Fija el brillo

if not cap.isOpened():
    print("No se pudo abrir la cámara")
    exit()

# ============================
# Ventanas y trackbars
# ============================
cv2.namedWindow("Calibracion HSV")
cv2.resizeWindow("Calibracion HSV", 400, 300)

# Valores iniciales (puedes ajustar si quieres otro punto de partida)
cv2.createTrackbar("H_min", "Calibracion HSV", 0,   179, nada)
cv2.createTrackbar("H_max", "Calibracion HSV", 179, 179, nada)
cv2.createTrackbar("S_min", "Calibracion HSV", 0,   255, nada)
cv2.createTrackbar("S_max", "Calibracion HSV", 255, 255, nada)
cv2.createTrackbar("V_min", "Calibracion HSV", 0,   255, nada)
cv2.createTrackbar("V_max", "Calibracion HSV", 255, 255, nada)

print("Calibrador HSV listo.")
print("Coloca el objeto/pieza frente a la cámara y ajusta los sliders.")
print("Pulsa 'p' para imprimir los valores actuales en consola.")
print("Pulsa 'q' o 'ESC' para salir.")

while True:
    ret, frame = cap.read()
    if not ret:
        print("Error al leer la cámara.")
        break

    # Convertir a HSV
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # Leer posiciones de las trackbars
    h_min = cv2.getTrackbarPos("H_min", "Calibracion HSV")
    h_max = cv2.getTrackbarPos("H_max", "Calibracion HSV")
    s_min = cv2.getTrackbarPos("S_min", "Calibracion HSV")
    s_max = cv2.getTrackbarPos("S_max", "Calibracion HSV")
    v_min = cv2.getTrackbarPos("V_min", "Calibracion HSV")
    v_max = cv2.getTrackbarPos("V_max", "Calibracion HSV")

    # Construir los límites
    lower = np.array([h_min, s_min, v_min])
    upper = np.array([h_max, s_max, v_max])

    # Máscara
    mask = cv2.inRange(hsv, lower, upper)

    # Resultado aplicado a la imagen original
    resultado = cv2.bitwise_and(frame, frame, mask=mask)

    # Mostrar ventanas
    cv2.imshow("Camara", frame)
    cv2.imshow("Mascara", mask)
    cv2.imshow("Resultado", resultado)

    key = cv2.waitKey(1) & 0xFF

    # 'p' para imprimir valores actuales
    if key == ord('p'):
        print(f"HSV_min = [{h_min}, {s_min}, {v_min}]")
        print(f"HSV_max = [{h_max}, {s_max}, {v_max}]")
        print("-" * 40)

    # 'q' o ESC para salir
    if key == ord('q') or key == 27:
        break

cap.release()
cv2.destroyAllWindows()
