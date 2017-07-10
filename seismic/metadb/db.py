import sqlalchemy
from sqlalchemy import Column, Index, String, Integer
from sqlalchemy_utcdatetime import UTCDateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from uuid import uuid4


Base = declarative_base()


class ObservationRecord(Base):
    __tablename__ = "observations"

    obs_id = Column(String, primary_key=True)
    network = Column(String)
    station = Column(String)
    channel = Column(String)
    start = Column(UTCDateTime, index=True)
    end = Column(UTCDateTime, index=True)
    format = Column(String)
    sampling_rate = Column(Integer)
    filename = Column(String)

    __table_args__ = (
        Index("obs_network_station_channel", "network", "station", "channel"),
    )

    def __init__(self, obs_id=None, **kwargs):
        """
        Define a new ObservationRecord for DB insert.  Automatically generates
        obs_id if not present.
        
        Args:
            obs_id: (string) Optional id 
            **kwargs: Other Args (see class variables)
        """
        if not obs_id:
            obs_id = uuid4().hex
        super().__init__(obs_id=obs_id, **kwargs)


class EventRecord(Base):
    __tablename__ = "events"

    evt_id = Column(String, primary_key=True)
    obs_id = Column(String, index=True)
    network = Column(String)
    station = Column(String)
    channel = Column(String)
    start = Column(UTCDateTime, index=True)
    end = Column(UTCDateTime, index=True)
    sampling_rate = Column(Integer)
    method = Column(String)

    __table_args__ = (
        Index("evt_network_station_channel", "network", "station", "channel"),
    )

    def __init__(self, evt_id=None, **kwargs):
        """
        Define a new EventRecord for DB insert.  Automatically generates
        evt_id if not present.

        Args:
            evt_id: (string) Optional id 
            **kwargs: Other Args (see class variables)
        """
        if not evt_id:
            evt_id = uuid4().hex
        super().__init__(evt_id=evt_id, **kwargs)


def get_session(url):
    engine = sqlalchemy.create_engine(url)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)
    return session()
