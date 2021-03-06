import sqlalchemy as db
from datetime import datetime
from collections import namedtuple, OrderedDict
from obs_inv_utils import search_engine as se
from sqlalchemy import Table, Column, MetaData
from sqlalchemy import Integer, String, ForeignKey, Boolean, DateTime, Float
from sqlalchemy import inspect
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

OBS_SQLITE_DATABASE = 'sqlite:///observations_inventory.db'
OBS_INVENTORY_TABLE = 'obs_inventory'
CMD_RESULTS_TABLE = 'cmd_results'
OBS_META_NCEPLIBS_BUFR_TABLE = 'obs_meta_nceplibs_bufr'

engine = db.create_engine(OBS_SQLITE_DATABASE, echo=True)
Base = declarative_base()
metadata = MetaData(engine)
Session = sessionmaker(bind=engine)

CmdResultData = namedtuple(
    'CmdResultData',
    [
        'command',
        'arg0',
        'raw_output',
        'raw_error',
        'error_code',
        'obs_day',
        'submitted_at',
        'latency',
        'inserted_at'
    ],
)

def create_obs_inventory_table():
    insp = inspect(engine)
    table_exists = insp.has_table(OBS_INVENTORY_TABLE)
    print(f'obs_inventory table exists: {table_exists}')
    if not insp.has_table(OBS_INVENTORY_TABLE):
 #       metadata = MetaData(engine)

        Table(OBS_INVENTORY_TABLE, metadata,
              Column(
                  'cmd_result_id',
                  Integer,
                  ForeignKey('cmd_results.cmd_result_id'),
                  nullable=False
              ),
              Column('obs_id', Integer, primary_key=True),
              Column('filename', String),
              Column('parent_dir', String),
              Column('platform', String),
              Column('s3_bucket', String),
              Column('prefix', String),
              Column('cycle_tag', String),
              Column('data_type', String),
              Column('cycle_time', Integer),
              Column('obs_day', DateTime),
              Column('data_format', String),
              Column('suffix', String),
              Column('nr_tag', Boolean),
              Column('file_size', Integer),
              Column('permissions', String),
              Column('last_modified', DateTime),
              Column('inserted_at', DateTime),
        )

  #      metadata.create_all(engine)


def create_cmd_results_table():
    insp = inspect(engine)
    table_exists = insp.has_table(CMD_RESULTS_TABLE)
    print(f'cmd_results table exists: {table_exists}')
    if not insp.has_table(CMD_RESULTS_TABLE):
  #      metadata = MetaData(engine)

        Table(CMD_RESULTS_TABLE, metadata,
              Column('cmd_result_id', Integer, primary_key=True),
              Column('command', String),
              Column('arg0', String),
              Column('raw_output', String),
              Column('raw_error', String),
              Column('error_code', String),
              Column('obs_day', DateTime),
              Column('submitted_at', DateTime),
              Column('latency', String),
              Column('inserted_at', DateTime),
        )

        # metadata.create_all(engine)


def create_obs_meta_nceplibs_bufr_table():
    insp = inspect(engine)
    table_exists = insp.has_table(OBS_META_NCEPLIBS_BUFR_TABLE)
    print(f'obs_meta_nceplibs_bufr table exists: {table_exists}')
    if not insp.has_table(OBS_META_NCEPLIBS_BUFR_TABLE):
  #      metadata = MetaData(engine)

        Table(OBS_META_NCEPLIBS_BUFR_TABLE, metadata,
              Column('meta_id', Integer, primary_key=True),
              Column(
                  'obs_id',
                  Integer,
                  ForeignKey('obs_inventory.obs_id'),
                  nullable=False
              ),
              Column(
                  'cmd_result_id',
                  Integer,
                  ForeignKey('cmd_results.cmd_result_id'),
                  nullable=False
              ),
              Column('cmd_str', String),
              Column('sat_id', Integer),
              Column('sat_id_name', String),
              Column('obs_count', Integer),
              Column('sat_inst_id', Integer),
              Column('sat_inst_desc', String),
              Column('filename', String),
              Column('file_size', Integer),
              Column('obs_day', DateTime),
              Column('inserted_at', DateTime),
        )

   #     metadata.create_all(engine)



class CmdResult(Base):
    __tablename__ = CMD_RESULTS_TABLE

    cmd_result_id = Column(Integer, primary_key=True)
    command = Column(String(512))
    arg0 = Column(String(256))
    raw_output = Column(String(50000))
    raw_error = Column(String(50000))
    error_code = Column(Integer())
    obs_day = Column(DateTime())
    submitted_at = Column(DateTime())
    latency = Column(Float())
    inserted_at = Column(DateTime())

    # nceplibs_bufr_items = relationship("ObsMetaNceplibsBufr", backref="cmd_results")


