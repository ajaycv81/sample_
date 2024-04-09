
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
import sqlite3
import math
import uvicorn
from commanConstant import ServerDetails

app = FastAPI()

class Address(BaseModel):
    id: Optional[int] = None
    street: str
    city: str
    country: str
    latitude: float
    longitude: float

def connect_db():
    conn = sqlite3.connect('addresses.db')
    cursor = conn.cursor()
    return conn, cursor

def create_table():
    conn, cursor = connect_db()
    cursor.execute('''CREATE TABLE IF NOT EXISTS addresses
                      (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      street TEXT,
                      city TEXT,
                      country TEXT,
                      latitude REAL,
                      longitude REAL)''')
    conn.commit()
    conn.close()

def validate_coordinates(latitude: float, longitude: float):
    if not (-90 <= latitude <= 90) or not (-180 <= longitude <= 180):
        raise HTTPException(status_code=400, detail="Invalid coordinates")

@app.post("/addresses/", response_model=Address)
def create_address(address: Address):
    validate_coordinates(address.latitude, address.longitude)
    conn, cursor = connect_db()
    cursor.execute('''INSERT INTO addresses (street, city, country, latitude, longitude)
                      VALUES (?, ?, ?, ?, ?)''',
                   (address.street, address.city, address.country, address.latitude, address.longitude))
    conn.commit()
    address.id = cursor.lastrowid
    conn.close()
    return address

@app.put("/addresses/{address_id}", response_model=Address)
def update_address(address_id: int, address: Address):
    validate_coordinates(address.latitude, address.longitude)
    conn, cursor = connect_db()
    cursor.execute('''UPDATE addresses
                      SET street=?, city=?, country=?, latitude=?, longitude=?
                      WHERE id=?''',
                   (address.street, address.city, address.country, address.latitude, address.longitude, address_id))
    conn.commit()
    conn.close()
    return address

@app.delete("/addresses/{address_id}")
def delete_address(address_id: int):
    conn, cursor = connect_db()
    cursor.execute('''DELETE FROM addresses WHERE id=?''', (address_id,))
    conn.commit()
    conn.close()
    return {"message": "Address deleted"}

@app.get("/addresses/", response_model=List[Address])
def get_addresses(latitude: float, longitude: float, distance: Optional[float] = Query(..., ge=0)):
    validate_coordinates(latitude, longitude)
    conn, cursor = connect_db()
    cursor.execute('''SELECT * FROM addresses''')
    addresses = cursor.fetchall()
    filtered_addresses = []
    for addr in addresses:
        if calculate_distance(latitude, longitude, addr[4], addr[5]) <= distance:
            filtered_addresses.append({"id": addr[0], "street": addr[1], "city": addr[2], "country": addr[3],
                                       "latitude": addr[4], "longitude": addr[5]})
    conn.close()
    return filtered_addresses

def calculate_distance(latitude_1: float, longitude_1: float, latitude_2: float, longitude_2: float) -> float:
    
    radius_of_earth = 6371  # Radius_of_earth of the Earth in kilometers
    distance_latitude = math.radians(latitude_2 - latitude_1)
    distance_longitude = math.radians(longitude_2 - longitude_1)
    # Haversine formula to calculate distance between two points on Earth
    a = math.sin(distance_latitude / 2) * math.sin(distance_latitude / 2) + math.cos(math.radians(latitude_1)) * math.cos(math.radians(latitude_2)) * math.sin(distance_longitude / 2) * math.sin(distance_longitude / 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = radius_of_earth * c
    return distance

if __name__ == "__main__":
    create_table()
    uvicorn.run(app="main:app", host=ServerDetails.host.value , port= ServerDetails.port.value , reload= True)