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
cap = cv2.VideoCapture(1)
cap.set(3, 640)
cap.set(4, 480)

# Intentos de fijar parámetros de la cámara
cap.set(70, 0.0)                 # WB (puede o no funcionar en tu cámara)
cap.set(39, 0.25)                # Exposición (puede o no funcionar)
cap.set(cv2.CAP_PROP_SATURATION, 150)
cap.set(cv2.CAP_PROP_BRIGHTNESS, 100)

if not cap.isOpened():
    print("No se pudo abrir la cámara")
    exit()

# =========================
# PARÁMETROS GENERALES
# =========================
AREA_MIN = 500      # filtro de ruido (área mínima para considerar un bloque)
ESCALA = 0.9        # 90% del tamaño original

# Colores BGR para dibujar los contornos por etiqueta
colores_bgr = {
    "Rojo":     (0, 0, 255),
    "Naranja":  (0, 128, 255),
    "Amarillo": (0, 255, 255),
    "Cafe":     (19, 69, 139),
    "Verde":    (0, 255, 0),
    "Azul":     (255, 0, 0)
}

# Mapeo etiqueta → instrumento (por ahora solo Azul = Kick)
instrumentos = {
    "Azul": "Kick",
    # "Rojo": "Snare",
    # "Naranja": "Tom",
    # "Amarillo": "Perc",
    # "Cafe": "Low Perc",
    # "Verde": "Hi-Hat"
}

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
# CLASIFICACIÓN POR COLOR (COLOR AVERAGING)
# =========================
def clasificar_color(h, s, v):
    """
    Recibe H, S, V promedio del bloque (0-179, 0-255, 0-255)
    y regresa una etiqueta: "Rojo", "Naranja", "Amarillo",
    "Cafe", "Verde", "Azul" o None si no clasifica.
    """

    # Ignorar zonas muy apagadas o casi grises
    if v < 40 or s < 40:
        return None

    # AZUL
    if 90 <= h <= 130:
        return "Azul"

    # VERDE
    if 50 <= h <= 85:
        return "Verde"

    # ZONA ROJO/NARANJA/AMARILLO/CAFÉ (H bajo)
    # Aquí usamos también V para diferenciar café (más oscuro)
    if 0 <= h < 10:
        # Muy oscuro → Café
        if v < 120:
            return "Cafe"
        return "Rojo"

    if 10 <= h < 20:
        # Oscuro → Café, claro → Naranja
        if v < 120:
            return "Cafe"
        return "Naranja"

    if 20 <= h < 32:
        # Amarillo típico
        return "Amarillo"

    # Si no cae en ningún rango útil
    return None

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
    # DETECCIÓN GENERAL DE COLORES (MÁSCARA GLOBAL)
    # ----------------------------
    # Filtro general: píxeles con cierta saturación y brillo (para ignorar fondo gris/oscuro)
    lower_all = np.array([0, 60, 40], dtype=np.uint8)
    upper_all = np.array([179, 255, 255], dtype=np.uint8)
    mask_all = cv2.inRange(hsv, lower_all, upper_all)

    contornos, _ = cv2.findContours(mask_all, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    azul_en_barra = False  # ¿la barra está cruzando algún bloque azul?

    for c in contornos:
        area = cv2.contourArea(c)
        if area < AREA_MIN:
            continue

        x, y, w, h = cv2.boundingRect(c)

        # ROI de HSV y su máscara local
        roi_hsv = hsv[y:y + h, x:x + w]
        roi_mask = mask_all[y:y + h, x:x + w]

        # HSV promedio dentro del bloque usando la máscara
        h_mean, s_mean, v_mean, _ = cv2.mean(roi_hsv, mask=roi_mask)
        h_mean = int(h_mean)
        s_mean = int(s_mean)
        v_mean = int(v_mean)

        etiqueta_color = clasificar_color(h_mean, s_mean, v_mean)
        if etiqueta_color is None:
            continue

        # Color para dibujar
        color_bgr = colores_bgr.get(etiqueta_color, (255, 255, 255))

        # Dibujar rectángulo de color alrededor del objeto
        cv2.rectangle(frame, (x, y), (x + w, y + h), color_bgr, 3)

        # Texto: instrumento (si existe) o etiqueta de color
        etiqueta_texto = instrumentos.get(etiqueta_color, etiqueta_color)
        cv2.putText(frame, etiqueta_texto, (x, y - 10),
                    cv2.FONT_HERSHEY_DUPLEX, 1, color_bgr, 2)

        # --- SI ES AZUL, CHECAR INTERSECCIÓN CON LA BARRA ---
        if etiqueta_color == "Azul":
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
