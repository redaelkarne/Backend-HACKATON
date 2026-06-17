import uuid
from sqlalchemy import Column, String, Integer, Float, DateTime, Text, JSON, Date, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


class User(Base):
    __tablename__ = "users"
    id = Column(String(20), primary_key=True, default=lambda: _id("usr"))
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    level = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    # Strava OAuth tokens (nullable — only set after the user connects their Strava account)
    strava_athlete_id = Column(String(64), nullable=True, unique=True)
    strava_access_token = Column(Text, nullable=True)
    strava_refresh_token = Column(Text, nullable=True)
    strava_token_expires_at = Column(Integer, nullable=True)  # Unix timestamp


    profile = relationship("Profile", back_populates="user", uselist=False)
    bikes = relationship("Bike", back_populates="user")
    activities = relationship("Activity", back_populates="user")
    likes = relationship("Like", back_populates="user")
    comments = relationship("Comment", back_populates="user")
    recommendations = relationship("TyreRecommendation", back_populates="user")
    challenge_participants = relationship("ChallengeParticipant", back_populates="user")


class Profile(Base):
    __tablename__ = "profiles"
    user_id = Column(String(20), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    avatar_url = Column(String(500))
    rider_type = Column(String(20), nullable=False, default="route")
    bio = Column(Text)
    preferences = Column(JSON)

    user = relationship("User", back_populates="profile")


class Bike(Base):
    __tablename__ = "bikes"
    id = Column(String(20), primary_key=True, default=lambda: _id("bik"))
    user_id = Column(String(20), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    brand = Column(String(100), nullable=False)
    model = Column(String(100), nullable=False)
    category = Column(String(20), nullable=False)
    wheel_size = Column(String(20))

    user = relationship("User", back_populates="bikes")
    mounted_tyres = relationship("MountedTyre", back_populates="bike")
    activities = relationship("Activity", back_populates="bike")


class MountedTyre(Base):
    __tablename__ = "mounted_tyres"
    id = Column(String(20), primary_key=True, default=lambda: _id("mty"))
    bike_id = Column(String(20), ForeignKey("bikes.id", ondelete="CASCADE"), nullable=False)
    brand = Column(String(100), nullable=False)
    model = Column(String(100), nullable=False)
    size = Column(String(20), nullable=False)
    mounted_at = Column(Date, nullable=False)
    estimated_lifespan_km = Column(Float, nullable=False)

    bike = relationship("Bike", back_populates="mounted_tyres")


class Activity(Base):
    __tablename__ = "activities"
    id = Column(String(20), primary_key=True, default=lambda: _id("act"))
    user_id = Column(String(20), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    bike_id = Column(String(20), ForeignKey("bikes.id"), nullable=False)
    type = Column(String(20), nullable=False)
    status = Column(String(20), nullable=False, default="draft")
    weather = Column(String(20))
    notes = Column(Text)
    distance_km = Column(Float)
    duration_seconds = Column(Integer)
    elevation_m = Column(Float)
    average_speed_kmh = Column(Float)
    route_polyline = Column(Text)
    rating = Column(Integer)
    started_at = Column(DateTime(timezone=True), nullable=False)
    completed_at = Column(DateTime(timezone=True))

    user = relationship("User", back_populates="activities")
    bike = relationship("Bike", back_populates="activities")
    likes = relationship("Like", back_populates="activity")
    comments = relationship("Comment", back_populates="activity")


class Like(Base):
    __tablename__ = "likes"
    id = Column(String(20), primary_key=True, default=lambda: _id("lk"))
    user_id = Column(String(20), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    activity_id = Column(String(20), ForeignKey("activities.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="likes")
    activity = relationship("Activity", back_populates="likes")


class Comment(Base):
    __tablename__ = "comments"
    id = Column(String(20), primary_key=True, default=lambda: _id("cmt"))
    activity_id = Column(String(20), ForeignKey("activities.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String(20), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    activity = relationship("Activity", back_populates="comments")
    user = relationship("User", back_populates="comments")


class TyreRecommendation(Base):
    __tablename__ = "tyre_recommendations"
    id = Column(String(20), primary_key=True, default=lambda: _id("rec"))
    user_id = Column(String(20), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    rider_type = Column(String(20))
    terrain = Column(String(20))
    weather = Column(String(20))
    priority = Column(String(30))
    ride_frequency = Column(String(20))
    primary_tyre = Column(JSON, nullable=False)
    alternatives = Column(JSON, default=list)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="recommendations")


class Challenge(Base):
    __tablename__ = "challenges"
    id = Column(String(20), primary_key=True, default=lambda: _id("chl"))
    title = Column(String(200), nullable=False)
    description = Column(Text)
    goal_type = Column(String(50), nullable=False)
    goal_value = Column(Float, nullable=False)
    starts_at = Column(DateTime(timezone=True), nullable=False)
    ends_at = Column(DateTime(timezone=True), nullable=False)

    participants = relationship("ChallengeParticipant", back_populates="challenge")


class ChallengeParticipant(Base):
    __tablename__ = "challenge_participants"
    id = Column(String(20), primary_key=True, default=lambda: _id("cp"))
    challenge_id = Column(String(20), ForeignKey("challenges.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String(20), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    joined_at = Column(DateTime(timezone=True), server_default=func.now())

    challenge = relationship("Challenge", back_populates="participants")
    user = relationship("User", back_populates="challenge_participants")


class Tyre(Base):
    __tablename__ = "tyres"
    id = Column(Integer, primary_key=True, autoincrement=True)
    brand = Column(String(100))
    product_type = Column(String(100))
    cycle_type = Column(String(100))
    segment = Column(String(200))
    bead = Column(String(100))
    width_etrto = Column(String(20))
    diameter_etrto = Column(String(20))
    type_tube = Column(String(100))
    valve_tube = Column(String(100))
    valve_length = Column(String(20))
    ean_code = Column(String(50))
    discontinued_date = Column(String(20))
    weight_g = Column(String(20))
    market_perimeter = Column(String(200))
    web_range_name = Column(String(300))
    web_diameter_mm = Column(String(20))
    web_diameter_inch = Column(String(20))
    web_width_mm = Column(String(20))
    web_width_inch = Column(String(20))
    rim_type = Column(String(100))
    web_product_designation = Column(String(300))
    fitting = Column(String(50))
    tpi = Column(String(50))
    min_pressure_bar = Column(String(20))
    max_pressure_bar = Column(String(20))
    min_pressure_psi = Column(String(20))
    max_pressure_psi = Column(String(20))
    recommended_inner_tube = Column(String(200))
    sidewall_type = Column(String(100))
    sealing = Column(String(100))
    shore = Column(String(50))
    sidewall_color = Column(String(50))
    tread_pattern_color = Column(String(50))
    terrain_types = Column(String(300))
    use = Column(String(100))
    rubber_technologies = Column(String(200))
    casing_technologies = Column(String(200))
    tread_pattern_technologies = Column(String(200))
    reinforcement_technologies = Column(String(200))
    ebike_technologies = Column(String(200))
    reflective_strip = Column(String(10))
    knurling_strip = Column(String(10))
    shoulder_color = Column(String(50))
    border_color = Column(String(50))
    cycle_type_web = Column(String(100))
    pic1 = Column(Text)
    pic2 = Column(Text)
    price = Column(Float, nullable=False)
