import cv2
import numpy as np
import pygame

print('Librerías leídas')

# =========================
# INICIALIZAR PYGAME (SONIDO)
# =========================
pygame.mixer.init()

# Carga tu sonido para el color azul
sonido_azul = pygame.mixer.Sound("assets/sounds/azul.wav")
sonando_azul = False  # bandera para saber si ya está sonando

# =========================
# CÁMARA
# =========================
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

# Diccionario de colores (rangos)
colores = {
    "Amarillo": (amarillo_osc, amarillo_cla),
    "Rojo":     (rojo_osc, rojo_cla),
    "Verde":    (verde_osc, verde_cla),
    "Azul":     (azul_osc, azul_cla)
}

# Colores BGR para dibujar los contornos
colores_bgr = {
    "Amarillo": (0, 255, 255),
    "Rojo":     (0, 0, 255),
    "Verde":    (0, 255, 0),
    "Azul":     (255, 0, 0)
}

# Mapear color → “instrumento” (por ahora solo Azul = Kick)
instrumentos = {
    "Azul": "Kick"
    # "Rojo": "Snare",
    # "Verde": "Hi-Hat",
    # "Amarillo": "Perc"
}

AREA_MIN = 5000  # filtro de ruido

# =========================
# BARRA Y BPM
# =========================
x_barra = 0              # posición inicial de la barra
ancho_barra = 15         # ancho de la barra
BPM = 120                # bpm inicial
velocidad = 12           # pixeles por frame (se ajusta con BPM)
moviendo = False         # bandera de movimiento automático

def nada(x):
    pass

def actualizar_velocidad():
    global velocidad, BPM
    # Mapeo sencillo: más BPM => más rápido
    velocidad = max(1, BPM // 10)

# Crear ventana principal y trackbar de BPM en la MISMA ventana
cv2.namedWindow("BeatVision")
cv2.createTrackbar("BPM", "BeatVision", BPM, 200, nada)

# Inicializar velocidad acorde al BPM inicial
actualizar_velocidad()

# =========================
# LOOP PRINCIPAL
# =========================
while True:
    ret, frame = cap.read()
    if not ret:
        print("Error al leer la cámara")
        break

    # Voltear imagen (modo espejo)
    frame = cv2.flip(frame, 1)

    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    alto, ancho = frame.shape[:2]

    # Leer BPM desde el trackbar
    bpm_val = cv2.getTrackbarPos("BPM", "BeatVision")
    if bpm_val < 40:
        bpm_val = 40       # BPM mínimo razonable
        cv2.setTrackbarPos("BPM", "BeatVision", bpm_val)
    BPM = bpm_val
    actualizar_velocidad()

    # ----------------------------
    # ACTUALIZAR POSICIÓN SI ESTÁ MOVIENDO
    # ----------------------------
    if moviendo:
        x_barra += velocidad
        if x_barra > ancho:
            x_barra = 0

    # ----------------------------
    # DIBUJAR LA BARRA NEGRA
    # ----------------------------
    cv2.rectangle(frame, (x_barra, 0), (x_barra + ancho_barra, alto), (0, 0, 0), -1)

    # ----------------------------
    # DETECCIÓN DE COLORES
    # ----------------------------
    azul_en_barra = False  # ¿la barra está cruzando algún azul?

    for nombre, (bajo, alto_hsv) in colores.items():
        mask = cv2.inRange(hsv, bajo, alto_hsv)
        contornos, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for c in contornos:
            area = cv2.contourArea(c)
            if area > AREA_MIN:
                # Rectángulo que encierra el contorno
                x, y, w, h = cv2.boundingRect(c)

                # Color BGR para dibujar
                color_bgr = colores_bgr.get(nombre, (255, 255, 255))

                # Dibujar rectángulo de color alrededor del objeto
                cv2.rectangle(frame, (x, y), (x + w, y + h), color_bgr, 3)

                # Texto: si ese color tiene instrumento, usarlo; si no, usar el nombre del color
                etiqueta = instrumentos.get(nombre, nombre)
                cv2.putText(frame, etiqueta, (x, y - 10),
                            cv2.FONT_HERSHEY_DUPLEX, 1, color_bgr, 2)

                # --- SI ES AZUL, CHECAR INTERSECCIÓN CON LA BARRA ---
                if nombre == "Azul":
                    azul_x_ini = x
                    azul_x_fin = x + w

                    barra_x_ini = x_barra
                    barra_x_fin = x_barra + ancho_barra

                    if barra_x_ini <= azul_x_fin and barra_x_fin >= azul_x_ini:
                        azul_en_barra = True

    # ----------------------------
    # LÓGICA DE SONIDO (SOLO CUANDO LA BARRA PASA POR AZUL)
    # ----------------------------
    if azul_en_barra and not sonando_azul:
        sonido_azul.play(-1)   # loop continuo mientras esté cruzando
        sonando_azul = True

    if not azul_en_barra and sonando_azul:
        sonido_azul.stop()
        sonando_azul = False

    # ----------------------------
    # MOSTRAR VIDEO
    # ----------------------------
    cv2.putText(frame, f"BPM: {BPM}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

    cv2.imshow("BeatVision", frame)

    # ----------------------------
    # LECTURA DE TECLAS
    # ----------------------------
    key = cv2.waitKey(30) & 0xFF

    if key == ord('d'):     # empezar movimiento automático
        moviendo = True

    if key == ord('s'):     # detener movimiento
        moviendo = False

    if key == ord('r'):     # reiniciar la barra
        x_barra = 0

    if key == 27:           # ESC → salir
        break

cap.release()
cv2.destroyAllWindows()
pygame.mixer.quit()
