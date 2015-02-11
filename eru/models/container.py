#!/usr/bin/python
#coding:utf-8

import sqlalchemy.exc
from datetime import datetime

from eru.models import db, Base


class Container(Base):
    __tablename__ = 'container'

    host_id = db.Column(db.Integer, db.ForeignKey('host.id'))
    app_id = db.Column(db.Integer, db.ForeignKey('app.id'))
    version_id = db.Column(db.Integer, db.ForeignKey('version.id'))
    container_id = db.Column(db.CHAR(64), nullable=False, unique=True)
    name = db.Column(db.CHAR(255), nullable=False)
    entrypoint = db.Column(db.CHAR(255), nullable=False)
    created = db.Column(db.DateTime, default=datetime.now)

    cores = db.relationship('Core', backref='container', lazy='dynamic')
    port = db.relationship('Port', backref='container', lazy='dynamic')

    def __init__(self, container_id, host, version, name, entrypoint):
        self.container_id = container_id
        self.host_id = host.id
        self.version_id = version.id
        self.app_id = version.app_id
        self.name = name
        self.entrypoint = entrypoint

    @classmethod
    def create(cls, container_id, host, version, name, entrypoint, cores, port):
        """
        创建一个容器. cores 是 [core, core, ...] port 则是 port.
        """
        try:
            container = cls(container_id, host, version, name, entrypoint)
            db.session.add(container)
            for core in cores:
                container.cores.append(core)
            container.ports.append(port)
            db.session.commit()
            return container
        except sqlalchemy.exc.IntegrityError:
            db.session.rollback()
            return None

    def delete(self):
        """删除这条记录, 记得要释放自己占用的资源"""
        host = self.host
        host.release_cores(self.cores.all())
        host.release_ports(self.port.all())
        db.session.delete(self)
        db.session.commit()

