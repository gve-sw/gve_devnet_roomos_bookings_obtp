'''
Copyright (c) 2021 Cisco and/or its affiliates.

This software is licensed to you under the terms of the Cisco Sample
Code License, Version 1.1 (the "License"). You may obtain a copy of the
License at

               https://developer.cisco.com/docs/licenses

All use of the material herein must be in accordance with the terms of
the License. All rights not expressly granted by the License are
reserved. Unless required by applicable law or agreed to separately in
writing, software distributed under the License is distributed on an "AS
IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
or implied.

'''
import json
import base64
import asyncio
import ssl
import websockets
import requests
import os
from lxml import etree
from flask import Flask, render_template, redirect, request, session

app = Flask(__name__)
app.secret_key = 'secret_key_here'


''' Flask application routes '''


@app.route('/')
# Default route
def default():
    return redirect('/login')


@app.route('/login')
# Login route
def login():
    return render_template('login.html')


@app.route('/verify_login', methods=['POST'])
# Verify login route
def verify_login():
    session['ip_address'] = request.form.get('ip_address')
    session['username'] = request.form.get('username')
    session['password'] = request.form.get('password')
    session['count'] = 0
    try:
        session['device_id'] = asyncio.run(
            xapi_get_host_info(session['ip_address']))
    except:
        return 'Couldn\'t get device Information. Please confirm your credentials..'

    print('New login - IP: ' + str(session['ip_address']))

    return redirect('/context')


@app.route('/logout')
# Logout route
def logout():
    print('Logout - device:' + str(session['ip_address']))
    session.pop('ip_address')
    session.pop('username')
    session.pop('password')
    session.pop('device_id')
    return redirect('/login')


@app.route('/context')
# Context route
def context():
    return render_template('context.html', device_ip_address=session['ip_address'], device_id=session['device_id'])


@app.route('/get_bookings')
# Get list of bookings in the endpoint
def get_bookings():
    print('Getting Bookings for device: ' + session['ip_address'])
    result = asyncio.run(xapi_get_bookings(session['ip_address']))

    # Creating summary for the web page
    num_of_bookings = result["result"]["ResultInfo"]["TotalRows"]
    # print('num_of_bookings: ' + str(num_of_bookings))

    list_of_bookings = ''

    if(num_of_bookings > 0):
        list_of_bookings = result["result"]["Booking"]
        # print('list_of_bookings' + str(list_of_bookings))

    json_summary = {
        'num_of_bookings': num_of_bookings,
        'list_of_bookings': list_of_bookings
    }

    return json.dumps(json_summary)


@app.route('/clear_bookings', methods=['POST'])
# Default route
def clear_bookings():
    print('Clearing all Bookings for device: ' + session['ip_address'])
    result = asyncio.run(xapi_clear_bookings(session['ip_address']))
    response = result["result"]
    return json.dumps(response)


@app.route('/insert_booking')
# Insert Booking route
def insert_booking():
    print('Inserting a booking to device: ' +
          session['ip_address'])

    return render_template('insert_booking.html', device_ip_address=session['ip_address'], device_id=session['device_id'])


@app.route('/send_xml_bookings', methods=['POST'])
# Send XML bookings route
def send_xml_bookings():
    print('Sending Bookings from local XML file to device: ' +
          session['ip_address'])
    meeting_title = request.form.get('meeting_title')
    start_time = request.form.get('start_time')
    end_time = request.form.get('end_time')
    sip_url = request.form.get('sip_url')

    # Check any existing booking in the device itself (Using Bookings List)
    bookings = json.loads(get_bookings())
    num_of_bookings = bookings['num_of_bookings']
    list_of_bookings = bookings['list_of_bookings']
    
    if(num_of_bookings > 0):
        print('# of bookings found in device: ' + str(num_of_bookings))
        delete_xml_file()
        for booking in list_of_bookings:
            existing_title = str(booking['Title'])
            existing_start_time = str(booking['Time']['StartTime'])
            existing_end_time = str(booking['Time']['EndTime'])
            existing_sip_url = str(booking['DialInfo']['Calls']['Call'][0]['Number'])
            xml = add_booking_to_xml(existing_title, existing_start_time, existing_end_time, existing_sip_url)
        
    
    xml = add_booking_to_xml(meeting_title, start_time, end_time, sip_url)    
    response = send_xml_to_device(xml)

    return 'XML Bookings Sent to device.\nResponse Code: ' + response


@app.route('/delete_xml_file', methods=['POST'])
# Delete XML File route
def delete_xml_file():
    print('Deleting local XML file for the device: ' +
          session['ip_address'])

    file_name = 'Bookings/Bookings_' + session['ip_address'] + '.xml'
    file_exists = os.path.isfile(file_name)
    if file_exists:
        print('File: ' + file_name + ' found, deleting it..')
        try:
            os.remove(file_name)
            return('File: ' + file_name + ' has been deleted')
        except:
            return('Unable to delete file: ' + file_name)
    else:
        return 'File not found!\nCreate a new booking to generate a new file for device: ' + session['ip_address']


