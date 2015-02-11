#!/usr/bin/python
#coding:utf-8

import requests
from flask import Blueprint, request, jsonify, abort

from eru.common import code
from eru.models import Group, Pod, Host
from eru.utils import check_request_json


sys = Blueprint('sys', __name__, url_prefix='/sys')


@sys.route('/')
def index():
    return 'sys control'


@sys.route('/group/create', methods=['POST', ])
@check_request_json('name', code.HTTP_BAD_REQUEST)
def create_group():
    data = request.get_json()
    if not Group.create(data['name'], data.get('description', '')):
        abort(code.HTTP_BAD_REQUEST)
    return jsonify(msg=code.OK), code.HTTP_CREATED


@sys.route('/pod/create', methods=['POST', ])
@check_request_json('name', code.HTTP_BAD_REQUEST)
def create_pod():
    data = request.get_json()
    if not Pod.create(data['name'], data.get('description', '')):
        abort(code.HTTP_BAD_REQUEST)
    return jsonify(msg=code.OK), code.HTTP_CREATED


@sys.route('/pod/<pod_name>/assign', methods=['POST', ])
@check_request_json('group_name', code.HTTP_BAD_REQUEST)
def assign_pod_to_group(pod_name):
    data = request.get_json()

    group = Group.get_by_name(data['group_name'])
    pod = Pod.get_by_name(pod_name)
    if not (group and pod):
        abort(code.HTTP_BAD_REQUEST)

    if not pod.assigned_to_group(group):
        abort(code.HTTP_BAD_REQUEST)
    return jsonify(msg=code.OK), code.HTTP_CREATED


@sys.route('/host/create', methods=['POST', ])
@check_request_json(['addr', 'pod_name'], code.HTTP_BAD_REQUEST)
def create_host(name):
    data = request.get_json()
    addr = data['addr']

    pod = Pod.get_by_name(data['pod_name'])
    if not pod:
        abort(code.HTTP_BAD_REQUEST)

    r = requests.get('http://%s/info' % addr)
    if r.status_code != 200:
        abort(r.status_code)
    rv = r.json()
    if not Host.create(pod, addr, rv['Name'], rv['ID'], rv['NCPU'], rv['MemTotal']):
        abort(code.HTTP_BAD_REQUEST)
    return jsonify(msg=code.OK), code.HTTP_CREATED


@sys.route('/host/<addr>/assign', methods=['POST', ])
@check_request_json('group_name', code.HTTP_BAD_REQUEST)
def assign_host_to_group(addr):
    data = request.get_json()

    group = Group.get_by_name(data['group_name'])
    if not group:
        abort(code.HTTP_BAD_REQUEST)

    host = Host.get_by_addr(addr)
    if not host:
        abort(code.HTTP_BAD_REQUEST)

    if not host.assigned_to_group(group):
        abort(code.HTTP_BAD_REQUEST)
    return jsonify(msg=code.OK), code.HTTP_CREATED


@sys.route('/group/<group_name>/available_container_count', methods=['GET', ])
def group_max_containers(group_name, count):
    pod_name = request.args.get('pod_name', type=str, default='')
    cores_per_container = request.args.get('ncore', type=int, default=1)

    group = Group.get_by_name(group_name)
    if not group:
        abort(code.HTTP_BAD_REQUEST)
    pod = Pod.get_by_name(pod_name)
    if not pod:
        abort(code.HTTP_BAD_REQUEST)

    return jsonify(msg=code.OK, data=group.get_max_containers(pod, cores_per_container))

