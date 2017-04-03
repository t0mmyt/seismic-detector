from crate.client import connect
from datetime import datetime
from iso8601 import parse_date
from sqlalchemy import create_engine, Column, Integer, String, TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from uuid import uuid4


class MetadataError(Exception):
    pass


class Metadata(object):
    def __init__(self, endpoints):
        if not isinstance(endpoints, list):
            endpoints = [endpoints]
        self.connection = connect(servers=endpoints)

    def create_tables(self):
        return True
        c = self.connection.cursor()
        c.execute("CREATE TABLE IF NOT EXISTS seismic.Metadata("
                  "uuid string PRIMARY KEY,"
                  "network STRING,"
                  "station STRING,"
                  "channel STRING,"
                  "start_time TIMESTAMP,"
                  "end_time TIMESTAMP,"
                  "sampling_rate int)")

    def put(self, uuid, network, station, channel, start, end, sampling_rate):
        start = datetime.fromtimestamp(start / 1000).replace(tzinfo=None).isoformat()
        end = datetime.fromtimestamp(end / 1000).replace(tzinfo=None).isoformat()
        c = self.connection.cursor()
        c.execute("SELECT COUNT(*) AS count FROM seismic.Metadata "
                  " WHERE network = ?"
                  " AND station = ?"
                  " AND channel = ?"
                  " AND start_time = ?"
                  " AND end_time = ?",
                  (network, station, channel, start, end))
        res = c.fetchone()
        if int(res[0]) > 0:
            raise MetadataError("Data already exists for {}".format(','.join((network, station, channel, start, end))))
        c.execute("INSERT INTO seismic.Metadata "
                  "(uuid, network, station, channel, start_time, end_time, sampling_rate)"
                  "VALUES(?, ?, ?, ?, ?, ?, ?)",
                  (uuid, network, station, channel, start, end, sampling_rate))

    def list(self, network, station, channel, start, end, sampling_rate=None):
        start = parse_date(start).replace(tzinfo=None)
        end = parse_date(end).replace(tzinfo=None)
        c = self.connection.cursor()
        c.execute("SELECT uuid, start_time, end_time, sampling_rate"
                  " FROM seismic.Metadata"
                  " WHERE network = ?"
                  " AND station = ?"
                  " AND channel = ?"
                  " AND (start_time <= ? AND end_time >= ?"
                  " OR start_time >= ? AND end_time <= ?"
                  " OR start_time <= ? AND end_time >= ?)"
                  " ORDER BY start_time",
                  (network, station, channel, start, start, start, end, end, end))
        return c.fetchall()


# Base = declarative_base()
#
#
# class MetadataTable(Base):
#     __table_args__ = {'schema' : 'seismic'}
#     __tablename__ = "Metadata"
#     uuid = Column(String, primary_key=True)
#     network = Column(String)
#     station = Column(String)
#     channel = Column(String)
#     sampling_rate = Column(Integer)
#     start_time = Column(TIMESTAMP)
#     end_time = Column(TIMESTAMP)
#
#     def __repr__(self):
#         return self.uuid, self.network, self.network, self.station, self.channel, \
#                self.start_time, self.end_time, self.sampling_rate
#
# if __name__ == '__main__':
#     engine = create_engine("crate://127.0.0.1:4200")
#     Session = sessionmaker(bind=engine)
#     s = Session()
#     s.add(MetadataTable(
#         uuid=str(uuid4()),
#         network="AB",
#         station="CDE1",
#         channel="Z",
#         start_time=parse_date("2011-01-01T00:00:00").replace(tzinfo=None),
#         end_time=parse_date("2011-01-01T01:00:00").replace(tzinfo=None),
#         sampling_rate=100
#     ))
#     s.commit()
#     print("Fin")
#
#
# # CREATE TABLE IF NOT EXISTS "seismic"."metadata" (
# #    "channel" STRING,
# #    "end_time" TIMESTAMP,
# #    "network" STRING,
# #    "sampling_rate" INTEGER,
# #    "start_time" TIMESTAMP,
# #    "station" STRING,
# #    "uuid" STRING,
# #    PRIMARY KEY ("uuid")
# # )