''' Websocket functions '''


async def connect(address):
    return await websockets.connect('wss://{}/ws/'.format(address), ssl=ssl._create_unverified_context(), extra_headers={
        'Authorization': 'Basic {}'.format(base64.b64encode('{}:{}'.format(session['username'], session['password']).encode()).decode('utf-8'))})


def construct(method):
    session['count'] += 1
    return {'jsonrpc': '2.0', 'id': str(session['count']), 'method': method}


def query(params):
    print('* Method: xQuery ' + params)
    payload = construct('xQuery')
    payload['params'] = {'Query': params.split()}
    return payload


def get(params):
    print('* Method: xGet ' + params)
    payload = construct('xGet')
    params = [i if not i.isnumeric() else int(i) for i in params.split()]
    payload['params'] = {'Path': params}
    return payload


def command(path, params=None):
    print('* Method: xCommand ' + path)
    payload = construct('{}{}'.format('xCommand/', '/'.join(path.split(' '))))

    # Params are for multiline commands and other command parameters {'ConfigId':'example', 'body':'<Extensions><Version>1.0</Version>...</Extensions>'}
    if params != None:
        payload['params'] = params

    return payload


def config(path, value):
    print('* Method: xSet ' + path)
    payload = construct('xSet')
    payload['params'] = {
        "Path": ['Configuration'] + path.split(' '),
        "Value": value
    }
    return payload


def feedbackSubscribe(path=None, notify=False):
    payload = construct('xFeedback/Subscribe')
    payload['params'] = {
        "Query": path.split(' '),
        "NotifyCurrentValue": notify
    }
    return payload


async def send(ws, message):
    await ws.send(json.dumps(message))
    # print('-'*5 + ' Sending: ' + '-'*5)
    # print(message)


async def receive(ws):
    result = await ws.recv()
    # print('-'*5 + ' Received: ' + '-'*5)
    # print(result)
    return (json.loads(result))


''' Customize tasks start here '''


async def xapi_get_host_info(devince_ip_address):
    ws = await connect(devince_ip_address)
    try:
        # Getting Bookings: xStatus SystemUnit ProductId
        params = 'Status SystemUnit ProductId'
        await send(ws, get(params))
        result = await receive(ws)
        product_id = result['result']

        return product_id
    finally:
        await ws.close()


async def xapi_get_bookings(devince_ip_address):
    ws = await connect(devince_ip_address)
    try:
        # Getting Bookings: xCommand Bookings List
        params = 'Bookings List'
        await send(ws, command(params))
        result = await receive(ws)
        return result

    finally:
        await ws.close()


async def xapi_clear_bookings(devince_ip_address):
    ws = await connect(devince_ip_address)
    try:
        # Getting Bookings: xCommand Bookings List
        params = 'Bookings Clear'
        await send(ws, command(params))
        result = await receive(ws)
        return result

    finally:
        await ws.close()


async def xapi_add_booking(devince_ip_address, payload):
    ws = await connect(devince_ip_address)
    try:
        # Creating a new Booking: xCommand Bookings PUT/Book (Book supported on OS10.x)
        params = 'Bookings Book'

        # TODO: Pass the right params to Bookings Book
        # await send(ws, command(params,payload))

        # Sample to add a booking with the default values (Duration: 30 min, StartTime: currentTime, Title:""Ad hoc meeting"")
        await send(ws, command(params))
        result = await receive(ws)
        return result

    finally:
        await ws.close()


# Manually send bookings from a local XML file
def add_booking_to_xml(meeting_title, start_time, end_time, sip_url):


    # Check if the file exists, read its data, add to it, then send it..
    file_name = 'Bookings/Bookings_' + session['ip_address'] + '.xml'
    file_exists = os.path.isfile(file_name)
    if file_exists:
        print('File: ' + file_name + ' found, adding the meeting to it..')
        f = open(file_name, 'r')
        xml = f.read()
        # Get the number of existing bookings in the file, then add the meeting to it
        xml_tree = etree.ElementTree(etree.fromstring(xml))
        xml_root = xml_tree.getroot()
        num_of_bookings = len(xml_root.getchildren())
        print('# of bookings found in the XML file: ' + str(num_of_bookings))
        new_id = num_of_bookings+1
        new_booking_xml = generate_booking_xml(
            new_id, meeting_title, start_time, end_time, sip_url)
        xml = xml.replace('</Bookings>', new_booking_xml)
    # Else if the file doesn't exist, create it, add the first booking to it, then send it..
    else:
        # Read the details of the meeting sent from the frontend and generate a new xml
        print('File: ' + file_name + ' doesn\'t exist, creating it..')
        xml = generate_new_xml_file(meeting_title, start_time, end_time, sip_url)

    # Write/rewrite the XML file
    f = open(file_name, 'w')
    f.write(xml)

    return xml


