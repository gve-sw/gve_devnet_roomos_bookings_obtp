## GVE_DevNet_RoomOS_Bookings_OBTP

### Note:
Parts of this code were driven by the emulator already-developed here: [OBTP-Emulator](https://github.com/acaeti/OBTP-emulator), with major enhancements on:
- Adding the ability to check what existing bookings are available on the Cisco TelePresence endpoints
- Adding the ability to send multiple bookings and not just one replacing any existing bookings.
- Dynamically reading existing bookings' data (using [xCommand Bookings List](https://roomos.cisco.com/xapi/Command.Bookings.List/)) to a local XML file, adding the newly inserted booking to it, and then  sent to the device using a POST call to: ```'http://(ip_address)/bookingsputxml'```


## Contacts
* Rami Alfadel (ralfadel@cisco.com)

## Solution Components
* Cisco TelePresence endpoints
* [Cisco TelePresence end-point xAPIs](https://roomos.cisco.com/xapi/)
* Python
  - Python Module:
    - [Flask](https://flask.palletsprojects.com/)

## Solution Overview
This prototype is showing a method to send OBTP bookings to Cisco Collaboration Endpoints from a web dashboard, without the need to connect to calendar-services.


## Installation/Configuration

### Getting Started   
 1. Choose a folder, then create a virtual environment:  
   ```python3 -m venv <name of environment>```

 2. Activate the created virtual environment:  
   ```source <name of environment>/Scripts/activate```

 3. Access the created virtual environment:  
   ```cd <name of environment>```

 4. Clone this Github repository into the virtual environment folder:  
   ```git clone [add github link here]```
   - For Github link: 
        In Github, click on the **Clone or download** button in the upper part of the page > click the **copy icon**  
        ![/IMAGES/giturl.png](/IMAGES/giturl.png)

 5. Access the folder **GVE_DevNet_RoomOS_Bookings_OBTP**:  
   ```cd GVE_DevNet_RoomOS_Bookings_OBTP```

 6. Install the solution requirements:  
   ```pip3 install -r requirements.txt```

 7. Initiate the Flask application settings:  
   ```export FLASK_APP=app.py```  
   ```export FLASK_ENV=development```

 8. Start the Flask application:  
   ```flask run```

 9. Open the hosted web page in your browser:  
    (Default: [localhost:5000](localhost:5000))


## Usage
- As you open the main page, you will be asked to login with a Meraki API Key:
    ![/IMAGES/login.png](/IMAGES/login.png)

- If the login is successful, the context page will show up:
    ![/IMAGES/context.png](/IMAGES/context.png)
    - Displaying the following buttons/options:
        - **Get Current Bookings**:  
        Which will invoke the xAPI call: ([Bookings List](https://roomos.cisco.com/xapi/Command.Bookings.List/)) and display if any bookings existing in the device, in a JSON format in the bookings area below:
        ![/IMAGES/list_of_bookings.png](/IMAGES/list_of_bookings.png)
        
        - **Insert a new booking**:  
        Which will open a new tab for the user to be able to add a new booking:
        ![/IMAGES/insert_booking.png](/IMAGES/insert_booking.png)
            - Note: When a new booking is inserted, a local XML file will be generated/updated. First checking any existing bookings and adding them to the XML file, then add the details of the new booking and then send the whole XML file to the device, using the API call:  
            ```'http://(ip_address)/bookingsputxml'```    
  
        - **Clear All Bookings**:
        Which will clear all the bookings in the device, and check with the user if to delete the generated XML file or keep it.

## Notes

- The xAPI calls genereated from the python flask application are following the websocket methodolegy explained here: [xAPI over WebSocket](https://community.cisco.com/t5/collaboration-voice-and-video/xapi-over-websocket-xows-ce9-7-x/ba-p/3831553) 
- Currently, new bookings will be sent using the API call:  
            ```'http://(ip_address)/bookingsputxml'```
    - For future enhancment, the method can be upgraded to use: ([Bookings Book](https://roomos.cisco.com/xapi/Command.Bookings.Book/)). However when we tested this call on devices that are register on-prem, the API wasn't able send bookings, responding with the error: ""Device not entitled" matching what's discussed here: [Cisco Community](https://community.cisco.com/t5/audio-and-video-endpoints/quot-bookings-put-quot-xapi-command-in-a-macro/td-p/4148369)


### LICENSE

Provided under Cisco Sample Code License, for details see [LICENSE](LICENSE.md)

### CODE_OF_CONDUCT

Our code of conduct is available [here](CODE_OF_CONDUCT.md)

### CONTRIBUTING

See our contributing guidelines [here](CONTRIBUTING.md)

#### DISCLAIMER:
<b>Please note:</b> This script is meant for demo purposes only. All tools/ scripts in this repo are released for use "AS IS" without any warranties of any kind, including, but not limited to their installation, use, or performance. Any use of these scripts and tools is at your own risk. There is no guarantee that they have been through thorough testing in a comparable environment and we are not responsible for any damage or data loss incurred with their use.
You are responsible for reviewing and testing any scripts you run thoroughly before use in any non-testing environment.
