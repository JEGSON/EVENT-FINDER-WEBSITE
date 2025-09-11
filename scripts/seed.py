#!/usr/bin/env python3
"""Seed the database with sample events for development."""
from datetime import date, timedelta

from app.core.database import init_db, db_session
from app.schemas.event import EventCreate, CategoryEnum
from app.repositories.events import insert_event


def main() -> None:
    init_db()
    today = date.today()
    samples = [
        EventCreate(title="Lagos Tech Meetup", description="Talks on AI, Web and Cloud.", location="Lagos, Nigeria", category=CategoryEnum.tech, date=today + timedelta(days=14)),
        EventCreate(title="Abuja Business Summit", description="Leaders discuss SME growth and funding.", location="Abuja, Nigeria", category=CategoryEnum.business, date=today + timedelta(days=21)),
        EventCreate(title="Port Harcourt Music Festival", description="Live performances by top Nigerian artists.", location="Port Harcourt, Nigeria", category=CategoryEnum.music, date=today + timedelta(days=30)),
        EventCreate(title="Lagos Marathon", description="Annual road race across Lagos.", location="Lagos, Nigeria", category=CategoryEnum.sports, date=today + timedelta(days=45)),
        EventCreate(title="Abuja Art & Culture Fair", description="Exhibitions and performances celebrating Nigerian culture.", location="Abuja, Nigeria", category=CategoryEnum.arts, date=today + timedelta(days=35)),
        EventCreate(title="Kano Community Clean-up", description="Join hands to keep Kano clean.", location="Kano, Nigeria", category=CategoryEnum.community, date=today + timedelta(days=10)),
        EventCreate(title="Ibadan Startup Weekend", description="Build and pitch startup ideas in 54 hours.", location="Ibadan, Nigeria", category=CategoryEnum.tech, date=today + timedelta(days=28)),
        EventCreate(title="Enugu Food Carnival", description="Taste delicacies from across Nigeria.", location="Enugu, Nigeria", category=CategoryEnum.community, date=today + timedelta(days=40)),
    ]

    with db_session() as conn:
        for s in samples:
            insert_event(conn, s)
    print("Seeded events successfully.")


if __name__ == "__main__":
    main()
