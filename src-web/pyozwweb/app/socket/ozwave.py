# -*- coding: utf-8 -*-

"""The network socket

Thinking about rooms.
- A room for the network : state,
- A room for nodes : list, add, remove, ...
- A room for each nodes (nodeid_1): values, parameters, ...
- A room for the controller
- A room for values

When joining a room, you will receive message from it.



"""

__license__ = """

This file is part of **python-openzwave** project https://github.com/bibi21000/python-openzwave.

License : GPL(v3)

**python-openzwave** is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

**python-openzwave** is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.
You should have received a copy of the GNU General Public License
along with python-openzwave. If not, see http://www.gnu.org/licenses.
"""
__author__ = 'Sébastien GALLET aka bibi21000'
__email__ = 'bibi21000@gmail.com'

import os, sys
import time
from threading import Thread

from flask import Flask, render_template, session, request, current_app
from flask.ext.socketio import SocketIO, emit, join_room, leave_room, close_room, disconnect

import libopenzwave
import openzwave
from openzwave.node import ZWaveNode
from openzwave.value import ZWaveValue
from openzwave.scene import ZWaveScene
from openzwave.controller import ZWaveController
from openzwave.network import ZWaveNetwork
from openzwave.option import ZWaveOption
from louie import dispatcher, All
from pyozwweb.app import socketio, app
from pyozwweb.app.rooms import data_room_network

import logging
try:  # Python 2.7+
    from logging import NullHandler
except ImportError:
    class NullHandler(logging.Handler):
        """NullHandler logger for python 2.6"""
        def emit(self, record):
            pass
logging.getLogger('pyozwweb').addHandler(NullHandler())

