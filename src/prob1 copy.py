import cv2
import numpy as np
import pygame

print('Librerías leídas')

# =========================
# INICIALIZAR PYGAME (SONIDO)
# =========================
pygame.mixer.init()

# Cargar sonidos por color
sonido_azul      = pygame.mixer.Sound("assets/sounds/azul.wav")
sonido_rojo      = pygame.mixer.Sound("assets/sounds/rojo.wav")
sonido_verde     = pygame.mixer.Sound("assets/sounds/verde.wav")
sonido_amarillo  = pygame.mixer.Sound("assets/sounds/amarillo.wav")

# Banderas para saber si ya están sonando
sonando_azul     = False
sonando_rojo     = False
sonando_verde    = False
sonando_amarillo = False

# =========================
# CÁMARA
# =========================
cap = cv2.VideoCapture(1)
cap.set(3, 640)
cap.set(4, 480)

# Intentos de fijar parámetros de la cámara
cap.set(70, 0.0)                 # WB (puede que no funcione en todas las cámaras)
cap.set(39, 0.25)                # Exposición (puede que no funcione siempre)
cap.set(cv2.CAP_PROP_SATURATION, 150)
cap.set(cv2.CAP_PROP_BRIGHTNESS, 100)

if not cap.isOpened():
    print("No se pudo abrir la cámara")
    exit()

# =========================
# RANGOS HSV (tus rangos)
# =========================
amarillo_osc = np.array([10, 120, 100])
amarillo_cla = np.array([40, 255, 255])

rojo_osc = np.array([0, 50, 30])
rojo_cla = np.array([8, 200, 255])

verde_osc = np.array([69, 210, 20])
verde_cla = np.array([175, 255, 148])

azul_osc = np.array([90, 60, 0])
azul_cla = np.array([121, 255, 255])

# Colores BGR para dibujar los contornos
colores_bgr = {
    "Amarillo": (0, 255, 255),
    "Rojo":     (0, 0, 255),
    "Verde":    (0, 255, 0),
    "Azul":     (255, 0, 0)
}

# Mapear color → “instrumento”
instrumentos = {
    "Azul":      "Kick",
    "Rojo":      "Snare",
    "Verde":     "Perc",
    "Amarillo":  "Hi-Hat"
}

AREA_MIN = 500  # filtro de ruido

# =========================
# BARRA Y BPM
# =========================
x_barra = 0              # posición inicial de la barra
ancho_barra = 15         # ancho de la barra
BPM = 120                # bpm inicial
velocidad = 12           # pixeles por frame (se ajusta con BPM)
moviendo = False         # bandera de movimiento automático

ESCALA = 1  # 100% del tamaño original

def nada(x):
    pass

def actualizar_velocidad():
    global velocidad, BPM
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

    # Redimensionar frame
    frame = cv2.resize(frame, None, fx=ESCALA, fy=ESCALA)

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
    # MÁSCARAS POR COLOR
    # ----------------------------
    mask_amarillo = cv2.inRange(hsv, amarillo_osc, amarillo_cla)
    mask_rojo     = cv2.inRange(hsv, rojo_osc, rojo_cla)
    mask_verde    = cv2.inRange(hsv, verde_osc, verde_cla)
    mask_azul     = cv2.inRange(hsv, azul_osc, azul_cla)

    # Resolver solapamiento:
    # PRIORIDAD al ROJO sobre el AMARILLO.
    mask_amarillo = cv2.bitwise_and(mask_amarillo, cv2.bitwise_not(mask_rojo))

    # ----------------------------
    # DETECCIÓN DE COLORES
    # ----------------------------
    # Banderas: ¿la barra está cruzando cada color?
    amarillo_en_barra = False
    rojo_en_barra     = False
    verde_en_barra    = False
    azul_en_barra     = False

    for nombre in ["Amarillo", "Rojo", "Verde", "Azul"]:
        if nombre == "Amarillo":
            mask = mask_amarillo
        elif nombre == "Rojo":
            mask = mask_rojo
        elif nombre == "Verde":
            mask = mask_verde
        elif nombre == "Azul":
            mask = mask_azul
        else:
            continue

        contornos, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for c in contornos:
            area = cv2.contourArea(c)
            if area > AREA_MIN:
                x, y, w, h = cv2.boundingRect(c)

                color_bgr = colores_bgr.get(nombre, (255, 255, 255))

                # Dibujar rectángulo de color alrededor del objeto
                cv2.rectangle(frame, (x, y), (x + w, y + h), color_bgr, 1)

                # Texto: instrumento o nombre de color
                etiqueta = instrumentos.get(nombre, nombre)
                cv2.putText(frame, etiqueta, (x, y - 10),
                            cv2.FONT_HERSHEY_DUPLEX, 0.45, color_bgr, 1)

                # --- CHECAR INTERSECCIÓN CON LA BARRA ---
                color_x_ini = x
                color_x_fin = x + w
                barra_x_ini = x_barra
                barra_x_fin = x_barra + ancho_barra

                if barra_x_ini <= color_x_fin and barra_x_fin >= color_x_ini:
                    if nombre == "Azul":
                        azul_en_barra = True
                    elif nombre == "Rojo":
                        rojo_en_barra = True
                    elif nombre == "Verde":
                        verde_en_barra = True
                    elif nombre == "Amarillo":
                        amarillo_en_barra = True

    # ----------------------------
    # LÓGICA DE SONIDO (CUANDO LA BARRA PASA POR CADA COLOR)
    # ----------------------------

    # AZUL
    if azul_en_barra and not sonando_azul:
        sonido_azul.play(-1)
        sonando_azul = True
    if not azul_en_barra and sonando_azul:
        sonido_azul.stop()
        sonando_azul = False

    # ROJO
    if rojo_en_barra and not sonando_rojo:
        sonido_rojo.play(-1)
        sonando_rojo = True
    if not rojo_en_barra and sonando_rojo:
        sonido_rojo.stop()
        sonando_rojo = False

    # VERDE
    if verde_en_barra and not sonando_verde:
        sonido_verde.play(-1)
        sonando_verde = True
    if not verde_en_barra and sonando_verde:
        sonido_verde.stop()
        sonando_verde = False

    # AMARILLO
    if amarillo_en_barra and not sonando_amarillo:
        sonido_amarillo.play(-1)
        sonando_amarillo = True
    if not amarillo_en_barra and sonando_amarillo:
        sonido_amarillo.stop()
        sonando_amarillo = False

    # ----------------------------
    # MOSTRAR VIDEO
    # ----------------------------
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
