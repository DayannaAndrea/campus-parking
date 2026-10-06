"""
Decodificador de códigos QR basado en OpenCV.
Se nombró 'pyzbar_fallback' porque reemplaza a pyzbar (requiere libzbar del
sistema, no disponible en todos los equipos del salón) sin cambiar la firma
que usa app/validator.py.

Estabilización: el detector básico de OpenCV falla con algunos QR según su
tamaño/versión, así que se prueban varias estrategias en orden (detector
Aruco, imagen original, escalas y borde blanco) hasta que una lea el código.
"""
import cv2


def _variantes(img):
    gris = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img
    yield gris
    yield cv2.resize(gris, None, fx=0.5, fy=0.5, interpolation=cv2.INTER_AREA)
    conborde = cv2.copyMakeBorder(gris, 40, 40, 40, 40, cv2.BORDER_CONSTANT, value=255)
    yield cv2.resize(conborde, None, fx=2, fy=2, interpolation=cv2.INTER_NEAREST)
    yield cv2.resize(gris, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    _, bin_ = cv2.threshold(gris, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    yield bin_


def decode_qr(ruta_imagen: str):
    img = cv2.imread(ruta_imagen)
    if img is None:
        return None
    detectores = [cv2.QRCodeDetector()]
    if hasattr(cv2, "QRCodeDetectorAruco"):
        detectores.insert(0, cv2.QRCodeDetectorAruco())
    for variante in [img, *_variantes(img)]:
        for det in detectores:
            try:
                data, _, _ = det.detectAndDecode(variante)
            except cv2.error:
                continue
            if data:
                return data
    return None