def generate_new_xml_file(meeting_title, start_time, end_time, sip_url):
    xml = "<?xml version='1.0'?>\r\n<Bookings status=\"OK\">\r\n    <Booking>\r\n        <Id>1</Id>\r\n        <Title>" + meeting_title + "</Title>\r\n        <Agenda></Agenda>\r\n        <Privacy>Public</Privacy>\r\n        <Organizer>\r\n            <FirstName>Demo</FirstName>\r\n            <LastName></LastName>\r\n            <Email></Email>\r\n        </Organizer>\r\n        <Time>\r\n            <StartTime>" + start_time + "</StartTime>\r\n            <StartTimeBuffer>300</StartTimeBuffer>\r\n            <EndTime>" + end_time + \
        "</EndTime>\r\n            <EndTimeBuffer>0</EndTimeBuffer>\r\n        </Time>\r\n        <MaximumMeetingExtension>5</MaximumMeetingExtension>\r\n        <BookingStatus>OK</BookingStatus>\r\n        <BookingStatusMessage></BookingStatusMessage>\r\n        <Webex>\r\n            <Enabled>False</Enabled>\r\n            <MeetingNumber></MeetingNumber>\r\n            <Password></Password>\r\n        </Webex>\r\n        <Encryption>BestEffort</Encryption>\r\n        <Role>Master</Role>\r\n        <Recording>Disabled</Recording>\r\n        <DialInfo>\r\n            <Calls>\r\n                <Call>\r\n                    <Number>" + \
        sip_url + "</Number>\r\n                    <Protocol>SIP</Protocol>\r\n                    <CallRate>6000</CallRate>\r\n                    <CallType>Video</CallType>\r\n                </Call>\r\n            </Calls>\r\n            <ConnectMode>OBTP</ConnectMode>\r\n        </DialInfo>\r\n    </Booking>\r\n</Bookings>"
    return xml


def generate_booking_xml(new_id, meeting_title, start_time, end_time, sip_url):
    print('Generating booking XML with: ' + str(new_id),
          meeting_title, start_time, end_time, sip_url)
    xml = "\r\n    <Booking>\r\n        <Id>" + str(new_id) + "</Id>\r\n        <Title>" + meeting_title + "</Title>\r\n        <Agenda></Agenda>\r\n        <Privacy>Public</Privacy>\r\n        <Organizer>\r\n            <FirstName>Demo</FirstName>\r\n            <LastName></LastName>\r\n            <Email></Email>\r\n        </Organizer>\r\n        <Time>\r\n            <StartTime>" + start_time + "</StartTime>\r\n            <StartTimeBuffer>300</StartTimeBuffer>\r\n            <EndTime>" + end_time + \
        "</EndTime>\r\n            <EndTimeBuffer>0</EndTimeBuffer>\r\n        </Time>\r\n        <MaximumMeetingExtension>5</MaximumMeetingExtension>\r\n        <BookingStatus>OK</BookingStatus>\r\n        <BookingStatusMessage></BookingStatusMessage>\r\n        <Webex>\r\n            <Enabled>False</Enabled>\r\n            <MeetingNumber></MeetingNumber>\r\n            <Password></Password>\r\n        </Webex>\r\n        <Encryption>BestEffort</Encryption>\r\n        <Role>Master</Role>\r\n        <Recording>Disabled</Recording>\r\n        <DialInfo>\r\n            <Calls>\r\n                <Call>\r\n                    <Number>" + \
        sip_url + "</Number>\r\n                    <Protocol>SIP</Protocol>\r\n                    <CallRate>6000</CallRate>\r\n                    <CallType>Video</CallType>\r\n                </Call>\r\n            </Calls>\r\n            <ConnectMode>OBTP</ConnectMode>\r\n        </DialInfo>\r\n    </Booking>\r\n</Bookings>"
    return xml


def send_xml_to_device(xml):
    # Send the updated Bookings XML to the device
    # Encoding username and password to get the Basic Authentication token
    creds = str.encode(session['username']+':'+session['password'])
    encodedAuth = bytes.decode(base64.b64encode(creds))

    url = 'http://' + session['ip_address'] + '/bookingsputxml'
    headers = {
        'Content-Type': 'application/xml',
        'Authorization': 'Basic ' + encodedAuth
    }
    payload = xml
    response = requests.request("POST", url, headers=headers, data=payload)
    result = str(response.status_code) + ', ' + str(response.text)

    return result

# ''' Starting Flask web application '''
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=7000, debug=True, threaded=True)
