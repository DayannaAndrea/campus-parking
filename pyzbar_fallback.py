"""
Decodificador de códigos QR basado en OpenCV.
Se nombró 'pyzbar_fallback' porque reemplaza a pyzbar (requiere libzbar del
sistema, no disponible en todos los equipos del salón) sin cambiar la firma
que usa app/validator.py.
"""
import cv2


def decode_qr(ruta_imagen: str):
    img = cv2.imread(ruta_imagen)
    if img is None:
        return None
    detector = cv2.QRCodeDetector()
    data, points, _ = detector.detectAndDecode(img)
    return data or None
