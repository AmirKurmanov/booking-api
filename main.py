from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime

resources = [
    {
        "resource_id": 1, "name": "Переговорка А", "capacity": 6    
    },
    {
        "id": 2, "name": "Переговорка Б", "capacity": 10
    },
]

bookings = [
    {
        "id": 1,
        "resource_id": 1,
        "start": datetime(2026, 11, 20, 10, 0),
        "end": datetime(2026, 11, 20, 11, 0),
    },
    {
        "id": 2,
        "resource_id": 2,
        "start": datetime(2026, 11, 20, 10, 0),
        "end": datetime(2026, 11, 20, 12, 0),
    },
]

class ResourceCreate(BaseModel):
    name: str
    capacity: int

class BookingCreate(BaseModel):
    resource_id: int
    start: datetime
    end: datetime

class ResourceUpdate(BaseModel):
    name: str | None = None
    capacity: int | None = None

app = FastAPI()


@app.get("/health")
def root():
    return {"status": "ok"}


@app.post("/resources", status_code=201)
def create_resources(data: ResourceCreate):
    for resource in resources:
        if resource["name"] == data.name:
            raise HTTPException(status_code=400, detail="Resource with this name already exists")

    new_id = len(resources) + 1

    new_resource = {
        "id": new_id, 
        "name": data.name, 
        "capacity": data.capacity 
    }
    resources.append(new_resource)

    return new_resource



@app.get("/resources")
def get_all_resources():
    return resources

           

@app.get("/resources/{resource_id}")
def get_id(resource_id: int | None = None):
    for resource in resources:
        if resource["id"] == resource_id: 
            return resource
    raise HTTPException(status_code=404, detail=f"id:{resource_id} not found")

@app.patch("/resources/{resource_id}")
def update_resource(resource_id: int, data: ResourceUpdate):
    for resource in resources:
        if resource["id"] == resource_id:
            if data.name is not None:
                for other in resources:
                    if other["name"] == data.name and other["id"] != resource_id:
                        raise HTTPException(
                            status_code=400, 
                            detail="Resource with this name already exists"
                    )
                resource["name"] = data.name

            if data.capacity is not None:
                resource["capacity"] = data.capacity

            return resource

    raise HTTPException(
        status_code=404, 
        detail=f"id: {resource_id} not found"
    )
 
@app.post("/bookings", status_code=201)
def create_booking(data: BookingCreate):
    found = False
    for resource in resources:
        if resource["id"] == data.resource_id:
            found = True
            break
    if not found:    
        raise HTTPException(
            status_code=404, 
            detail="NOT FOUND"
        )

    if data.end <= data.start:
        raise HTTPException(
            status_code=400, 
            detail="BAD REQUEST"
        )

    for booking in bookings:
        if (
    booking["resource_id"] == data.resource_id
    and data.start < booking["end"]
    and data.end > booking["start"]
):
            raise HTTPException(
                status_code=409, 
                detail="This time slot is already booked"
            )

    new_booking = {
        "id": len(bookings) + 1, 
        "resource_id": data.resource_id,
        "start": data.start, 
        "end": data.end
    }
    bookings.append(new_booking)

    return new_booking
            
@app.get("/bookings")
def get_all_bookings(resource_id: int | None = None):
    if resource_id is None:
            return bookings
    result = []
    for booking in bookings:
        if booking["resource_id"] == resource_id:
            result.append(booking)
    return result 
        

@app.delete("/bookings/{booking_id}", status_code=204)
def remove_booking(booking_id: int):
    for i, booking in enumerate(bookings):
        if booking["id"] == booking_id:
            del bookings[i]
            return
    raise HTTPException(
        status_code=404, 
        detail=f"id:{booking_id} not found"
    )

@app.delete("/resources/{resource_id}", status_code=204)
def remove_resource(resource_id: int):
    for i, resource in enumerate(resources):
        if resource["id"] == resource_id:
            for booking in bookings:
                if booking["booking_id"] == resource_id:
                    raise HTTPException(
                        status_code=409,
                        detail="Resource has bookings, delete them first"
                    )
            del resource_id[i]
            return 
    raise HTTPException(
        status_code=404, 
        detail=f"id: {resource_id} not found"
    )