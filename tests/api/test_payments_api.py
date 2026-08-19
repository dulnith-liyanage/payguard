from fastapi.testclient import TestClient
from PIL import Image, ImageDraw
from io import BytesIO
from app.main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_get_payments_list():
    response = client.get("/api/payments/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_upload_payment():
    img = Image.new('RGB', (300, 150), color='white')
    draw = ImageDraw.Draw(img)
    draw.text((20, 30), "Total Amount: 25000\nAccount: 100200300\nRef: 839201", fill='black')
    buf = BytesIO()
    img.save(buf, format='JPEG')
    buf.seek(0)

    response = client.post(
        "/api/payments/upload",
        data={"order_id": 1},
        files={"file": ("slip.jpg", buf, "image/jpeg")}
    )
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["status"] == "success"
    assert "payment_id" in res_data