class ObsInventory(Base):
    __tablename__ = OBS_INVENTORY_TABLE

    obs_id = Column(Integer, primary_key=True)
    cmd_result_id = Column(Integer, ForeignKey('cmd_results.cmd_result_id'))
    filename = Column(String(255))
    parent_dir = Column(String(1023))
    platform = Column(String(63))
    s3_bucket = Column(String(63))
    prefix = Column(String(63))
    cycle_tag = Column(String(63))
    data_type = Column(String(63))
    cycle_time = Column(Integer(), default=0)
    obs_day = Column(DateTime())
    data_format = Column(String(63))
    suffix = Column(String(63))
    nr_tag = Column(Boolean())
    file_size = Column(Integer())
    permissions = Column(String(15))
    last_modified = Column(DateTime())
    inserted_at = Column(DateTime())

    cmd_result = relationship("CmdResult", foreign_keys=[cmd_result_id])


class ObsMetaNceplibsBufr(Base):
    __tablename__ = OBS_META_NCEPLIBS_BUFR_TABLE

    meta_id = Column(Integer, primary_key=True)
    obs_id = Column(Integer, ForeignKey('obs_inventory.obs_id'))
    cmd_result_id = Column(Integer, ForeignKey('cmd_results.cmd_result_id'))
    cmd_str = Column(String(31))
    sat_id = Column(Integer(), default=-1)
    sat_id_name = Column(String(31))
    obs_count = Column(Integer(), default=-1)
    sat_inst_id = Column(Integer, default=-1)
    sat_inst_desc = Column(String(127))
    filename = Column(String(63))
    file_size = Column(Integer(), default=-1)
    obs_day = Column(DateTime())
    inserted_at = Column(DateTime())

    cmd_result = relationship("ObsInventory", foreign_keys=[obs_id])
    cmd_result = relationship("CmdResult", foreign_keys=[cmd_result_id])

def insert_obs_inv_items(obs_inv_items):
    if not isinstance(obs_inv_items, list):
        msg = 'Inserted observation inventory items must be in the form' \
              f' of a list.  Received type: {type(obs_inv_items)}'
        raise TypeError(msg)

    rows = []
    for obs_item in obs_inv_items:
        if not isinstance(obs_item, se.TarballFileMeta):
            msg = 'Each observation inventory item must be in the form' \
                  f' of TarballFileMeta. Item type: {type(obs_item)}'
            raise TypeError(msg)

        tbl_item = ObsInventory(
            cmd_result_id=obs_item.cmd_result_id,
            filename=obs_item.filename,
            parent_dir=obs_item.parent_dir,
            platform=obs_item.platform,
            s3_bucket=obs_item.s3_bucket,
            prefix=obs_item.prefix,
            cycle_tag=obs_item.cycle_tag,
            data_type=obs_item.data_type,
            cycle_time=obs_item.cycle_time,
            obs_day=obs_item.obs_day,
            data_format=obs_item.data_format,
            suffix=obs_item.suffix,
            nr_tag=obs_item.nr_tag,
            file_size=obs_item.file_size,
            permissions=obs_item.permissions,
            last_modified=obs_item.last_modified,
            inserted_at=obs_item.inserted_at,
        )
        rows.append(tbl_item)

    session = Session()
    session.bulk_save_objects(rows)
    session.commit()
    session.close()


def insert_cmd_result(cmd_result_data):
    if not isinstance(cmd_result_data, CmdResultData):
        msg = 'Inserted command result item must be in the form' \
              f' of type: CmdResultData.  Received type: ' \
              f'{type(cmd_result_data)}'
        raise TypeError(msg)

    tbl_item = CmdResult(
        command=cmd_result_data.command,
        arg0=cmd_result_data.arg0,
        raw_output=cmd_result_data.raw_output,
        raw_error=cmd_result_data.raw_error,
        error_code=cmd_result_data.error_code,
        obs_day=cmd_result_data.obs_day,
        submitted_at=cmd_result_data.submitted_at,
        latency=cmd_result_data.latency,
        inserted_at=datetime.utcnow()
    )

    session = Session()
    session.add(tbl_item)
    session.commit()
    print(f'cmd_result id: {tbl_item.cmd_result_id}')
    cmd_id = tbl_item.cmd_result_id
    session.close()
    return cmd_id


def insert_obs_meta_nceplibs_bufr_item(obs_meta_items):
    if not isinstance(obs_meta_items, list):
        msg = 'Inserted obs nceplibs bufr meta items must be in the form' \
              f' of a list.  Received type: {type(obs_meta_items)}'

    rows = []
    for item in obs_meta_items:

        tbl_item = ObsMetaNceplibsBufr(
            obs_id=item.obs_id,
            cmd_result_id=item.cmd_result_id,
            cmd_str=item.cmd_str,
            sat_id=item.sat_id,
            sat_id_name=item.sat_id_name,
            obs_count=item.obs_count,
            sat_inst_id=item.sat_inst_id,
            sat_inst_desc=item.sat_inst_desc,
            filename=item.filename,
            file_size=item.file_size,
            obs_day=item.obs_day,
            inserted_at=datetime.utcnow()
        )

        rows.append(tbl_item)

    session = Session()
    session.bulk_save_objects(rows)
    session.commit()
    session.close()



create_obs_inventory_table()
create_cmd_results_table()
create_obs_meta_nceplibs_bufr_table()
metadata.create_all(engine)
