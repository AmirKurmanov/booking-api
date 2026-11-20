from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from database import Base, engine, get_db
from models import Resource, Booking
from sqlalchemy import select
from sqlalchemy.orm import Session
import models

 

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

class BookingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    resource_id: int
    start: datetime
    end: datetime    


class ResourceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    capacity: int

app = FastAPI()

Base.metadata.create_all(engine)

@app.get("/health")
def root():
    return {"status": "ok"}


@app.post("/resources", status_code=201, response_model=ResourceRead)
def create_resources(data: ResourceCreate, db: Session = Depends(get_db)):
    existing = db.scalar(select(Resource).where(Resource.name == data.name))
    if existing is not None:
        raise HTTPException(
            status_code=400, 
            detail="Resource with this name already exists"
        )
    resource = Resource(name = data.name, capacity=data.capacity)

    db.add(resource)
    db.commit()
    db.refresh(resource)
    return resource



@app.get("/resources", response_model=list[ResourceRead])
def get_all_resources(db: Session = Depends(get_db)):
    return db.scalars(select(Resource)).all()

           

@app.get("/resources/{resource_id}", response_model=ResourceRead)
def get_resource(resource_id: int, db: Session = Depends(get_db)):
    resource = db.get(Resource, resource_id)
    if resource is None:
        raise HTTPException(status_code=404, detail=f"id: {resource_id} not found")
    return resource

@app.patch("/resources/{resource_id}", response_model=ResourceRead)
def update_resource(resource_id: int, data: ResourceUpdate, db: Session = Depends(get_db)):
    resource = db.get(Resource, resource_id)
    if resource is None:
        raise HTTPException(status_code=404, detail=f"id: {resource_id} not found")

    if data.name is not None:
        other = db.scalar(
            select(Resource).where(Resource.name == data.name, Resource.id != resource_id)
            )
        if other is not None:
            raise HTTPException(status_code=400, detail="Resource with this name already exists")
        resource.name = data.name

    if data.capacity is not None:
        resource.capacity = data.capacity 

    db.commit()
    db.refresh(resource) 
    return resource
        
 
@app.post("/bookings", status_code=201, response_model=BookingRead)
def create_booking(data: BookingCreate, db: Session = Depends(get_db)):
    resource = db.get(Resource, data.resource_id)
    if resource is None:
        raise HTTPException(
            status_code=404, 
            detail="Resource not found"
        )
    if data.start >= data.end:
        raise HTTPException(
            status_code=400, 
            detail="end must be later than start"
        )
    overlap = db.scalar(
        select(Booking).where(
            Booking.resource_id == data.resource_id, 
            Booking.start < data.end, 
            Booking.end > data.start,
        )
    )
    if overlap is not None:
        raise HTTPException(status_code=409, detail="This time slot is already booked")

    booking = Booking(resource_id=data.resource_id, start=data.start, end=data.end)
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking

@app.get("/bookings", response_model=list[BookingRead])
def get_all_bookings(resource_id: int | None = None, db: Session = Depends(get_db)):
    query = select(Booking)
    if resource_id is not None:
        query = query.where(Booking.resource_id == resource_id)
    return db.scalars(query).all()
        

@app.delete("/bookings/{booking_id}", status_code=204)
def remove_booking(booking_id: int, db: Session = Depends(get_db)):
    booking = db.get(Booking, booking_id)
    if booking is None:
        raise HTTPException(
            status_code=404, 
            detail=f"id: {booking_id} not found"
        )
    db.delete(booking)
    db.commit()


@app.delete("/resources/{resource_id}", status_code=204)
def remove_resource(resource_id: int, db: Session = Depends(get_db)):
    resource = db.get(Resource, resource_id)
    if resource is None:
        raise HTTPException(
            status_code=404, 
            detail=f'id: {resource_id} not found'
        )

    has_booking = db.scalar(select(Booking).where(Booking.resource_id ==resource_id))
    if has_booking is not None:
        raise HTTPException(
            status_code=409, 
            detail="Resource has booking, delete them first"
        )
    db.delete(resource)
    db.commit()