@socketio.on('my echo event', namespace='/ozwave')
def echo_message(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    logging.debug("Client %s request echo message : %s", request.remote_addr, message)
    emit('my response',
         {'data': message['data'], 'count': session['receive_count']})

@socketio.on('disconnect request', namespace='/ozwave')
def disconnect_request():
    session['receive_count'] = session.get('receive_count', 0) + 1
    logging.debug("Client %s disconnects", request.remote_addr)
    emit('my response',
         {'data': 'Disconnected!', 'count': session['receive_count']})
    disconnect()

@socketio.on('connect', namespace='/ozwave')
def echo_connect():
    logging.debug("Client %s connects", request.remote_addr)
    emit('my response', {'data': 'Connected', 'count': 0})

@socketio.on('my network event', namespace='/ozwave')
def echo_network_event(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    logging.debug("Client %s network event : %s", request.remote_addr, message)
    emit('my network response',
         {'data': data_room_network(current_app.extensions['zwnetwork']), 'count': session['receive_count']})

@socketio.on('my nodes event', namespace='/ozwave')
def echo_nodes_event(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    logging.debug("Client %s nodes event : %s", request.remote_addr, message)
    emit('my nodes response',
         {'data': current_app.extensions['zwnetwork'].nodes_to_dict(), 'count': session['receive_count']})

@socketio.on('my controller event', namespace='/ozwave')
def echo_controller_event(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    logging.debug("Client %s controller event : %s", request.remote_addr, message)
    emit('my controller response',
         {'data': current_app.extensions['zwnetwork'].controller.to_dict(), 'count': session['receive_count']})

@socketio.on('my command event', namespace='/ozwave')
def echo_command_event(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    logging.debug("Client %s controller command event : %s", request.remote_addr, message)
    data = {}
    data['result'] = False
    data['message'] = "Command fail to start"
    init_data = {'result':False, 'message':'', 'state':''}
    #Emit a blank message to clean the old data in javascript
    emit('my command response',
        {'data': init_data,
        'count': session['receive_count']})

    command = message['command']
    if command == 'no_command':
        #This is for first time launch. Return default values for javascript
        data = {}
        data['message'] = current_app.extensions['zwnetwork'].controller.ctrl_last_message
        data['state'] = current_app.extensions['zwnetwork'].controller.ctrl_last_state
        emit('my message response',
            {'data': data,
            'count': session['receive_count']})
        emit('my command response',
            {'data': init_data,
            'count': session['receive_count']})
        return
    elif command == 'send_node_information':
        node_id=-1
        try:
            node_id=int(message['node_id'])
        except ValueError:
            node_id = -1
        except KeyError:
            node_id = -1
        if node_id not in current_app.extensions['zwnetwork'].nodes :
            data['result'] = False
            data['message'] = "Bad node_id"
        else:
            data['result'] = current_app.extensions['zwnetwork'].controller.begin_command_send_node_information(node_id)
            #data['result'] = True
    elif command == 'remove_failed_node':
        node_id=-1
        try:
            node_id=int(message['node_id'])
        except ValueError:
            node_id = -1
        except KeyError:
            node_id = -1
        if node_id not in current_app.extensions['zwnetwork'].nodes :
            data['result'] = False
            data['message'] = "Bad node_id"
        else:
            data['result'] = current_app.extensions['zwnetwork'].controller.begin_command_remove_failed_node(node_id)
            #data['result'] = True
    elif command == 'has_node_failed':
        node_id=-1
        try:
            node_id=int(message['node_id'])
        except ValueError:
            node_id = -1
        except KeyError:
            node_id = -1
        if node_id not in current_app.extensions['zwnetwork'].nodes :
            data['result'] = False
            data['message'] = "Bad node_id"
        else:
            data['result'] = current_app.extensions['zwnetwork'].controller.begin_command_has_node_failed(node_id)
            #data['result'] = True
    elif command == 'replace_failed_node':
        node_id=-1
        try:
            node_id=int(message['node_id'])
        except ValueError:
            node_id = -1
        except KeyError:
            node_id = -1
        if node_id not in current_app.extensions['zwnetwork'].nodes :
            data['result'] = False
            data['message'] = "Bad node_id"
        else:
            data['result'] = current_app.extensions['zwnetwork'].controller.begin_command_replace_failed_node(node_id)
            #data['result'] = True
    elif command == 'request_node_neigbhor_update':
        node_id=-1
        try:
            node_id=int(message['node_id'])
        except ValueError:
            node_id = -1
        except KeyError:
            node_id = -1
        if node_id not in current_app.extensions['zwnetwork'].nodes :
            data['result'] = False
            data['message'] = "Bad node_id"
        else:
            data['result'] = current_app.extensions['zwnetwork'].controller.begin_command_request_node_neigbhor_update(node_id)
            #data['result'] = True
    elif command == 'request_network_update':
        data['result'] = current_app.extensions['zwnetwork'].controller.begin_command_request_network_update()
    elif command == 'replication_send':
        try:
            high_power = bool(message['high_power']) if 'high_power' in message else False
        except ValueError:
            high_power = False
        except KeyError:
            high_power = False
        data['result'] = current_app.extensions['zwnetwork'].controller.begin_command_replication_send(high_power)
        #data['result'] = True
    elif command == 'add_device':
        try:
            high_power = bool(message['high_power']) if 'high_power' in message else False
        except ValueError:
            high_power = False
        except KeyError:
            high_power = False
        data['result'] = current_app.extensions['zwnetwork'].controller.begin_command_add_device(high_power)
        #data['result'] = True
    elif command == 'remove_device':
        try:
            high_power = bool(message['high_power']) if 'high_power' in message else False
        except ValueError:
            high_power = False
        except KeyError:
            high_power = False
        data['result'] = current_app.extensions['zwnetwork'].controller.begin_command_remove_device(high_power)
        #data['result'] = True
    elif command == 'cancel_command':
        data['result'] = current_app.extensions['zwnetwork'].controller.cancel_command()
    if data['result'] == True :
        data['message'] = "Command started"
    logging.debug("Client %s controller command event, data returned : %s", request.remote_addr, data)
    emit('my command response',
         {'data': data,
          'count': session['receive_count']})

@socketio.on('my value event', namespace='/ozwave')
def echo_value_event(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    node_id = message['node_id']
    value_id = message['value_id']
    logging.debug("Client %s value event : %s", request.remote_addr, current_app.extensions['zwnetwork'].nodes[node_id].values[value_id].to_dict())
    emit('my value response',
         {'data': current_app.extensions['zwnetwork'].nodes[node_id].values[value_id].to_dict(), 'count': session['receive_count']})
